import ast
import json
import math
import os

from numpy.ma.extras import average
from scipy.stats import norm, truncnorm
import cv2
import numpy as np
from scipy.optimize import root, root_scalar

import reader
from config.default_config import main_gradeNames, main_view, main_data_path, global_mm_per_pixel, local_mm_per_pixel

"""
所有常用方法
"""
gradeNames = main_gradeNames
data_path = main_data_path
view = main_view

# 文本数据转换为字典，专用于转换从图片中提取到txt的数据
def parse_txt_to_dict(file_path):
    """
    将文本数据转换为数组数据，对文本数据有要求
    单级配需要short_list, long_list和area_list三个属性
    样品砂需要g_short_list, g_long_list, g_area_list以及l_short_list, l_long_list, l_area_list
    :param file_path: txt路径
    :return:
    """
    data_dict = {}
    current_key = None
    current_list = []

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue  # 跳过空行
            if ':' in line:
                if current_key and current_list:
                    # 将之前的列表存入字典
                    data_dict[current_key] = current_list
                # 处理新的键
                current_key, list_str = line.split(':', 1)
                current_key = current_key.strip()
                list_str = list_str.strip()
                if list_str.startswith('[') and list_str.endswith(']'):
                    try:
                        current_list = ast.literal_eval(list_str)
                    except (SyntaxError, ValueError):
                        current_list = []
                else:
                    current_list = []
            else:
                # 处理多行列表的情况
                if line.startswith('[') and line.endswith(']'):
                    try:
                        current_list.append(ast.literal_eval(line))
                    except (SyntaxError, ValueError):
                        continue

    # 存入最后一个键值对
    if current_key and current_list:
        data_dict[current_key] = current_list

    return data_dict


# 计算夹角
def calculate_angle(start, far, end):
    """计算夹角"""
    v1 = np.array(start) - np.array(far)
    v2 = np.array(end) - np.array(far)
    dot_product = np.dot(v1, v2)
    norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
    angle = np.arccos(dot_product / norm_product)
    return np.degrees(angle)

# 返回长轴和短轴值
def eqEllipticFeretCAD(cnt, get_angle=False):
    # 拟合等效椭圆
    ellipse = cv2.fitEllipse(cnt)
    # 提取椭圆长短轴
    w, h = ellipse[1]
    angle = ellipse[2]
    major_axis = max(w, h)
    minor_axis = min(w, h)

    if get_angle:
        return minor_axis, major_axis, angle

    return minor_axis, major_axis

# 计算面积
def expand_contour(cnt, expansion=0.5):
    # 计算轮廓的中心
    M = cv2.moments(cnt)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
    else:
        cx, cy = 0, 0
    # 沿45度方向外扩半个像素点
    expanded_cnt = []
    for pt in cnt:
        x, y = pt[0]
        dx, dy = x - cx, y - cy
        new_x = int(x + expansion * np.sign(dx))
        new_y = int(y + expansion * np.sign(dy))
        expanded_cnt.append([[new_x, new_y]])
    return np.array(expanded_cnt, dtype=np.int32)

# 45度外扩半个像素点法计算面积
def expand_area(cnt):
    expanded_cnt = expand_contour(cnt)
    # 计算外扩后的轮廓面积
    area = cv2.contourArea(expanded_cnt)
    return area

# 极坐标计算
def jizuobiao(contour):

    # 计算轮廓的矩
    M = cv2.moments(contour)

    # 计算中心点坐标
    if M['m00'] != 0:
        center_x = int(M['m10'] / M['m00'])
        center_y = int(M['m01'] / M['m00'])

        center = (center_x, center_y)
        # 计算每个轮廓点到中心点的距离
        distances = np.sqrt((contour[:, 0, 0] - center_x) ** 2 + (contour[:, 0, 1] - center_y) ** 2)
        # 最长距离对应的边缘点坐标
        max_distance_index = np.argmax(distances)
        # max_distance_point = tuple(contour[max_distance_index][0])
        # max_distance_distance = distances[max_distance_index]
        #这里每隔三十度提取一个点，计算距离
        num_points = 12  # 360 度分为 12 份
        angles = np.arange(0, 2 * np.pi, 2 * np.pi / num_points)
        # 将最长轴边缘点作为起点
        start_index = max_distance_index

        # 每隔 30 度找到一个边缘点
        indices = [start_index]
        for i in range(1, num_points):
            angle = angles[i]
            end_index = np.argmin(np.abs(np.arctan2(contour[:, 0, 1] - center_y, contour[:, 0, 0] - center_x) - angle))
            indices.append(end_index)
        # 对边缘点按照顺序进行排序
        sorted_indices = sorted(indices)
        # 计算每个点到中心点的距离
        distances = np.sqrt(
            (contour[sorted_indices, 0, 0] - center_x) ** 2 + (contour[sorted_indices, 0, 1] - center_y) ** 2)
        return distances

# 细度模数计算函数
def get_mx(data):

    data = data[::-1]
    # data = [a * 0.01 for a in data]
    # print(data)
    data = [a * 100 for a in data]
    # print(sum(data[:7]))
    mx = ((sum(data[:2]) + sum(data[:3]) + sum(data[:4]) + sum(data[:5]) + sum(data[:6])) - 5 * data[0]) / (100 - data[0])
    # print(mx)
    return mx


# 局部和全局物理像素尺寸转换，返回 全局->局部 的倍数
def area_gap():
    local_a_s = 38 / 5472
    local_a_c = 26 / 3648

    global_a_s = 109 / 3072
    global_a_c = 75 / 2048

    k_s = global_a_s / local_a_s
    k_c = global_a_c / local_a_c

    global_area_ratio = 1 * k_c * k_s

    return global_area_ratio


# 局部和全局采样范围的差距
def physics_gap():
    a = 109 * 75
    b = 38 * 26
    return round(a / b, 4)


# 像素转换为物理尺寸
def xiangsuTm(value,type):
    if type == 1:
        # 局部相机
        return value * 0.0024 * 137 / 50
    else:
        # 全局相机
        return value * 0.0024 * 161.5 / 12


def get_project_path():
    # 获取当前脚本文件的绝对路径
    script_path = os.path.abspath(__file__)
    # 获取当前脚本文件所在的目录
    script_directory = os.path.dirname(script_path)
    # 获取项目根目录（假设项目根目录是脚本所在目录的父目录）
    project_root = os.path.dirname(script_directory)
    return project_root


# 局部和全局等效Feret短径差距倍率，全局->局部
def diameter_gap(angle):
    local_a_s = 38 / 5472
    local_a_c = 26 / 3648

    global_a_s = 109 / 3072
    global_a_c = 75 / 2048

    k_s = global_a_s / local_a_s
    k_c = global_a_c / local_a_c

    global_short_ratio = math.sqrt(k_s ** 2 * math.cos(angle) ** 2 + k_c ** 2 * math.sin(angle) ** 2)

    return global_short_ratio


# 局部和全局等效Feret短径差距倍率，全局->局部
def diameter_gap_average():
    datas = []
    for i in range(180):
        datas.append(diameter_gap(i))

    return average(datas)


def calculate_mean_and_variance_origin(show_figure=True):
    singleLocs ={}
    distributions = []
    datas=[]
    prop = "short_list"
    # prop = "long_list"
    # prop = "area_list"
    # prop = "volume_list"
    for singleLoc in gradeNames:
        print("singleLoc:",singleLoc)
        # data =  reader.parse_txt_to_dict("/Users/chuanyunxu/Documents/DDD/workspace/Work/2025/09 砂级配/张世豪-砂级配实验数据/data_text/single/local/"+singleLoc+".txt")
        data =  reader.load_dict_from_file(data_path+"/single/"+str(singleLoc)+"/"+view+"/"+str(singleLoc)+".txt")
        # data = reader.load_dict_from_file(data_path + "/single/" + view + "/" + str(singleLoc) + ".txt")
        if len(data) == 0:
            distributions.append([0, 0, 0])
            continue

        if show_figure:
            datas.append([item for sublist in data[prop] for item in sublist])

        sum = 0
        cout = 0
        varianceSum=0
        for i in range(0,len(data[prop])):
            sum += np.sum(data[prop][i])
            cout += len(data[prop][i])
        mean = sum/cout
        for i in range(0,len(data[prop])):
            varianceSum += np.sum((x - mean)**2 for x in data[prop][i])
        variance = varianceSum/cout
        distributions.append([mean, math.sqrt(variance),cout])

    return distributions


def divide_contour(contour, index1, index2):
    """
    在指定的两个点之间分割轮廓，创建两条闭合路径
    
    参数:
        contour: 需要分割的轮廓
        index1: 第一个分割点索引
        index2: 第二个分割点索引
    
    返回:
        两个闭合轮廓组成的列表，如果分割失败则返回原轮廓
    """
    try:
        # 基本验证
        if contour is None or len(contour) < 5:
            return [contour] if contour is not None else []
        
        # 确保索引有效
        contour_length = len(contour)
        if index1 < 0 or index1 >= contour_length or index2 < 0 or index2 >= contour_length:
            return [contour]
        
        # 确保两个索引不同
        if index1 == index2:
            return [contour]
            
        # 确保轮廓是标准格式 (n,1,2)
        if len(contour.shape) != 3 or contour.shape[1] != 1 or contour.shape[2] != 2:
            try:
                contour = contour.reshape(-1, 1, 2)
            except:
                return [contour]  # 无法重整则返回原轮廓
        
        # 创建两条路径
        path1 = []
        path2 = []
        
        # 确保index1 < index2
        if index1 > index2:
            index1, index2 = index2, index1
            
        # 创建第一条路径（从index1到index2）
        for i in range(index1, index2 + 1):
            path1.append(contour[i])
            
        # 创建第二条路径（从index2到末尾，再从开始到index1）
        for i in range(index2, contour_length):
            path2.append(contour[i])
        for i in range(0, index1 + 1):
            path2.append(contour[i])
            
        # 验证路径闭合性（确保首尾点相同）
        try:
            import numpy as np
            path1 = np.array(path1)
            path2 = np.array(path2)
            
            # 检查路径是否包含足够的点
            if len(path1) < 3 or len(path2) < 3:
                return [contour]
                
            # 确保路径闭合
            if not np.array_equal(path1[0], path1[-1]):
                path1 = np.vstack([path1, path1[0:1]])
            if not np.array_equal(path2[0], path2[-1]):
                path2 = np.vstack([path2, path2[0:1]])
                
            # 使用OpenCV计算面积验证轮廓有效性
            import cv2
            area1 = cv2.contourArea(path1)
            area2 = cv2.contourArea(path2)
            
            # 确保分割后的轮廓面积不为零或负值
            if area1 <= 0 or area2 <= 0:
                return [contour]
                
            # 确保分割后的轮廓面积总和不大于原始面积的120%
            # （考虑到数值计算可能带来的小误差）
            original_area = cv2.contourArea(contour)
            if area1 + area2 > original_area * 1.2:
                return [contour]
                
            return [path1, path2]
            
        except Exception as e:
            print(f"验证分割轮廓时出错: {str(e)}")
            return [contour]
            
    except Exception as e:
        print(f"轮廓分割出错: {str(e)}")
        return [contour] if contour is not None else []


def convert_global_to_local_adaptive(short, long, area, particle_size):
    """
    使用自适应方法将全局视图的砂粒特征转换为局部视图格式
    
    这个方法结合了理论物理尺寸转换和实验数据校准，能处理不同粒径的砂粒
    
    参数:
    ----
    short: float - 短径
    long: float - 长径
    area: float - 面积
    particle_size: float - 砂粒所属的粒径类别，比如0.15, 0.3等
    
    返回:
    ----
    tuple(float, float, float) - 转换后的(短径, 长径, 面积)
    """
    # 基础比例转换
    scale_ratio = local_mm_per_pixel / global_mm_per_pixel
    
    # 粒径特定的校准系数 - 根据实验数据确定
    # 这些系数可以根据不同粒径的砂粒校准结果进行调整
    calibration_factors = {
        0.075: {"diameter": 1.12, "area": 0.90},  # 最小粒径可能需要更大的校准
        0.15: {"diameter": 1.08, "area": 0.92},
        0.3: {"diameter": 1.05, "area": 0.94},
        0.6: {"diameter": 1.03, "area": 0.96},
        1.18: {"diameter": 1.01, "area": 0.98},
        2.36: {"diameter": 1.00, "area": 1.00},   # 最大粒径可能几乎不需要校准
    }
    
    # 如果没有找到精确匹配的粒径，使用最接近的一个
    if particle_size not in calibration_factors:
        available_sizes = list(calibration_factors.keys())
        available_sizes.sort()
        
        # 找到最接近的粒径
        closest_size = available_sizes[0]
        for size in available_sizes:
            if abs(size - particle_size) < abs(closest_size - particle_size):
                closest_size = size
        
        particle_size = closest_size
    
    # 获取校准系数
    diameter_calibration = calibration_factors[particle_size]["diameter"]
    area_calibration = calibration_factors[particle_size]["area"]
    
    # 转换
    short_converted = short / scale_ratio * diameter_calibration
    long_converted = long / scale_ratio * diameter_calibration
    area_converted = area / (scale_ratio * scale_ratio) * area_calibration
    
    return short_converted, long_converted, area_converted


def convert_features(short, long, area, view_from="global", view_to="local", method="advanced", particle_size=None):
    """
    高级砂粒特征转换函数，支持多种转换方法
    
    参数:
    ----
    short: float - 短径
    long: float - 长径
    area: float - 面积
    view_from: str - 源视图类型，"global"或"local"
    view_to: str - 目标视图类型，"global"或"local"
    method: str - 转换方法:
        "physical" - 基于物理尺寸比例的转换
        "calibrated" - 使用校准系数的转换
        "adaptive" - 基于粒径的自适应转换
        "advanced" - 结合多种方法的综合转换(默认)
    particle_size: float - 砂粒所属的粒径类别，当method为"adaptive"或"advanced"时使用
    
    返回:
    ----
    tuple(float, float, float) - 转换后的(短径, 长径, 面积)
    """
    # 如果源视图和目标视图相同，则不需要转换
    if view_from == view_to:
        return short, long, area
    
    # 如果是从局部转到全局，逻辑相反
    if view_from == "local" and view_to == "global":
        # 递归调用，然后翻转转换方向
        conv_short, conv_long, conv_area = convert_features(
            short, long, area, 
            view_from="global", view_to="local", 
            method=method, particle_size=particle_size
        )
        # 局部到全局是全局到局部的反向操作
        if method == "physical":
            scale_ratio = local_mm_per_pixel / global_mm_per_pixel
            return short * scale_ratio, long * scale_ratio, area * scale_ratio ** 2
        elif method in ["calibrated", "adaptive", "advanced"]:
            # 使用校准系数的反向转换
            estimated_size = estimate_particle_size_from_local(short) if particle_size is None else particle_size
            scale_ratio = local_mm_per_pixel / global_mm_per_pixel
            
            # 获取校准系数
            calib_factors = get_calibration_factors(estimated_size)
            
            # 反向应用校准系数
            r_short = short * scale_ratio / calib_factors["diameter"]
            r_long = long * scale_ratio / calib_factors["diameter"]
            r_area = area * (scale_ratio ** 2) / calib_factors["area"]
            
            return r_short, r_long, r_area
    
    # 默认是全局到局部的转换    
    # 方法1: 物理尺寸直接转换
    if method == "physical":
        scale_ratio = local_mm_per_pixel / global_mm_per_pixel
        conv_short = short / scale_ratio
        conv_long = long / scale_ratio
        conv_area = area / (scale_ratio * scale_ratio)
        return conv_short, conv_long, conv_area
    
    # 方法2: 使用校准系数的转换
    elif method == "calibrated":
        scale_ratio = local_mm_per_pixel / global_mm_per_pixel
        # 使用固定的校准系数
        diameter_calibration = 1.05  # 直径校准系数
        area_calibration = 0.95      # 面积校准系数
        
        conv_short = short / scale_ratio * diameter_calibration
        conv_long = long / scale_ratio * diameter_calibration
        conv_area = area / (scale_ratio * scale_ratio) * area_calibration
        return conv_short, conv_long, conv_area
    
    # 方法3: 基于粒径的自适应转换
    elif method == "adaptive":
        estimated_size = estimate_particle_size(short) if particle_size is None else particle_size
        return convert_global_to_local_adaptive(short, long, area, estimated_size)
    
    # 方法4: 高级综合转换（结合多种方法）
    elif method == "advanced":
        # 估计粒径
        estimated_size = estimate_particle_size(short) if particle_size is None else particle_size
        
        # 物理尺寸比例
        scale_ratio = local_mm_per_pixel / global_mm_per_pixel
        
        # 形状分析：长短比例影响转换系数
        shape_ratio = long / short if short > 0 else 1
        shape_factor = min(1.1, max(0.9, 1 + (shape_ratio - 2) * 0.02))
        
        # 获取基本校准系数
        calib_factors = get_calibration_factors(estimated_size)
        
        # 形状校正：形状越不规则，校准需要越大的调整
        diameter_calib = calib_factors["diameter"] * shape_factor
        
        # 综合校准
        conv_short = short / scale_ratio * diameter_calib
        conv_long = long / scale_ratio * diameter_calib
        conv_area = area / (scale_ratio * scale_ratio) * calib_factors["area"]
        
        return conv_short, conv_long, conv_area
    
    # 默认使用物理转换
    else:
        print(f"警告：未知的转换方法 '{method}'，使用物理尺寸转换")
        scale_ratio = local_mm_per_pixel / global_mm_per_pixel
        return short / scale_ratio, long / scale_ratio, area / (scale_ratio * scale_ratio)

def estimate_particle_size(short, view="global"):
    """
    根据短径估计砂粒所属的粒径类别
    
    参数:
    ----
    short: float - 短径
    view: str - 视图类型，"global"或"local"
    
    返回:
    ----
    float - 估计的粒径类别(mm)
    """
    # 全局视图的短径阈值
    if view == "global":
        if short < 5:
            return 0.075
        elif short < 10:
            return 0.15
        elif short < 20:
            return 0.3
        elif short < 40:
            return 0.6
        elif short < 75:
            return 1.18
        else:
            return 2.36
    # 局部视图的短径阈值
    else:
        if short < 25:
            return 0.075
        elif short < 55:
            return 0.15
        elif short < 110:
            return 0.3
        elif short < 220:
            return 0.6
        elif short < 400:
            return 1.18
        else:
            return 2.36

def estimate_particle_size_from_local(short):
    """
    根据局部视图短径估计砂粒所属的粒径类别
    
    参数:
    ----
    short: float - 局部视图的短径
    
    返回:
    ----
    float - 估计的粒径类别(mm)
    """
    return estimate_particle_size(short, view="local")

def get_calibration_factors(particle_size):
    """
    获取特定粒径的校准系数
    
    参数:
    ----
    particle_size: float - 砂粒粒径(mm)
    
    返回:
    ----
    dict - 包含"diameter"和"area"校准系数的字典
    """
    # 粒径特定的校准系数 - 根据实验数据确定
    calibration_factors = {
        0.075: {"diameter": 1.12, "area": 0.90},  # 最小粒径可能需要更大的校准
        0.15: {"diameter": 1.08, "area": 0.92},
        0.3: {"diameter": 1.05, "area": 0.94},
        0.6: {"diameter": 1.03, "area": 0.96},
        1.18: {"diameter": 1.01, "area": 0.98},
        2.36: {"diameter": 1.00, "area": 1.00},   # 最大粒径可能几乎不需要校准
    }
    
    # 如果没有找到精确匹配的粒径，使用最接近的一个
    if particle_size not in calibration_factors:
        available_sizes = list(calibration_factors.keys())
        available_sizes.sort()
        
        # 找到最接近的粒径
        closest_size = available_sizes[0]
        for size in available_sizes:
            if abs(size - particle_size) < abs(closest_size - particle_size):
                closest_size = size
        
        particle_size = closest_size
    
    return calibration_factors[particle_size]

def transform_contour_by_affine(contour, view_from="global", view_to="local"):
    """
    使用仿射变换将轮廓从一个视图转换到另一个视图
    
    参数:
    ----
    contour: np.ndarray - 轮廓点集
    view_from: str - 源视图类型，"global"或"local"
    view_to: str - 目标视图类型，"global"或"local"
    
    返回:
    ----
    transformed_contour: np.ndarray - 变换后的轮廓
    """
    import cv2
    import numpy as np
    
    # 如果源视图和目标视图相同，则不需要转换
    if view_from == view_to or contour is None or len(contour) < 5:
        return contour
    
    # 图像物理范围和分辨率参数
    # 局部相机参数
    A1, B1 = 38, 26      # 局部物理范围（mm）
    W1, H1 = 5472, 3648  # 局部分辨率
    
    # 全局相机参数
    A2, B2 = 109, 75     # 全局物理范围（mm）
    W2, H2 = 3072, 2048  # 全局分辨率
    
    # 计算缩放比例
    scale_x = (A1 * W2) / (A2 * W1)  # 全局到局部的X轴缩放
    scale_y = (B1 * H2) / (B2 * H1)  # 全局到局部的Y轴缩放
    
    # 如果是从局部转到全局，需要反转缩放比例
    if view_from == "local" and view_to == "global":
        scale_x = 1.0 / scale_x
        scale_y = 1.0 / scale_y
    
    # 拟合当前椭圆以获取中心点
    try:
        ellipse = cv2.fitEllipse(contour)
        center = ellipse[0]
    except:
        # 如果无法拟合椭圆，使用轮廓的质心
        M = cv2.moments(contour)
        if M["m00"] != 0:
            center = (M["m10"] / M["m00"], M["m01"] / M["m00"])
        else:
            # 如果无法计算质心，使用轮廓的边界框中心
            x, y, w, h = cv2.boundingRect(contour)
            center = (x + w/2, y + h/2)
    
    # 构建仿射变换矩阵（以椭圆中心为中心缩放）
    M = np.array([
        [scale_x, 0, center[0] * (1 - scale_x)],
        [0, scale_y, center[1] * (1 - scale_y)]
    ], dtype=np.float32)
    
    # 应用变换到轮廓点
    transformed_contour = cv2.transform(contour, M)
    
    return transformed_contour


