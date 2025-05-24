import json
import math
import os
import time
import functools
import datetime  # 添加导入datetime模块用于获取时间戳

import cv2
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

import image_config
import zsh_methods
from zsh_image_handle import pictures_handle
from reader import save_pickle_to_file
from config.default_config import main_gradeNames, main_data_path, main_view, main_volume_corrections, main_LABELS, \
    main_input_image_path, background_path
from background import read_backgrounds_single, read_backgrounds_mixture

"""
级配计算保存结果，保存到txt中
"""

# 全局背景模型缓存
_background_model_cache = {}


# 不再使用这个函数，保留它以防其他地方调用
@functools.lru_cache(maxsize=32)
def get_background_model_key(view, sample):
    """生成背景模型的键，使用缓存提高效率（不再使用）"""
    return f"{view}_s{sample}"


def save_data_txt(file_path, data, name, type=None, save_pickle=True):
    """
    保存计算结果到txt中
    :param file_path: 文件路径，需指明存储的结果路径, 相对路径
    :param data: 字典数据
    :param name: 保存文件名,不需加上扩展名
    :param type如果不是将结果保存到result目录下，可以传入，然后自定义相对路径
    :param save_pickle: 是否同时保存pickle文件
    :return:
    """
    dirs = os.path.join(zsh_methods.get_project_path(), "result")

    if not isinstance(data, dict):
        raise TypeError("data must be a dictionary")

    if type != None:
        dirs = zsh_methods.get_project_path()
    file_path = os.path.join(dirs, file_path)

    # 使用os.path.exists代替os.path.exists更高效，避免额外的赋值
    if not os.path.exists(file_path):  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(file_path)  # makedirs 创建文件时如果路径不存在会创建这个路径

    filename = f"{file_path}/{name}.txt"

    # 以追加模式打开文件，一次写入所有数据以减少IO操作
    with open(filename, 'a', encoding='utf-8') as f:
        for key, value in data.items():  # 使用 items() 方法迭代字典
            f.write(f'{key}: {str(value)}\n')  # 将每个键值对的数据写入文件，并换行

    # 只在需要时保存pickle文件
    if save_pickle:
        save_pickle_to_file(data, filename + ".pickle")

    print(f"{filename} 保存成功")


# 保存结果为json文件
def save_results_to_json(results, file_path):
    """将结果保存为JSON文件，并自动创建目录"""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print(f"Results saved to {file_path}")


# =================== 示例用法 ===================
# if __name__ == "__main__":
#     save_data_txt(r'gradation_result',{},'test')


# 添加新函数，不使用lru_cache，手动实现缓存避免哈希问题
def get_background_model(view, sample, background_models):
    """获取背景模型，使用手动缓存避免字典哈希问题"""
    key = f"{view}_s{sample}"

    # 使用全局缓存
    if key in _background_model_cache:
        return _background_model_cache[key]

    # 如果缓存中没有，则从background_models获取并缓存
    if key in background_models:
        _background_model_cache[key] = background_models[key]
        return _background_model_cache[key]
    else:
        # 添加更详细的错误信息
        available_keys = list(background_models.keys())[:5]
        raise KeyError(f"背景模型键'{key}'不存在。可用键(部分): {available_keys}")


# 优化图片处理函数
def process_single_image(args):
    """处理单张图片并返回结果"""
    try:
        image_path, image_name, sample, view, background_models, is_mixture, threshold = args
        full_image_path = os.path.join(image_path, image_name)

        print(full_image_path)
        # 使用修改后的方式获取背景模型
        # background_model = get_background_model(view, sample, background_models)

        contours, binary = pictures_handle(full_image_path)

        # 预分配列表，避免动态扩展
        short_temp = []
        long_temp = []
        area_temp = []

        # 只为有效轮廓分配内存
        valid_contours = [contour for contour in contours if len(contour) > 5]

        # 批量处理轮廓
        for contour in valid_contours:
            # 如果是全局视图，先对轮廓进行仿射变换转换为局部视图
            if view == "global":
                # 使用仿射变换方法转换轮廓
                transformed_contour = zsh_methods.transform_contour_by_affine(contour, view_from="global", view_to="local")
                
                # 对变换后的轮廓计算几何特征
                short, long = zsh_methods.eqEllipticFeretCAD(transformed_contour)
                area = zsh_methods.expand_area(transformed_contour)
            else:
                # 为局部视图轮廓计算几何特征
                short, long = zsh_methods.eqEllipticFeretCAD(contour)
                area = zsh_methods.expand_area(contour)
                
            if math.isnan(short):
                continue

            if short == float('inf'):
                continue

            if short < 2:
                continue

            # 确保无论是否有阈值筛选，都将三个值一起添加或不添加
            if threshold is not None:
                if short >= threshold[0] and long <= threshold[1]:
                    short_temp.append(short)
                    long_temp.append(long)
                    area_temp.append(area)
            else:
                short_temp.append(short)
                long_temp.append(long)
                area_temp.append(area)

        # 添加长度校验，确保三个列表长度一致
        if len(short_temp) != len(area_temp) or len(long_temp) != len(area_temp):
            print(
                f"警告：图片 {image_name} 的特征列表长度不一致! short:{len(short_temp)}, long:{len(long_temp)}, area:{len(area_temp)}")
            # 确保三个列表长度相同，取最小长度
            min_len = min(len(short_temp), len(long_temp), len(area_temp))
            short_temp = short_temp[:min_len]
            long_temp = long_temp[:min_len]
            area_temp = area_temp[:min_len]

        return short_temp, long_temp, area_temp

    except Exception as e:
        print(f"处理图片 {image_name} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印详细堆栈信息，帮助调试
        return [], [], []


# 批量处理图片函数
def process_image_batch(args_batch):
    """批量处理一组图片，减少进程间通信开销"""
    results = []
    for args in args_batch:
        try:
            result = process_single_image(args)
            results.append(result)
        except Exception as e:
            # 如果单个图片处理失败，添加空结果并继续处理其他图片
            print(f"批处理中处理图片失败: {args[1]} - {str(e)}")
            results.append(([], [], []))
    return results


# 保持原有接口不变，但内部实现优化
def process_image(args):
    """处理单张图片的兼容接口"""
    return process_single_image(args)


def process_data(base_path, output_root, step=1):
    """
    处理指定路径下的数据，图片处理算法在process_image中使用
    :param base_path: 数据路径，可以是以下任意一种：
                    1. 单级配全局图片路径 (包含 /single/xxx/global/)
                    2. 单级配局部图片路径 (包含 /single/xxx/local/)
                    3. 混合级配图片路径 (包含 /mixture/sampleX/global/ 或 /mixture/sampleX/local/)
                    4. 基础路径 (包含 single 和 mixture 文件夹)
    :param output_root: 输出根目录，将保持与输入路径相同的结构
    :param step: 图片提取步长，默认为1（提取所有图片）
    :return:
    """
    # 标准化路径
    base_path = os.path.normpath(base_path)
    output_root = os.path.normpath(output_root)

    single_background_models = read_backgrounds_single(background_path)
    mixture_background_models = read_backgrounds_mixture(background_path)

    # 判断路径类型并处理
    if "single" in base_path:
        if "global" in base_path or "local" in base_path:
            # 处理单个单级配文件夹
            process_single_data(base_path, output_root, step, single_background_models)
        else:
            # 处理完整的single文件夹
            process_single_folder(base_path, output_root, step, single_background_models)
    elif "mixture" in base_path:
        if "global" in base_path or "local" in base_path:
            # 处理单个混合级配文件夹
            process_mixture_data(base_path, output_root, step, mixture_background_models)
        else:
            # 处理完整的mixture文件夹
            process_mixture_folder(base_path, output_root, step, mixture_background_models)
    else:
        # 处理完整的基础路径
        process_full_data(base_path, output_root, step, single_background_models, mixture_background_models)


def get_output_path(input_path, output_root):
    """
    根据输入路径生成对应的输出路径，保持相同的目录结构
    :param input_path: 输入路径
    :param output_root: 输出根目录
    :return: 输出路径
    """
    # 获取输入路径中single或mixture之后的部分
    if "single" in input_path:
        relative_path = input_path[input_path.index("single"):]
        return os.path.join(output_root, relative_path)
    elif "mixture" in input_path:
        # 对于mixture，保持sample文件夹结构
        relative_path = input_path[input_path.index("mixture"):]
        return os.path.join(output_root, relative_path)
    else:
        return output_root


def process_single_data(base_path, output_root, step, background_models):
    """
    处理单级配数据（全局或局部）
    :param base_path: 数据路径
    :param output_root: 输出根目录
    :param step: 图片提取步长
    """
    # 从路径中提取直径和视图类型
    path_parts = base_path.split(os.sep)
    diameter_index = path_parts.index("single") + 1
    diameter = path_parts[diameter_index]
    view = "global" if "global" in base_path else "local"

    # 只跳过0.075直径的全局图片，但创建空的txt文件
    if diameter == "0.075" and view == "global":
        print(f"跳过0.075直径的全局图片处理，创建空的txt文件")
        # 创建空的0.075.txt文件
        output_path = get_output_path(base_path, output_root)
        save_data_txt(output_path, {
            'short_list': [],
            'long_list': [],
            'area_list': [],
        }, diameter, 1)
        return

    # 获取对应的全局/局部图片路径
    base_dir = os.path.dirname(base_path)
    opposite_view = "local" if view == "global" else "global"
    opposite_path = os.path.join(base_dir, opposite_view)

    # 检查对应的视图路径是否存在
    if not os.path.exists(opposite_path):
        print(f"警告：找不到对应的{opposite_view}视图路径：{opposite_path}")
        return

    # 获取两个视图的所有图片（单级配使用png格式）
    current_images = set(f[:-4] for f in os.listdir(base_path)
                         if f.endswith('.png'))
    opposite_images = set(f[:-4] for f in os.listdir(opposite_path)
                          if f.endswith('.png'))

    # 找出两个视图共有的图片
    common_images = sorted(list(current_images.intersection(opposite_images)),
                           key=lambda x: int(x))

    if not common_images:
        print(f"警告：在{diameter}直径下没有找到全局和局部都存在的图片")
        return

    print(f"找到{len(common_images)}对匹配的图片")

    # 根据步长选择要处理的图片
    common_images = common_images[::step]
    print(f"根据步长{step}，将处理{len(common_images)}对图片")

    # 检查图片文件是否存在（直接在列表推导中过滤）
    valid_images = [img for img in common_images
                    if os.path.exists(os.path.join(base_path, f"{img}.png"))]

    if not valid_images:
        print(f"警告：没有找到有效的图片文件")
        return

    diameters = [0.075, 0.15, 0.3, 0.6, 1.18, 2.36]

    diameter_index = 0
    for index, d in enumerate(diameters):
        if float(diameter) == d:
            diameter_index = index
            break

    local_threshold = [[0, 45.45454545454546], [0, 90.90909090909092], [11.363636363636365, 178.78787878787878],
                       [22.72727272727273, 357.57575757575756], [45.45454545454546, 909.0909090909092],
                       [90.90909090909092, 909.0909090909092]]
    global_threshold = [[0, 8.547008547008547], [0, 17.094017094017094], [2.1367521367521367, 33.61823361823362],
                        [4.273504273504273, 67.23646723646723], [8.547008547008547, 170.94017094017093],
                        [17.094017094017094, 170.94017094017093]]

    if view == 'global':
        threshold = global_threshold[diameter_index]
    else:
        threshold = local_threshold[diameter_index]

    # 准备处理参数
    args_list = [(base_path, f"{img}.png", diameter, view, background_models, image_config.single_split, threshold) for
                 img in valid_images]

    # 批量处理参数，减少进程创建和通信开销
    batch_size = min(20, max(1, len(args_list) // (cpu_count() * 2)))
    batched_args = [args_list[i:i + batch_size] for i in range(0, len(args_list), batch_size)]

    results = []

    # 根据可用CPU数量设置进程池大小
    max_workers = min(32, cpu_count() + 4)

    # 使用并行处理和进度跟踪
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有批次任务
        if batch_size > 1:
            futures = [executor.submit(process_image_batch, batch) for batch in batched_args]

            # 处理完成的批次结果
            for future in as_completed(futures):
                batch_results = future.result()
                results.extend(batch_results)
                # 打印进度
                progress = len(results) / len(batched_args) * 100
                print(f"\r处理进度: {progress:.1f}%", end="", flush=True)
        else:
            # 如果批次小于1，则使用原方法
            futures = [executor.submit(process_image, args) for args in args_list]

            # 收集结果
            for future in as_completed(futures):
                results.append(future.result())
                # 打印进度
                progress = len(results) / len(args_list) * 100
                print(f"\r处理进度: {progress:.1f}%", end="", flush=True)

    print("\n处理完成！")

    # 根据批次大小重组结果
    if batch_size > 1 and len(results) > 0 and isinstance(results[0], list):
        # 批量处理结果展平，修正之前的展平逻辑
        # 原始的flat_results.extend(batch_result)会导致结果结构混乱

        # 正确的展平方式：每个batch_result是一个列表，包含多个图片的处理结果
        # 每个图片的处理结果是一个三元组(short_temp, long_temp, area_temp)
        flat_results = []
        for batch_result in results:
            for single_result in batch_result:
                if isinstance(single_result, tuple) and len(single_result) == 3:
                    flat_results.append(single_result)
                else:
                    print(f"警告：发现无效的结果项：{type(single_result)}")

        # 如果展平后的结果数量明显不对，记录日志
        expected_count = sum(len(batch) for batch in results if isinstance(batch, list))
        if len(flat_results) != expected_count:
            print(f"警告：展平后的结果数量({len(flat_results)})与预期({expected_count})不符！")

        results = flat_results

    # 重组结果
    short_list = [res[0] for res in results]
    long_list = [res[1] for res in results]
    area_list = [res[2] for res in results]

    # 生成输出路径
    output_path = get_output_path(base_path, output_root)

    # 流式保存结果，避免内存峰值
    chunk_size = 1000
    total_chunks = (len(short_list) + chunk_size - 1) // chunk_size

    if total_chunks > 1:
        # 分块保存大数据
        for i in range(0, len(short_list), chunk_size):
            end = min(i + chunk_size, len(short_list))
            chunk_data = {
                'short_list': short_list[i:end],
                'long_list': long_list[i:end],
                'area_list': area_list[i:end],
            }
            chunk_name = f"{diameter}_part{i // chunk_size + 1}of{total_chunks}"
            save_data_txt(output_path, chunk_data, chunk_name, 1)

        # 保存元数据
        meta_data = {
            'total_parts': total_chunks,
            'total_images': len(short_list),
            'diameter': diameter,
        }
        save_data_txt(output_path, meta_data, f"{diameter}_meta", 1)
    else:
        # 数据量小，直接保存
        save_data_txt(output_path, {
            'short_list': short_list,
            'long_list': long_list,
            'area_list': area_list,
        }, diameter, 1)


def process_mixture_data(base_path, output_root, step, background_models):
    """
    处理混合级配数据
    :param base_path: 数据路径
    :param output_root: 输出根目录
    :param step: 图片提取步长
    """
    # 从路径中提取视图类型和sample编号
    path_parts = base_path.split(os.sep)
    view = "global" if "global" in base_path else "local"

    # 获取sample编号（文件夹名）
    sample = path_parts[-2]  # 倒数第二个部分是sample文件夹名

    # 为错误处理添加更多详细信息
    try:
        # 调试信息 - 检查背景模型
        sample_id = sample[6:]
        test_key = f"global_s{sample_id}"
        print(f"调试信息 - 检查背景模型键: {test_key}")
        if test_key in background_models:
            print(f"背景模型存在，类型: {type(background_models[test_key])}")
        else:
            print(f"警告: 背景模型不存在: {test_key}")
            available_keys = list(background_models.keys())[:5]  # 只显示前5个键
            print(f"可用的背景模型键(部分): {available_keys}")
    except Exception as e:
        print(f"准备处理参数时出错(sample): {str(e)}")

    # 获取对应的全局/局部图片路径
    base_dir = os.path.dirname(base_path)
    opposite_view = "local" if view == "global" else "global"
    opposite_path = os.path.join(base_dir, opposite_view)

    # 检查对应的视图路径是否存在
    if not os.path.exists(opposite_path):
        print(f"警告：找不到对应的{opposite_view}视图路径：{opposite_path}")
        return

    # 获取两个视图的所有图片（混合级配使用jpg格式）
    current_images = set(f[:-4] for f in os.listdir(base_path)
                         if f.endswith('.jpg'))
    opposite_images = set(f[:-4] for f in os.listdir(opposite_path)
                          if f.endswith('.jpg'))

    # 找出两个视图共有的图片
    common_images = sorted(list(current_images.intersection(opposite_images)),
                           key=lambda x: int(x))

    if not common_images:
        print(f"警告：在sample{sample}下没有找到全局和局部都存在的图片")
        return

    total_images = len(common_images)
    print(f"找到{total_images}对匹配的图片")

    # 根据步长选择要处理的图片
    common_images = common_images[::step]
    print(f"根据步长{step}，将处理{len(common_images)}对图片")

    # 直接过滤有效图片
    valid_images = [img for img in common_images
                    if os.path.exists(os.path.join(base_path, f"{img}.jpg"))]

    if not valid_images:
        print(f"警告：没有找到有效的图片文件")
        return

    # 准备处理参数
    args_list = []
    for img in valid_images:
        try:
            # 确保sample_id是字符串类型
            sample_id_str = str(sample[6:])
            args = (base_path, f"{img}.jpg", sample_id_str, view,
                    background_models, image_config.mixture_split, None)
            args_list.append(args)
        except Exception as e:
            print(f"准备处理参数时出错(图片{img}): {str(e)}")

    # 批量处理参数，减少进程创建和通信开销
    batch_size = min(20, max(1, len(args_list) // (cpu_count() * 2)))
    batched_args = [args_list[i:i + batch_size] for i in range(0, len(args_list), batch_size)]

    results = []

    # 根据可用CPU数量设置进程池大小并使用并行处理
    max_workers = min(32, cpu_count() + 4)

    print(f"开始处理混合级配数据，使用{max_workers}个并行进程...")

    # 并行处理图片，增加进程数并使用进度跟踪
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有批次任务
        if batch_size > 1:
            futures = [executor.submit(process_image_batch, batch) for batch in batched_args]

            # 处理完成的批次结果
            total_batches = len(batched_args)
            completed = 0

            for future in as_completed(futures):
                batch_results = future.result()
                results.extend(batch_results)
                completed += 1
                # 打印进度
                progress = completed / total_batches * 100
                print(f"\r处理进度: {progress:.1f}%", end="", flush=True)
        else:
            # 如果批次小于1，则使用原方法
            futures = [executor.submit(process_image, args) for args in args_list]

            # 收集结果
            total_tasks = len(args_list)
            completed = 0

            for future in as_completed(futures):
                results.append(future.result())
                completed += 1
                # 打印进度
                progress = completed / total_tasks * 100
                print(f"\r处理进度: {progress:.1f}%", end="", flush=True)

    print("\n处理完成！")

    # 根据批次大小重组结果
    if batch_size > 1 and len(results) > 0 and isinstance(results[0], list):
        # 批量处理结果展平，修正之前的展平逻辑
        # 原始的flat_results.extend(batch_result)会导致结果结构混乱

        # 正确的展平方式：每个batch_result是一个列表，包含多个图片的处理结果
        # 每个图片的处理结果是一个三元组(short_temp, long_temp, area_temp)
        flat_results = []
        for batch_result in results:
            for single_result in batch_result:
                if isinstance(single_result, tuple) and len(single_result) == 3:
                    flat_results.append(single_result)
                else:
                    print(f"警告：发现无效的结果项：{type(single_result)}")

        # 如果展平后的结果数量明显不对，记录日志
        expected_count = sum(len(batch) for batch in results if isinstance(batch, list))
        if len(flat_results) != expected_count:
            print(f"警告：展平后的结果数量({len(flat_results)})与预期({expected_count})不符！")

        results = flat_results

    # 重组结果
    short_list = [res[0] for res in results]
    long_list = [res[1] for res in results]
    area_list = [res[2] for res in results]

    # 生成输出路径（使用mixture/sample文件夹）
    output_path = os.path.join(output_root, "mixture", sample)

    # 按每500张图片分割并保存，使用流式处理减少内存占用
    chunk_size = 500
    total_images = len(short_list)

    print(f"保存数据中，总共{total_images}个结果，分{(total_images + chunk_size - 1) // chunk_size}个块...")

    for j in range(0, total_images, chunk_size):
        end = min(j + chunk_size, total_images)
        chunk_data = {
            f'{view[0]}_short_list': short_list[j:end],
            f'{view[0]}_long_list': long_list[j:end],
            f'{view[0]}_area_list': area_list[j:end],
        }
        chunk_index = j // chunk_size + 1
        # 不为每个块保存pickle文件，只为最后一个块保存以节省空间和时间
        save_pickle = (j + chunk_size >= total_images)
        save_data_txt(output_path, chunk_data, f"value{chunk_index}", 1, save_pickle)

        # 显示保存进度
        progress = (j + chunk_size) / total_images * 100
        print(f"\r保存进度: {min(progress, 100):.1f}%", end="", flush=True)

    print("\n保存完成！")


def process_single_folder(base_path, output_root, step, background_models):
    """
    处理完整的single文件夹
    :param base_path: single文件夹路径
    :param output_root: 输出根目录
    :param step: 图片提取步长
    """
    # 获取所有直径文件夹
    diameter_folders = [d for d in os.listdir(base_path)
                        if os.path.isdir(os.path.join(base_path, d))]

    for diameter in diameter_folders:
        # 处理global和local文件夹
        for view in ["global", "local"]:
            view_path = os.path.join(base_path, diameter, view)
            if not os.path.exists(view_path):
                continue
            process_single_data(view_path, output_root, step, background_models)


def process_mixture_folder(base_path, output_root, step, background_models):
    """
    处理完整的mixture文件夹
    :param base_path: mixture文件夹路径
    :param output_root: 输出根目录
    :param step: 图片提取步长
    """
    # 获取所有子文件夹
    sub_folders = [d for d in os.listdir(base_path)
                   if os.path.isdir(os.path.join(base_path, d))]

    for folder in sub_folders:
        # 处理global和local文件夹
        for view in ["global", "local"]:
            view_path = os.path.join(base_path, folder, view)
            if not os.path.exists(view_path):
                continue
            process_mixture_data(view_path, output_root, step, background_models)


def process_full_data(base_path, output_root, step, single_background_models, mixture_background_models):
    """
    处理完整的基础路径（包含single和mixture文件夹）
    :param base_path: 基础数据路径
    :param output_root: 输出根目录
    :param step: 图片提取步长
    """
    # 处理single文件夹下的数据
    single_path = os.path.join(base_path, "single")
    if os.path.exists(single_path):
        process_single_folder(single_path, output_root, step, single_background_models)

    # 处理mixture文件夹下的数据
    mixture_path = os.path.join(base_path, "mixture")
    if os.path.exists(mixture_path):
        process_mixture_folder(mixture_path, output_root, step, mixture_background_models)


# 添加函数：保存配置信息到JSON文件
def save_config_info(base_path, output_root, step=1, max_workers=None):
    """
    保存当前运行的配置信息到JSON文件，便于实验复现和调试
    :param base_path: 图片路径
    :param output_root: 输出路径
    :param step: 提取步长
    :param max_workers: 最大工作进程数
    :return: 配置信息文件的路径
    """
    # 收集当前时间作为唯一标识
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # 收集系统信息
    try:
        import platform
        import psutil
        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total // (1024 ** 2),  # MB
        }
    except ImportError:
        system_info = {
            "os": os.name,
            "cpu_count": cpu_count(),
        }

    # 收集配置信息
    config_info = {
        "timestamp": timestamp,
        "system_info": system_info,
        "processing_params": {
            "base_path": base_path,
            "output_root": output_root,
            "step": step,
            "max_workers": max_workers if max_workers else min(32, cpu_count() + 4),
            "single_split": image_config.single_split,
            "mixture_split": image_config.mixture_split,
        },
        "config_params": {
            "main_gradeNames": main_gradeNames,
            "main_data_path": main_data_path,
            "main_view": main_view,
            "background_path": background_path,
            "main_input_image_path": main_input_image_path,
        }
    }

    # 创建配置信息保存路径
    config_dir = os.path.join(output_root, "config_logs")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    config_file = os.path.join(config_dir, f"config_log_{timestamp}.json")

    # 保存配置信息到JSON文件
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_info, f, indent=4, ensure_ascii=False)

    print(f"配置信息已保存到: {config_file}")
    return config_file


def refine_image_data_main(base_path, output_root, step=1, max_workers=None):
    """
    提取指定路径下图片数据的砂粒特征，并保存到指定目录的txt中
    :param base_path: 图片路径，可以传入单级配和混合砂，也可以只传入一个
    :param output_root: 输出路径，单级配保存时和图片结构一致，混合砂一个sample一个value.txt
    :param step: 提取步长，默认为1，表示遍历所有图片。2为每隔一张提取一次
    :param max_workers: 最大工作进程数，默认为None自动计算
    """
    try:
        # 保存配置信息
        config_file = save_config_info(base_path, output_root, step, max_workers)
        print(f"运行配置已保存，配置文件: {config_file}")

        # 打印内存使用情况的辅助函数
        def print_memory_usage():
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                print(f"内存使用: {memory_info.rss / 1024 / 1024:.1f} MB")
            except ImportError:
                print("未安装psutil模块，无法监控内存使用")

        # 启动时打印内存使用
        print_memory_usage()

        # 记录开始时间
        start_time = time.time()
        print(f"开始处理数据: {base_path}")

        # 处理数据
        process_data(base_path, output_root, step)

        # 结束时打印内存使用和耗时
        elapsed_time = time.time() - start_time
        print(f"数据处理完成，耗时: {elapsed_time:.2f}秒 ({elapsed_time / 60:.2f}分钟)")
        print_memory_usage()

        # 更新配置文件，添加处理结果信息
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        config_data["processing_results"] = {
            "elapsed_time_seconds": elapsed_time,
            "elapsed_time_minutes": elapsed_time / 60,
            "completed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)

    except Exception as e:
        import traceback
        print(f"处理过程中出错: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    # 设置更高的递归限制以处理大量数据
    import sys

    sys.setrecursionlimit(10000)

    # 记录开始时间
    start_time = time.time()

    # 配置参数
    base_path = fr"{main_input_image_path}/single"  # 默认基础路径
    # base_path =  fr"{main_input_image_path}single"  # 只提取单级配
    # base_path = fr"{main_input_image_path}mixture"  # 只提取混合砂
    output_root = main_data_path  # 默认输出根目录
    step = 1  # 默认提取步长，1表示提取所有图片

    # 创建输出目录
    if not os.path.exists(output_root):
        os.makedirs(output_root)
        print(f"创建输出目录: {output_root}")

    print(f"开始处理图片数据...")
    print(f"- 输入路径: {base_path}")
    print(f"- 输出路径: {output_root}")
    print(f"- 提取步长: {step}")

    # 可以处理以下几种路径：
    # 1. 单级配全局图片路径
    # process_data("E:/zsh-data/single/0.15/global", "F:/", step=2)  # 每隔一张提取一次

    # 2. 单级配局部图片路径
    # process_data("E:/zsh-data/single/0.15/local", "F:/", step=5)  # 每隔4张提取一次

    # 3. 混合级配图片路径
    # process_data("E:/zsh-data/mixture/sample1/global", "F:/", step=10)  # 每隔9张提取一次

    # 4. 完整的基础路径
    refine_image_data_main(base_path, output_root, step)

    # 计算总耗时
    total_time = time.time() - start_time
    print(f"全部处理完成，总耗时: {total_time:.2f}秒 ({total_time / 60:.2f}分钟)")