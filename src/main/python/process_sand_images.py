"""
Standalone Sand Particle Image Processor
This script processes sand particle images using the specified background models
and saves the results to a JSON file.
"""

import os
import sys
import json
import cv2
import numpy as np
from datetime import datetime
import traceback
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

# 定义结果保存路径
RESULTS_BASE_PATH = r"C:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\results"
RESULTS_GLOBAL_PATH = os.path.join(RESULTS_BASE_PATH, "global")
RESULTS_LOCAL_PATH = os.path.join(RESULTS_BASE_PATH, "local")

# 定义子文件夹
SUBFOLDERS = ["original", "classified", "segmented"]

# 创建所需目录
os.makedirs(RESULTS_BASE_PATH, exist_ok=True)
os.makedirs(RESULTS_GLOBAL_PATH, exist_ok=True)
os.makedirs(RESULTS_LOCAL_PATH, exist_ok=True)

# 创建子文件夹
for folder in [RESULTS_GLOBAL_PATH, RESULTS_LOCAL_PATH]:
    for subfolder in SUBFOLDERS:
        os.makedirs(os.path.join(folder, subfolder), exist_ok=True)

# Add project root to sys.path to allow for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from config.default_config import (
        background_path as BACKGROUND_PATH,
        main_input_image_path,
        global_mm_per_pixel,
        local_mm_per_pixel
    )
    
    GLOBAL_IMAGES_PATH = os.path.join(main_input_image_path, "global")
    LOCAL_IMAGES_PATH = os.path.join(main_input_image_path, "local")
    
    from zsh_image_handle import pictures_handle 
    from background import read_backgrounds_single, read_backgrounds_mixture

except ImportError as e:
    print(f"Error importing configuration or modules: {e}")
    sys.exit(1)

# 指定背景模型文件名
GLOBAL_BG_FILE = "G1.bmp"
LOCAL_BG_FILE = "L1.bmp"

# 粒径阈值 (mm)
GLOBAL_THRESHOLDS = [0.15, 0.3, 0.6, 1.18, 2.36]
LOCAL_THRESHOLDS = [0.15, 0.3, 0.6, 1.18, 2.36]

# 可视化颜色
COLORS = [
    (0, 0, 255),    # Red 0.075~0.15
    (0, 255, 0),    # Green 0.15~0.3
    (255, 0, 0),    # Blue 0.3~0.6
    (255, 255, 0),  # Cyan 0.6~1.18
    (0, 255, 255),  # Yellow 1.18~2.36
    (255, 0, 255)   # Purple 2.36~4.75
]

def load_background_model(image_type):
    """加载背景模型"""
    try:
        bg_path = os.path.join(BACKGROUND_PATH, 
                              GLOBAL_BG_FILE if image_type == "global" else LOCAL_BG_FILE)
        if not os.path.exists(bg_path):
            print(f"Error: Background model not found at {bg_path}")
            return None
            
        bg_image = cv2.imread(bg_path)
        if bg_image is None:
            print(f"Error: Could not load background image from {bg_path}")
            return None
            
        # 如果是全局背景图，也要放大5倍
        if image_type == "global":
            bg_image = cv2.resize(bg_image, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
            
        print(f"Loaded {image_type} background from {bg_path}")
        return bg_image
    except Exception as e:
        print(f"Error loading background model: {str(e)}")
        return None

def fuse_global_local_images(global_result, local_result):
    """融合全局和局部图像的处理结果"""
    try:
        if not global_result["success"] or not local_result["success"]:
            return None
            
        # 合并颗粒统计数据
        fused_result = {
            "success": True,
            "contours_count": global_result["contours_count"] + local_result["contours_count"],
            "short_list": global_result["short_list"] + local_result["short_list"],
            "long_list": global_result["long_list"] + local_result["long_list"],
            "area_list": global_result["area_list"] + local_result["area_list"],
            "volume_list": global_result["volume_list"] + local_result["volume_list"],
            "grade_statistics": []
        }
        
        # 融合每个等级的统计数据
        for i in range(len(global_result["grade_statistics"])):
            fused_count = (global_result["grade_statistics"][i]["count"] + 
                         local_result["grade_statistics"][i]["count"])
            fused_percentage = fused_count / fused_result["contours_count"] if fused_result["contours_count"] > 0 else 0
            fused_result["grade_statistics"].append({
                "count": fused_count,
                "percentage": fused_percentage
            })
            
        return fused_result
    except Exception as e:
        print(f"融合图像结果时出错: {str(e)}")
        return None

def process_image(image_path, background, image_type, debug=False):
    """处理单个图像"""
    try:
        print(f"Processing image: {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "error": "无法读取图像"}

        mm_per_pixel = global_mm_per_pixel if image_type == "global" else local_mm_per_pixel
        
        # # 如果是全局图像，放大5倍以适配局部图像
        # if image_type == "global":
        #     img = cv2.resize(img, None, fx=5, fy=5, interpolation=cv2.INTER_LINEAR)
        #     mm_per_pixel = mm_per_pixel / 5  # 调整像素比例
        
        # 调整背景大小
        if img.shape != background.shape:
            background_resized = cv2.resize(background, (img.shape[1], img.shape[0]), 
                                         interpolation=cv2.INTER_LINEAR)
        else:
            background_resized = background
            
        # 背景差分并转换为灰度
        diff = cv2.absdiff(img, background_resized)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # 使用OTSU阈值分割
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 高效的形态学处理
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        morphology = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        morphology = cv2.morphologyEx(morphology, cv2.MORPH_CLOSE, kernel)
        
        # 轮廓检测
        contours, _ = cv2.findContours(morphology, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 优化的轮廓过滤
        filtered_contours = []
        min_area = 200
        min_perimeter = 30
        
        grade_statistics = [{"count": 0, "percentage": 0} for _ in range(6)]
        classified_contours = [[] for _ in range(6)]
        short_list, long_list, area_list, volume_list = [], [], [], []
        
        # 使用向量化操作处理轮廓
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
                
            perimeter = cv2.arcLength(cnt, True)
            if perimeter < min_perimeter:
                continue
            
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            if not (0.2 < circularity < 1.0):
                continue
                
            rect = cv2.minAreaRect(cnt)
            (_, _), (width, height), _ = rect
            
            if width < height:
                width, height = height, width
                
            width_mm = width * mm_per_pixel
            height_mm = height * mm_per_pixel
            
            filtered_contours.append(cnt)
            short_list.append(float(height_mm))  # 转换为Python原生float
            long_list.append(float(width_mm))
            area_list.append(float(area))
            volume_list.append(float(area * height_mm))
            
            # 分类
            grade_index = 5
            thresholds = GLOBAL_THRESHOLDS if image_type == "global" else LOCAL_THRESHOLDS
            for i, threshold in enumerate(thresholds):
                if height_mm < threshold:
                    grade_index = i
                    break
            
            grade_statistics[grade_index]["count"] += 1
            classified_contours[grade_index].append(cnt)
            
        # 计算百分比
        total_particles = len(filtered_contours)
        for stat in grade_statistics:
            stat["percentage"] = float(stat["count"] / total_particles) if total_particles > 0 else 0.0
        
        # 创建和保存结果图像
        visualization = img.copy()
        segmented = np.zeros_like(img)  # 添加分割图像
        
        # 在分割图上绘制轮廓
        cv2.drawContours(segmented, filtered_contours, -1, (0, 0, 255), 2)
        
        # 在可视化图上绘制不同颜色的轮廓
        for i, contours_list in enumerate(classified_contours):
            cv2.drawContours(visualization, contours_list, -1, COLORS[i], 2)
            
        base_path = RESULTS_GLOBAL_PATH if image_type == "global" else RESULTS_LOCAL_PATH
        base_filename = os.path.splitext(os.path.basename(image_path))[0]
        
        # 保存图像结果
        paths = {}
        for img_type, img_data in [
            ("original", img),
            ("classified", visualization),
            ("segmented", segmented)  # 添加分割图
        ]:
            save_path = os.path.join(base_path, img_type, f"{base_filename}.png")
            cv2.imwrite(save_path, img_data)
            paths[f"{img_type}_path"] = save_path
            
        # 返回JSON可序列化的结果
        return {
            "success": True,
            "image_path": image_path,
            "contours_count": total_particles,
            "short_list": short_list,
            "long_list": long_list,
            "area_list": area_list,
            "volume_list": volume_list,
            "grade_statistics": grade_statistics,
            **paths,  # 展开paths字典，现在包含了 segmented_path
            "image_type": image_type,
            "mm_per_pixel": float(mm_per_pixel)  # 确保是Python原生float
        }
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "image_path": image_path, "error": str(e)}

def process_images_in_directory(directory_path, image_type, debug=False):
    """处理目录中的所有图像"""
    results = []
    print(f"Processing {image_type} images from {directory_path}")
    
    background = load_background_model(image_type)
    if background is None:
        return results
    
    try:
        image_files = [f for f in os.listdir(directory_path) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        total_files = len(image_files)
        print(f"Found {total_files} images")
        
        for i, image_file in enumerate(image_files, 1):
            print(f"[{i}/{total_files}] Processing: {image_file}")
            image_path = os.path.join(directory_path, image_file)
            result = process_image(image_path, background, image_type, debug=(i==1))
            
            if result["success"]:
                # 只保留需要的数据
                results.append({
                    "image_path": result["image_path"],
                    "original_path": result.get("original_path", ""),
                    "classified_path": result.get("classified_path", ""),
                    "contours_count": result["contours_count"],
                    "grade_statistics": result["grade_statistics"],
                    "success": True
                })
            else:
                results.append({
                    "image_path": image_path,
                    "success": False,
                    "error": result.get("error", "Unknown error")
                })
                
            # 显示进度条
            progress = int(i * 50 / total_files)
            print(f"\rProgress: [{'=' * progress}{' ' * (50-progress)}] {i}/{total_files}", end='')
            
        print("\nProcessing complete!")
                
    except Exception as e:
        print(f"\n读取目录时出错: {e}")
        traceback.print_exc()
    
    return results

def process_image_pair(args):
    """处理一对全局和局部图像"""
    global_path, local_path, global_bg, local_bg = args
    
    # 处理全局图像
    global_result = process_image(global_path, global_bg, "global")
    
    # 处理局部图像
    local_result = process_image(local_path, local_bg, "local")
    
    # 融合结果
    fused_result = None
    if global_result["success"] and local_result["success"]:
        fused_result = fuse_global_local_images(global_result, local_result)
        
    return {
        "global": global_result,
        "local": local_result,
        "fused": fused_result,
        "global_file": os.path.basename(global_path),
        "local_file": os.path.basename(local_path)
    }

def main():
    """主函数"""
    try:
        print("开始处理沙粒图像...")
        
        # 检查背景模型
        for bg_file, bg_type in [(GLOBAL_BG_FILE, "global"), (LOCAL_BG_FILE, "local")]:
            bg_path = os.path.join(BACKGROUND_PATH, bg_file)
            if not os.path.exists(bg_path):
                print(f"错误: {bg_type}背景模型不存在: {bg_path}")
                return
        
        # 获取文件列表
        global_files = sorted([f for f in os.listdir(GLOBAL_IMAGES_PATH) 
                             if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
        local_files = sorted([f for f in os.listdir(LOCAL_IMAGES_PATH) 
                            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
        
        # 初始化结果
        all_results = {
            "global": [],
            "local": [],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summaryStats": {
                "global": {"totalImages": 0, "successfulImages": 0, "totalParticles": 0},
                "local": {"totalImages": 0, "successfulImages": 0, "totalParticles": 0}
            }
        }
        
        # 处理全局图像
        if os.path.exists(GLOBAL_IMAGES_PATH):
            all_results["global"] = process_images_in_directory(GLOBAL_IMAGES_PATH, "global")
        else:
            print(f"警告: 全局图像目录不存在: {GLOBAL_IMAGES_PATH}")
            
        # 处理局部图像
        if os.path.exists(LOCAL_IMAGES_PATH):
            all_results["local"] = process_images_in_directory(LOCAL_IMAGES_PATH, "local")
        else:
            print(f"警告: 局部图像目录不存在: {LOCAL_IMAGES_PATH}")
        
        # 更新统计信息
        for image_type in ["global", "local"]:
            results = all_results[image_type]
            stats = all_results["summaryStats"][image_type]
            stats["totalImages"] = len(results)
            stats["successfulImages"] = sum(1 for r in results if r.get("success", False))
            stats["totalParticles"] = sum(r.get("contours_count", 0) for r in results if r.get("success", False))
        
        # 保存结果
        results_file = os.path.join(RESULTS_BASE_PATH, "processing_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print("\n处理摘要:")
        for image_type in ["global", "local"]:
            stats = all_results["summaryStats"][image_type]
            print(f"{image_type.capitalize()}图像: {stats['successfulImages']}/{stats['totalImages']} 成功处理")
            print(f"{image_type.capitalize()}总颗粒数: {stats['totalParticles']}")
        
        print(f"\n结果保存位置:")
        print(f"- JSON文件: {results_file}")
        print(f"- 全局图像结果: {RESULTS_GLOBAL_PATH}")
        print(f"- 局部图像结果: {RESULTS_LOCAL_PATH}")
        
        return all_results
        
    except Exception as e:
        traceback.print_exc()
        print(f"处理图像时出错: {str(e)}")
        return []

if __name__ == "__main__":
    main()