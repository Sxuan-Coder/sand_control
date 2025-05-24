import os

import cv2
import numpy as np
from scipy.stats import mode

import image_config
from background import save_image
from  config.default_config import global_mm_per_pixel, local_mm_per_pixel
from zsh_methods import eqEllipticFeretCAD


def calculate_angle(start, far, end):
    """计算夹角"""
    v1 = np.array(start) - np.array(far)
    v2 = np.array(end) - np.array(far)
    dot_product = np.dot(v1, v2)
    norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
    angle = np.arccos(dot_product / norm_product)
    return np.degrees(angle)


def calculate_shape_factor(contour):
    """计算形状因子"""
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return 0
    return (4 * np.pi * area) / (perimeter * perimeter)


def enhance_contrast_clahe(gray):
    clahe = cv2.createCLAHE(clipLimit=20, tileGridSize=(16, 16))
    enhanced_gray = clahe.apply(gray)
    return enhanced_gray


def enhance_contrast_histogram_equalization(gray):
    enhanced_gray = cv2.equalizeHist(gray)
    return enhanced_gray


def enhance_contrast_linear_transform(gray, alpha=0.2, beta=0):
    enhanced_gray = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    return enhanced_gray


def show_image(image, window_name='Image', show_window=True):
    if not show_window:
        return
    # 设置窗口大小，使其可调节
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.imshow(window_name, image)
    cv2.waitKey(0)  # 按下任意键关闭窗口
    cv2.destroyAllWindows()  # 关闭所有 OpenCV 窗口


def show_contours(contours, defects=None):
    # 创建空白图像
    filled_image = np.zeros((3648, 5472, 3))
    cv2.drawContours(filled_image, contours, -1, (255, 0, 0), thickness=cv2.LINE_4)
    # cv2.drawContours(filled_image, contours, -1, (0, 255, 0), thickness=cv2.FILLED)

    if defects is not None:
        for i in range(defects.shape[0]):
            s, e, f, d = defects[i, 0]
            start = tuple(contours[0][s][0])
            end = tuple(contours[0][e][0])
            far = tuple(contours[0][f][0])
            cv2.line(filled_image, start, end, [0, 0, 255], 2)
            cv2.circle(filled_image, far, 2, [0, 255, 0], -1)

    # 显示处理后的图像
    show_image(filled_image, show_window=True)


def calculate_mode(gray):
    """计算灰度图像的众数"""
    mode_value, count = mode(gray, axis=None)
    return mode_value, count


# 形状因子判断的进阶
# def is_single_particle(contour, shape_thresh=0.65, solidity_thresh=0.9):
#     hull = cv2.convexHull(contour)
#     area = cv2.contourArea(contour)
#     hull_area = cv2.contourArea(hull)
#     solidity = area / hull_area if hull_area else 0
#
#     sf = calculate_shape_factor(contour)
#
#     # 双条件判断
#     if sf > shape_thresh and solidity > solidity_thresh:
#         return True
#     return False

def is_single_particle(contour, mm_per_pixel):
    # 获取砂粒信息
    center, (width, height), angle = cv2.minAreaRect(contour)
    if width < height:
        height, width = width, height
    particle_size_mm = width * mm_per_pixel

    # 计算实际形状因子
    hull = cv2.convexHull(contour)
    area = cv2.contourArea(contour)
    hull_area = cv2.contourArea(hull)
    solidity = area / hull_area if hull_area else 0
    sf = calculate_shape_factor(contour)

    # 动态计算形状因子阈值 - 提高基础阈值
    # 使用连续函数，随着尺寸增加平滑降低阈值
    shape_thresh = max(0.6, 0.8 - 0.05 * (particle_size_mm / 1.0))
    solidity_thresh = max(0.85, 0.95 - 0.05 * (particle_size_mm / 1.0))

    # 对非常大的砂粒特别处理，但保持较高的基础阈值
    if particle_size_mm > 2.0:
        shape_thresh = max(0.55, shape_thresh - 0.05)
        solidity_thresh = max(0.8, solidity_thresh - 0.05)

    # 双条件判断
    if sf > shape_thresh and solidity > solidity_thresh:
        return True
    return False


def blockwise_thresholding(gray, block_size=8):
    """
    将灰度图像分成 block_size x block_size 的小块，
    计算每一块的众数，并以众数作为阈值进行二值化，
    最后将这些小块拼接成最终的二值化结果。
    """
    height, width = gray.shape
    block_height = height // block_size
    block_width = width // block_size
    binary_image = np.zeros_like(gray)

    for i in range(block_size):
        for j in range(block_size):
            # 计算每个小块的起始和结束坐标
            start_y = i * block_height
            end_y = (i + 1) * block_height
            start_x = j * block_width
            end_x = (j + 1) * block_width

            # 提取小块
            block = gray[start_y:end_y, start_x:end_x]

            # 计算小块的众数
            mode_value, count = mode(block, axis=None)
            # print(f"{i}_{j}小块的众数: {mode_value}, 出现次数: {count}")

            # 以众数作为阈值进行二值化
            _, block_binary = cv2.threshold(block, mode_value + 5, 255, cv2.THRESH_BINARY)

            # 将二值化后的小块放回原图位置
            binary_image[start_y:end_y, start_x:end_x] = block_binary

    return binary_image


def divide_contour(contour, start_index, end_index):
    contours = []
    if start_index > end_index:
        start_index, end_index = end_index, start_index

    contours.append(contour[start_index:end_index + 1])
    contours.append(np.concatenate((contour[end_index:len(contour)], contour[0:start_index]), axis=0))

    return contours


def split_contour(contour, contours_splited, contour_index, angle_threshold, mm_per_pixel, split_overlapping=True,
                  is_debug=False):
    if len(contour) < 5:
        return

    # 计算最小外接矩形
    center, (width, height), angle = cv2.minAreaRect(contour)
    if width < height:
        height, width = width, height
    # 如果长宽过大，这说明不是石头，放弃
    if height == 0 or width / height > 4.0:
        return

        # 如果最长的边小于0.075，则去取
    if width * mm_per_pixel < 0.075:
        return

        # 计算形状因子,形状因子值0~1，越靠近1表示越接近圆形
    shape_factor = calculate_shape_factor(contour)

    # 判断是否为粘连颗粒
    # 如果形状因子大于0.6，那么可以判断这颗砂粒大概率为单颗砂粒
    if is_single_particle(contour, mm_per_pixel):  # 形状因子阈值可以根据实际情况调整
        contours_splited.append(contour)
        contour_index += 1
        return

    #
    # # 进一步使用凸性检测
    # # 粘连颗粒一般是凹的，所以进行凸性检测
    # is_convex = cv2.isContourConvex(contour)
    # if  is_convex:
    #     contours_splited.append(contour)
    #     contour_index+=1
    #     print(len(contours_splited))
    #     print("-----------------")
    #     return

    # 判断凹点数量，如果没有两个，无法分割
    hull = cv2.convexHull(contour, returnPoints=False)
    if len(hull) < 2:
        contours_splited.append(contour)
        contour_index += 1
        return

    try:
        # 轮廓凹陷判断
        defects = cv2.convexityDefects(contour, hull)
    except Exception as e:
        # print(fr"Warning:错误的轮廓，执行cv2.convexityDefects出错，原因为：{str(e)}")
        # print(f"该颗粒数是第{contour_index}颗")
        return

    # 显示轮廓和凹缺陷
    # show_contours([contour],defects)

    # 没有凸性缺陷
    if defects is None:
        contours_splited.append(contour)
        contour_index += 1
        return

    angles = []
    convex_point_indexes = []
    for i in range(defects.shape[0]):
        s, e, f, d = defects[i, 0]
        start = tuple(contour[s][0])
        end = tuple(contour[e][0])
        far = tuple(contour[f][0])

        # 如果凹点的深度小于0.075/2，则放弃该点，凹点的深度指凹区起点到终点的直线与最深点的距离
        # 它以8位定点小数来近似表示，所以如果要换成浮点数，应该除以256，即the floating-point value=fixpt_depth/256.0
        d = d / 256.0 * mm_per_pixel
        if is_debug:
            print(fr"深度{d}")
        if d < 0.075 / 2:
            continue

        # 凹点的起点和终点的距离小于0.075，则放弃该点
        distance = np.linalg.norm(np.array(start) - np.array(end)) * mm_per_pixel
        if is_debug:
            print(fr"宽度 {distance}")
        if distance < 0.075:
            continue
        # 计算角度
        angle = calculate_angle(start, far, end)
        if is_debug:
            print(fr"角度 {angle}")
        # 记录凹点
        if angle < angle_threshold:
            angles.append(angle)
            convex_point_indexes.append(f)

    # 如果有凹点，但不需要分割，则放弃该点，主要用于单级配提取
    if len(convex_point_indexes) > 0 and not split_overlapping:
        return

        # 如果只有一个凹点，则不进行切割
    if len(convex_point_indexes) < 2:
        contours_splited.append(contour)
        contour_index += 1
        return

        # 找到最小角度的位置
    # min_angle_index = np.argmin(angles)

    # distances=[]
    # min_angle_point = contour[convex_point_indexes[min_angle_index]]
    # for i in range(len(convex_point_indexes)):
    #     if i==min_angle_index:
    #         distances.append(10000000000)
    #         continue
    #     point1 = contour[convex_point_indexes[i]]
    #     distance = np.linalg.norm(np.array(min_angle_point) - np.array(point1))
    #     distances.append(distance)
    # # 找到最小距离的位置
    # min_distance_index = np.argmin(distances)

    # 把距离最近的两个凹点作为分割点
    distances = np.zeros((len(convex_point_indexes), len(convex_point_indexes)))
    for i in range(len(convex_point_indexes)):
        for j in range(len(convex_point_indexes)):
            if i == j:
                distances[i, j] = 10000000000
            else:
                point1 = contour[convex_point_indexes[i]]
                point2 = contour[convex_point_indexes[j]]
                distances[i, j] = np.linalg.norm(np.array(point1) - np.array(point2))

    # 找到最小距离的索引
    min_distance_index_flat = np.argmin(distances)
    min_distance_index_2d = np.unravel_index(min_distance_index_flat, distances.shape)

    if is_debug:
        print(f"最小值的坐标: {min_distance_index_2d}")
        print(f"最小值: {distances[min_distance_index_2d]}")

    # 基于最小角度的凹点与其距离最近的凹点做切割
    contours_divided = divide_contour(contour, convex_point_indexes[min_distance_index_2d[0]],
                                      convex_point_indexes[min_distance_index_2d[1]])

    for i in range(len(contours_divided)):
        split_contour(contours_divided[i], contours_splited, contour_index, angle_threshold, split_overlapping)
    return


def pictures_handle(
        input_image_path,
        background_model,
        type=None,
        output_image_path=None,
        split_overlapping=True,
        is_debug=False):
    """
    去除重叠的砂粒颗粒
    :param input_image_path:
    :param output_image_path:
    :param input_image_path: 读取图片路径，需加上文件名和扩展名
    :param type: 图片类型，1为全局，其他为局部
    :param output_image_path: 输出路径，需要加上文件名和扩展名
    :return:
    """
    # 如果输入是文件路径，则加载图像
    if isinstance(input_image_path, str):
        image = cv2.imread(input_image_path)
        if image is None:
            raise ValueError("无法加载图像，请检查路径是否正确！")
    else:
        image = input_image_path  # 如果直接传入图像数据，则直接使用

    # 图像预处理
    if is_debug:
        show_image(image)
        # 计算差异图像
        show_image(background_model)

    # 去除背景
    image = cv2.absdiff(image, background_model)

    if is_debug:
        show_image(image)

    # 将图像转换为灰度图像
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if is_debug:
        save_image(gray, r"C:\Users\ASUS\Desktop\test\huiduhua.jpg")

    # 颜色反转
    # gray = cv2.bitwise_not(gray)
    # show_image(gray)

    # 对灰度图像进行线性对比度增强
    gray = enhance_contrast_linear_transform(gray, alpha=0.4, beta=5)
    if is_debug:
        save_image(image, r"C:\Users\ASUS\Desktop\test\xianxingzq.jpg")

    # 使用块状阈值化方法进行二值化
    binary = blockwise_thresholding(gray, block_size=8)
    if is_debug:
        save_image(image, r"C:\Users\ASUS\Desktop\test\erzhihua.jpg")

    # type =1 全部，= 局部
    if type == 1:
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, image_config.global_ksize)
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=image_config.global_iterations)
    else:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, image_config.local_ksize)
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=image_config.local_iterations)

    if is_debug:
        show_image(image)

    # 提取轮廓
    contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    image_height, image_width = image.shape[:2]
    valid_contours = []
    boundary_contours = []

    # 设置角度，夹角检测是否为粘连颗粒
    if type == 1:
        angle_k = image_config.global_angle_k
    else:
        angle_k = image_config.local_angle_k

    mm_per_pixel = global_mm_per_pixel if type == 1 else local_mm_per_pixel

    contour_index = 0
    for i in range(len(contours)):
        if is_debug:
            print(fr"contour {input_image_path}    {i}")
        contour = contours[i]
        # 去除边界不完整颗粒
        x, y, w, h = cv2.boundingRect(contour)
        if x == 0 or y == 0 or x + w >= image_width or y + h >= image_height:
            boundary_contours.append(contour)
            continue

        split_contour(contour, valid_contours, contour_index, angle_k, mm_per_pixel, split_overlapping, is_debug)

    filled_image = np.zeros_like(image)
    cv2.drawContours(filled_image, valid_contours, -1, (255, 255, 255), thickness=cv2.FILLED)
    # cv2.drawContours(filled_image, boundary_contours, -1, (0, 0, 0), thickness=cv2.FILLED)
    #
    # 保存二值化轮廓图像，能够正常使用的
    if output_image_path is not None:
        # 获取完整路径
        full_path = os.path.join(output_image_path)
        #
        # 创建目录（如果不存在）
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        #
        # 保存图像
        cv2.imwrite(full_path, filled_image)
        print('保存成功：', full_path)

    return valid_contours, binary


# def pictures_handle(input_image_path, background_model, type=None, output_image_path=None):
#     """
#     去除重叠的砂粒颗粒
#     :param input_image_path:
#     :param output_image_path:
#     :param input_image_path: 读取图片路径，需加上文件名和扩展名
#     :param type: 图片类型，1为全局，其他为局部
#     :param output_image_path: 输出路径，需要加上文件名和扩展名
#     :return:
#     """
#     # 如果输入是文件路径，则加载图像
#     if isinstance(input_image_path, str):
#         image = cv2.imread(input_image_path)
#         if image is None:
#             raise ValueError("无法加载图像，请检查路径是否正确！")
#     else:
#         image = input_image_path  # 如果直接传入图像数据，则直接使用
#
#     # 图像预处理
#
#     # show_image(image)
#     # 计算差异图像
#     # show_image(background_model)
#     image = cv2.absdiff(image, background_model)
#     # show_image(image)
#     # 将图像转换为灰度图像
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     # show_image(gray)
#
#     # 颜色反转
#     # gray = cv2.bitwise_not(gray)
#     # show_image(gray)
#
#     gray = enhance_contrast_linear_transform(gray, alpha=0.4, beta=5)
#     # show_image(gray)
#
#     # 使用块状阈值化方法进行二值化
#     binary = blockwise_thresholding(gray, block_size=8)
#     # show_image(binary)
#
#     # type =1 全部，= 局部
#     if type == 1:
#         # 自适应阈值分割
#         # binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2)
#         # _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
#
#         # 形态学操作
#         kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
#         opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
#     else:
#         # _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
#         kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
#         opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
#         # opening = enhanced_processing(image)
#
#     # show_image(binary)
#
#     # 提取轮廓
#     # contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     image_height, image_width = image.shape[:2]
#     valid_contours = []
#     boundary_contours = []
#
#     # 设置角度，夹角检测是否为粘连颗粒
#     angle_k = 110
#
#     if type == 1:
#         angle_k = 130
#
#     mm_per_pixel = global_mm_per_pixel if type == 1 else local_mm_per_pixel
#
#     # Apply watershed algorithm to separate overlapping contours
#     # Create a marker image for the watershed algorithm
#     marker_image = np.zeros_like(gray, dtype=np.int32)
#
#     # Label the background with 1
#     marker_image[binary == 0] = 1
#
#     # Label the foreground with 2
#     marker_image[binary == 255] = 2
#
#     # Apply the watershed algorithm
#     cv2.watershed(image, marker_image)
#
#     # Extract the separated contours
#     separated_contours = []
#     for label in np.unique(marker_image):
#         if label == 0 or label == 1:  # 0 is the background, 1 is the original background
#             continue
#         mask = np.zeros_like(gray)
#         mask[marker_image == label] = 255
#         contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#         separated_contours.extend(contours)
#
#     for contour in separated_contours:
#         # 去除边界不完整颗粒
#         x, y, w, h = cv2.boundingRect(contour)
#         if x == 0 or y == 0 or x + w >= image_width or y + h >= image_height:
#             boundary_contours.append(contour)
#             continue
#
#         center, (width, height), angle = cv2.minAreaRect(contour)
#         # 判断长宽比
#         if width < height:
#             height, width = width, height
#         if height == 0:
#             continue
#         if width / height > 3.0:
#             continue
#
#         # 如果最长的边小于0.075，则去取
#         if width * mm_per_pixel < 0.075:
#             continue
#
#         # 计算形状因子
#         shape_factor = calculate_shape_factor(contour)
#
#         # 判断是否为粘连颗粒
#         is_overlapping = False
#         if shape_factor < 0.6:  # 形状因子阈值可以根据实际情况调整
#             # 进一步使用凸性检测
#             is_convex = cv2.isContourConvex(contour)
#             if not is_convex:
#                 hull = cv2.convexHull(contour, returnPoints=False)
#                 if len(hull) > 0:
#                     defects = cv2.convexityDefects(contour, hull)
#                     if defects is not None:
#                         for i in range(defects.shape[0]):
#                             s, e, f, d = defects[i, 0]
#                             start = tuple(contour[s][0])
#                             end = tuple(contour[e][0])
#                             far = tuple(contour[f][0])
#                             # 计算角度
#                             angle = calculate_angle(start, far, end)
#
#                             if angle < angle_k:  # 角度阈值可以根据实际情况调整
#                                 is_overlapping = True
#                                 break
#                         if is_overlapping:
#                             continue
#
#         # 如果不是粘连颗粒，则保留
#         valid_contours.append(contour)
#
#     # # 创建空白图像
#     # filled_image = np.zeros_like(image)
#     # cv2.drawContours(filled_image, valid_contours, -1, (255, 255, 255), thickness=cv2.FILLED)
#     # cv2.drawContours(filled_image, boundary_contours, -1, (0, 0, 0), thickness=cv2.FILLED)
#
#     # # 保存二值化轮廓图像，能够正常使用的
#     # if output_image_path is not None:
#     #     # 获取完整路径
#     #     full_path = os.path.join(output_image_path)
#
#     #     # 创建目录（如果不存在）
#     #     os.makedirs(os.path.dirname(full_path), exist_ok=True)
#
#     #     # 保存图像
#     #     cv2.imwrite(full_path, filled_image)
#     #     print('保存成功：', full_path)
#
#     # # 二值化处理
#     # _, binary = cv2.threshold(filled_image, 1, 255, cv2.THRESH_BINARY)
#     # binary = cv2.cvtColor(binary, cv2.COLOR_BGR2GRAY)
#     # contours1, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#
#     # 返回处理后图片的特征信息
#     return valid_contours, binary

# def pictures_handle(input_image_path, type=None, output_image_path=None, debug=False):
#     """
#     去除重叠的砂粒颗粒
#     :param input_image_path:
#     :param output_image_path:
#     :param input_image_path: 读取图片路径，需加上文件名和扩展名
#     :param type: 图片类型，1为全局，其他为局部
#     :param output_image_path: 输出路径，需要加上文件名和扩展名
#     :return:
#     """
#     # 如果输入是文件路径，则加载图像
#     if isinstance(input_image_path, str):
#         image = cv2.imread(input_image_path)
#         if image is None:
#             raise ValueError("无法加载图像，请检查路径是否正确！")
#     else:
#         image = input_image_path  # 如果直接传入图像数据，则直接使用
#
#     image = remove_background(image, background_model, threshold = 30)
#
#     # 图像预处理
#
#     # 将图像转换为灰度图像
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     # show_image(gray)
#
#     # 颜色反转
#     # gray = cv2.bitwise_not(gray)
#     # show_image(gray)
#
#     gray = enhance_contrast_linear_transform(gray)
#
#     # 计算灰度图像的众数
#     # mode_value, count = calculate_mode(gray)
#     # print(f"灰度图像的众数: {mode_value}, 出现次数: {count}")
#
#     # show_image(gray)
#     # 使用块状阈值化方法进行二值化
#     binary = blockwise_thresholding(gray, block_size=8)
#     # show_image(binary)
#
#     if type == 1:
#         # 自适应阈值分割
#         # binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2)
#         # _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV )
#
#         # 形态学操作
#         kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
#         opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
#     else:
#         # _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV )
#         kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
#         opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
#         # opening = enhanced_processing(image)
#
#     # show_image(binary)
#
#     # 提取轮廓
#     contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     image_height, image_width = image.shape[:2]
#     valid_contours = []
#     boundary_contours = []
#
#     # 设置角度，夹角检测是否为粘连颗粒
#     angle_k = 110
#
#     if type == 1:
#         angle_k = 130
#
#     for contour in contours:
#         # 去除边界不完整颗粒
#         x, y, w, h = cv2.boundingRect(contour)
#         if x == 0 or y == 0 or x + w >= image_width or y + h >= image_height:
#             boundary_contours.append(contour)
#             continue
#
#         # 计算形状因子
#         shape_factor = calculate_shape_factor(contour)
#
#         # 判断是否为粘连颗粒
#         is_overlapping = False
#         if shape_factor < 0.6:  # 形状因子阈值可以根据实际情况调整
#             # 进一步使用凸性检测
#             is_convex = cv2.isContourConvex(contour)
#             if not is_convex:
#                 hull = cv2.convexHull(contour, returnPoints=False)
#                 if len(hull) > 0:
#                     defects = cv2.convexityDefects(contour, hull)
#                     if defects is not None:
#                         for i in range(defects.shape[0]):
#                             s, e, f, d = defects[i, 0]
#                             start = tuple(contour[s][0])
#                             end = tuple(contour[e][0])
#                             far = tuple(contour[f][0])
#                             # 计算角度
#                             angle = calculate_angle(start, far, end)
#
#                             if angle < angle_k:  # 角度阈值可以根据实际情况调整
#                                 is_overlapping = True
#                                 break
#                         if is_overlapping:
#                             continue
#
#         # 如果不是粘连颗粒，则保留
#         valid_contours.append(contour)
#
#     # 只在调试模式下创建和保存图像，否则直接处理轮廓
#     if debug:
#         # 创建空白图像
#         filled_image = np.zeros_like(image)
#         cv2.drawContours(filled_image, valid_contours, -1, (255, 255, 255), thickness=cv2.FILLED)
#         cv2.drawContours(filled_image, boundary_contours, -1, (0, 0, 0), thickness=cv2.FILLED)
#
#         # 二值化处理
#         _, binary = cv2.threshold(filled_image, 1, 255, cv2.THRESH_BINARY)
#         binary = cv2.cvtColor(binary, cv2.COLOR_BGR2GRAY)
#
#         # 保存二值化轮廓图像
#         if output_image_path is not None:
#             # 获取完整路径
#             full_path = os.path.join(output_image_path)
#
#             # 创建目录（如果不存在）
#             os.makedirs(os.path.dirname(full_path), exist_ok=True)
#
#             # 保存图像
#             cv2.imwrite(full_path, filled_image)
#             print('保存成功：', full_path)
#     else:
#         # 非调试模式，直接创建二值图像，不保存中间结果
#         binary = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
#         cv2.drawContours(binary, valid_contours, -1, 255, thickness=cv2.FILLED)
#         cv2.drawContours(binary, boundary_contours, -1, (0, 0, 0), thickness=cv2.FILLED)
#
#     # 提取轮廓
#     contours1, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#
#     # 返回处理后图片的特征信息
#     return contours1, binary


if __name__ == '__main__':
    background_model = cv2.imread(r"C:\Users\ASUS\Desktop\test\L2.bmp", )
    contours, binary = pictures_handle(r"C:\Users\ASUS\Desktop\test\21_1.jpg",
                                       background_model, 2,
                                       output_image_path=r"C:\Users\ASUS\Desktop\test\8.jpg")