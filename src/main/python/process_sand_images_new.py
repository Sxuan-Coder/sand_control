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
        print(f"Loaded {image_type} background from {bg_path}")
        return bg_image
    except Exception as e:
        print(f"Error loading background model: {str(e)}")
        return None

def process_image(image_path, background, image_type, debug=False):
    """处理单个图像"""
    try:
        print(f"Processing image: {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "error": "无法读取图像"}

        mm_per_pixel = global_mm_per_pixel if image_type == "global" else local_mm_per_pixel
        
        # 调整背景大小
        if img.shape != background.shape:
            background_resized = cv2.resize(background, (img.shape[1], img.shape[0]))
        else:
            background_resized = background
            
        # 背景差分
        diff = cv2.absdiff(img, background_resized)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 形态学处理
        kernel = np.ones((5, 5), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=3)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # 轮廓检测和过滤
        contours, _ = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = [cnt for cnt in contours if (cv2.contourArea(cnt) > 200 and 
                                              cv2.arcLength(cnt, True) > 30)]
        
        # 创建结果图像
        visualization = img.copy()  # 彩色分类图
        segmented = np.zeros_like(img)  # 红色分割图
        
        thresholds = GLOBAL_THRESHOLDS if image_type == "global" else LOCAL_THRESHOLDS
        grade_statistics = [{"count": 0, "percentage": 0} for _ in range(6)]
        classified_contours = [[] for _ in range(6)]
        short_list, long_list, area_list, volume_list = [], [], [], []
        
        # 处理每个轮廓
        for contour in contours:
            rect = cv2.minAreaRect(contour)
            (x, y), (width, height), angle = rect
            
            if width < height:
                width, height = height, width
                
            width_mm = width * mm_per_pixel
            height_mm = height * mm_per_pixel
            
            short_list.append(height_mm)
            long_list.append(width_mm)
            
            area = cv2.contourArea(contour)
            area_list.append(area)
            volume = area * height_mm
            volume_list.append(volume)
            
            # 在分割图上绘制红色轮廓
            cv2.drawContours(segmented, [contour], -1, (0, 0, 255), 2)
            
            # 分类
            grade_index = 5
            for i, threshold in enumerate(thresholds):
                if height_mm < threshold:
                    grade_index = i
                    break
                    
            if debug:
                print(f"Particle size: {height_mm:.4f}mm, grade {grade_index}")
                    
            grade_statistics[grade_index]["count"] += 1
            classified_contours[grade_index].append(contour)
        
        # 计算百分比
        total_particles = len(contours)
        for i in range(6):
            if total_particles > 0:
                grade_statistics[i]["percentage"] = grade_statistics[i]["count"] / total_particles
        
        # 使用不同颜色绘制不同等级的轮廓（分类图）
        for i, contours_list in enumerate(classified_contours):
            cv2.drawContours(visualization, contours_list, -1, COLORS[i], 2)
            
        # 保存各类结果图像
        base_path = RESULTS_GLOBAL_PATH if image_type == "global" else RESULTS_LOCAL_PATH
        base_filename = os.path.splitext(os.path.basename(image_path))[0]
        
        # 复制原图到original文件夹
        original_path = os.path.join(base_path, "original", f"{base_filename}.png")
        cv2.imwrite(original_path, img)
        
        # 保存分类图到classified文件夹
        classified_path = os.path.join(base_path, "classified", f"{base_filename}.png")
        cv2.imwrite(classified_path, visualization)
        
        # 保存分割图到segmented文件夹
        segmented_path = os.path.join(base_path, "segmented", f"{base_filename}.png")
        cv2.imwrite(segmented_path, segmented)
        
        return {
            "success": True,
            "image_path": image_path,
            "contours_count": total_particles,
            "short_list": short_list,
            "long_list": long_list,
            "area_list": area_list,
            "volume_list": volume_list,
            "grade_statistics": grade_statistics,
            "original_path": original_path,
            "classified_path": classified_path,
            "segmented_path": segmented_path,
            "visualization": visualization,
            "image_type": image_type,
            "mm_per_pixel": mm_per_pixel
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
        print(f"Found {len(image_files)} images")
        
        for i, image_file in enumerate(image_files):
            print(f"Processing image {i+1}/{len(image_files)}: {image_file}")
            image_path = os.path.join(directory_path, image_file)
            result = process_image(image_path, background, image_type, debug=(i==0))
            
            if result["success"]:
                results.append({
                    "image_path": image_path,
                    "original_path": result["original_path"],
                    "classified_path": result["classified_path"],
                    "segmented_path": result["segmented_path"],
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
    except Exception as e:
        print(f"读取目录时出错: {e}")
    
    return results

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
        
        # 处理图像
        global_results = []
        local_results = []
        
        if os.path.exists(GLOBAL_IMAGES_PATH):
            global_results = process_images_in_directory(GLOBAL_IMAGES_PATH, "global")
        else:
            print(f"警告: 全局图像目录不存在: {GLOBAL_IMAGES_PATH}")
            
        if os.path.exists(LOCAL_IMAGES_PATH):
            local_results = process_images_in_directory(LOCAL_IMAGES_PATH, "local")
        else:
            print(f"警告: 局部图像目录不存在: {LOCAL_IMAGES_PATH}")
        
        # 计算统计数据
        global_success = sum(1 for r in global_results if r.get("success", False))
        local_success = sum(1 for r in local_results if r.get("success", False))
        global_particles = sum(r.get("contours_count", 0) for r in global_results if r.get("success", False))
        local_particles = sum(r.get("contours_count", 0) for r in local_results if r.get("success", False))
        
        # 保存结果
        all_results = {
            "global": global_results,
            "local": local_results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summaryStats": {
                "global": {
                    "totalImages": len(global_results),
                    "successfulImages": global_success,
                    "totalParticles": global_particles
                },
                "local": {
                    "totalImages": len(local_results),
                    "successfulImages": local_success,
                    "totalParticles": local_particles
                }
            }
        }
        
        results_file = os.path.join(RESULTS_BASE_PATH, "processing_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print("\n处理摘要:")
        print(f"全局图像: {global_success}/{len(global_results)} 成功处理")
        print(f"局部图像: {local_success}/{len(local_results)} 成功处理")
        print(f"总颗粒数: 全局={global_particles}, 局部={local_particles}")
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