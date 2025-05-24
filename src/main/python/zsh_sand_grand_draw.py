# 该文件用于提前测试图片数据是否能够正常使用
import os
from pathlib import Path

import cv2
import numpy as np
from matplotlib.pyplot import contour

import image_config
from background import read_backgrounds_mixture, read_backgrounds_single
from zsh_image_handle import pictures_handle, split_contour
# from zsh_image_handle_copy import pictures_handle
# from zsh_image_handle import pictures_handle, show_image, calculate_shape_factor, split_contour
from zsh_methods import eqEllipticFeretCAD, expand_area
from config.default_config import main_gradeNames, main_data_path, main_view, main_volume_corrections, main_LABELS, \
    main_input_image_path, background_path, global_mm_per_pixel


def process_sand_images(image_path,sample_index, start_index, num_images, output_path, thresholds, is_single=True, is_global=True):
    """
    统一处理砂粒图片的方法，图片处理算法在 todo
    :param image_path: 图片路径，例如 fr"{main_input_image_path}single/0.15/global" 或 fr"{main_input_image_path}mixture/sample4/local"
    :param start_index: 起始图片索引
    :param num_images: 需要处理的图片数量
    :param output_path: 输出路径
    :param thresholds: 阈值列表，用于判断粒径范围
    :param is_single: 是否为单级配图片，True为单级配，False为混合级配
    :param is_global: 是否为全局图片，True为全局，False为局部
    :return:
    """
    index = 4

    # 将路径转换为Path对象以更好地处理路径
    output_path = Path(output_path)
    image_path = Path(image_path)

    view_type = "global" if is_global else "local"

    if is_single == False:
        background_models = read_backgrounds_mixture(background_path)
        background_model = background_models[f"{view_type}_s{sample_index}"]
    else:
        background_models = read_backgrounds_single(background_path)
        background_model = background_models[f"{view_type}_s{sample_index}"]

    # 检查输出路径是否存在
    if not output_path.exists():
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            print(f"创建主输出目录：{output_path}")
        except Exception as e:
            print(f"创建主输出目录失败：{str(e)}")
            return

    # 处理指定数量的图片
    for i in range(start_index, start_index + num_images):
        # 构建输出目录
        if is_single:
            diameter = image_path.parent.name

            current_output_dir = output_path / "single" / diameter / view_type / str(sample_index) / str(start_index)
        else:
            current_output_dir = output_path / "mixture" / str(sample_index) / str(start_index)

        # 确保输出目录存在
        try:
            current_output_dir.mkdir(parents=True, exist_ok=True)
            print(f"创建输出目录：{current_output_dir}")
        except Exception as e:
            print(f"创建输出目录失败：{str(e)}")
            continue

        # 读取原图
        if is_single:
            image_file = image_path / f"{i}.png"
        else:
            image_file = image_path / f"{i}_5.jpg"
        print(f"尝试读取图片：{image_file}")
        original_image = cv2.imread(str(image_file))
        if original_image is None:
            print(f"无法读取图片：{image_file}")
            continue

        # 保存原图
        original_filename = f"{'global' if is_global else 'local'}_{sample_index}_{i}_original.png"
        original_path = current_output_dir / original_filename

        try:
            print(f"原图尺寸：{original_image.shape}")
            print(f"原图类型：{original_image.dtype}")
            if original_image.size == 0:
                print("原图数据为空")
                continue

            success = cv2.imwrite(str(original_path.absolute()), original_image)
            if success:
                print(f'保存原图成功：{original_path}')
            else:
                print(f'保存原图失败：{original_path}')
        except Exception as e:
            print(f'保存原图时出错：{str(e)}')
            continue

        # 处理图片获取轮廓和二值图
        try:
            # todo:图片处理算法
            contours, binary = pictures_handle(
                str(image_file),
                background_model,
                1 if is_global else 2,
                None  # 不保存中间结果
            )
            print(f"成功处理图片：{image_file}")
            # print(f"二值图尺寸：{binary.shape}")
            # print(f"二值图类型：{binary.dtype}")
        except Exception as e:
            print(f"处理图片时出错：{str(e)}")
            raise Exception("处理图片时出错：{str(e)}")


        # 创建分类结果列表
        classified_contours = [[] for _ in range(6)]
        areas = [0] * 6
        volumes = [0] * 6

        # 对轮廓进行分类
        for contour in contours:
            if len(contour) > 5:
                try:
                    short, _ = eqEllipticFeretCAD(contour)
                    area = cv2.contourArea(contour)
                    volume = short * area

                    if short < thresholds[0]:
                        classified_contours[0].append(contour)
                        areas[0] += area
                        volumes[0] += volume
                    elif short < thresholds[1]:
                        classified_contours[1].append(contour)
                        areas[1] += area
                        volumes[1] += volume
                    elif short < thresholds[2]:
                        classified_contours[2].append(contour)
                        areas[2] += area
                        volumes[2] += volume
                    elif short < thresholds[3]:
                        classified_contours[3].append(contour)
                        areas[3] += area
                        volumes[3] += volume
                    elif short < thresholds[4]:
                        classified_contours[4].append(contour)
                        areas[4] += area
                        volumes[4] += volume
                    else:
                        classified_contours[5].append(contour)
                        areas[5] += area
                        volumes[5] += volume
                except Exception as e:
                    print(f"处理轮廓时出错：{str(e)}")
                    continue

        # 定义颜色
        colors = [
            (0, 0, 255),    # 红色 0.075~0.15
            (0, 255, 0),    # 绿色 0.15~0.3
            (255, 0, 0),    # 蓝色 0.3~0.6
            (255, 255, 0),  # 青色 0.6~1.18
            (0, 255, 255),  # 黄色 1.18~2.36
            (255, 0, 255)   # 紫色 2.36~4.75
        ]

        colors = [
            (0, 0, 255),  # 红色 0.075~0.15
            (0, 0, 255),  # 红色 0.075~0.15
            (0, 0, 255),  # 红色 0.075~0.15
            (0, 0, 255),  # 红色 0.075~0.15
            (0, 0, 255),  # 红色 0.075~0.15
            (0, 0, 255),  # 红色 0.075~0.15
        ]

        # 在原图上绘制分类结果
        original_classification = original_image.copy()
        for j, contours_list in enumerate(classified_contours):
            # 使用边框式轮廓，线宽为2
            cv2.drawContours(original_classification, contours_list, -1, colors[j], 2)

        # 在二值图上绘制分类结果
        binary_classification = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        for j, contours_list in enumerate(classified_contours):
            # 使用边框式轮廓，线宽为2
            cv2.drawContours(binary_classification, contours_list, -1, colors[j], 2)

        #输出轮廓序号

        for j in range(len(contours)):
            contour = contours[j]
            # 计算轮廓的质心
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            else:
                cX, cY = 0, 0

            split_contour(contour,[], j,image_config.local_angle_k, global_mm_per_pixel,is_debug=True)
            # 输出序号
            cv2.putText(original_classification, f"{j}", (cX-10, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 123, 255), 1, cv2.LINE_AA)

        # show_image(original_classification, "原图分类结果", True)
        # 保存分类结果图像
        try:
            # 保存原图上的分类结果
            original_classified_path = current_output_dir / f"{'global' if is_global else 'local'}_{sample_index}_{i}_original_classified-{index}.png"
            cv2.imwrite(str(original_classified_path.absolute()), original_classification)
            print(f'保存原图分类结果成功：{original_classified_path}')

            # 保存二值图上的分类结果
            binary_classified_path = current_output_dir / f"{'global' if is_global else 'local'}_{sample_index}_{i}_binary_classified-{index}.png"
            cv2.imwrite(str(binary_classified_path.absolute()), binary_classification)
            print(f'保存二值图分类结果成功：{binary_classified_path}')
        except Exception as e:
            print(f'保存分类结果图像时出错：{str(e)}')

# 示例用法image_process
if __name__ == "__main__":
    # 定义阈值
    local_threshold = [20.31326078477733, 38.8063435040528, 101.50969991129595, 192.3552254025128, 353.7784860367505]
    global_threshold = [2.7791685066646155, 8.57674605621097, 18.533280806946458, 36.035896953941865, 67.4079337405388]

    # # 处理单级配全局图片
    # process_sand_images(
    #     image_path=fr"{main_input_image_path}single/0.6/global",
    #     start_index=45,
    #     sample_index=0.6,
    #     num_images=1,
    #     output_path=r"F:\sand\process_result",
    #     thresholds=global_threshold,
    #     is_single=True,
    #     is_global=True
    # )
    #
    # # 处理单级配局部图片
    # process_sand_images(
    #     image_path=fr"{main_input_image_path}single/0.15/local",
    #     sample_index=0.15,
    #     start_index=50,
    #     num_images=1,
    #     output_path=r"F:\sand\process_result",
    #     thresholds=local_threshold,
    #     is_single=True,
    #     is_global=False
    # )
    #


    # # 处理混合级配局部图片
    sample_index = 0.6
    process_sand_images(
        # image_path=fr"{main_input_image_path}mixture/sample{sample_index}/global",
        image_path=fr"E:\zsh-data\single\0.6\local",
        # image_path=fr"F:\sand\submit\ZSH_Sand_411\zsh_images_421\mixture\sample1\local",
        sample_index=sample_index,
        start_index=90,
        num_images=1,
        output_path=rf"F:\sand\process_result",
        thresholds=global_threshold,
        is_single=True,
        is_global=False
    )

    #
    # sample_index = 6
    # process_sand_images(
    #     image_path=fr"{main_input_image_path}mixture/sample{sample_index}/global",
    #     sample_index=sample_index,
    #     start_index=70,
    #     num_images=1,
    #     output_path=r"F:\sand\process_result",
    #     thresholds=global_threshold,
    #     is_single=False,；k
    #     is_global=True
    # )
    #
    # sample_index = 9
    # process_sand_images(
    #     image_path=fr"{main_input_image_path}mixture/sample{sample_index}/global",
    #     sample_index=sample_index,
    #     start_index=24,
    #     num_images=1,
    #     output_path=r"F:\sand\process_result",
    #     thresholds=global_threshold,
    #     is_single=False,
    #     is_global=True
    # )
    #
    # sample_index = 10
    # process_sand_images(
    #     image_path=fr"{main_input_image_path}mixture/sample{sample_index}/global",
    #     sample_index=sample_index,
    #     start_index=50,
    #     num_images=1,
    #     output_path=r"F:\sand\process_result",
    #     thresholds=global_threshold,
    #     is_single=False,
    #     is_global=True
    # )
