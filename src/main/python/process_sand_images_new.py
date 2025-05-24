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

# Define paths for background models and images
BACKGROUND_PATH = r"C:\Users\ASUS\Desktop\test"
GLOBAL_IMAGES_PATH = r"F:\sand_data\test\global"
LOCAL_IMAGES_PATH = r"F:\sand_data\test\local"
RESULTS_PATH = r"C:\Users\ASUS\Desktop\SandControl\results"

# 指定背景模型文件名
GLOBAL_BG_FILE = "G1.bmp"
LOCAL_BG_FILE = "L1.bmp"

# Create the results directory if it doesn't exist
os.makedirs(RESULTS_PATH, exist_ok=True)

# Define conversion factors (pixels to mm)
GLOBAL_MM_PER_PIXEL = 0.0351  # Global view: 1 pixel = 0.0351mm
LOCAL_MM_PER_PIXEL = 0.0066   # Local view: 1 pixel = 0.0066mm

# 沙粒分类阈值 (单位: mm)
# 调整为更合理的阈值，以便更好地分类沙粒
# 全局视图阈值 (粒径由小到大)
GLOBAL_THRESHOLDS = [0.15, 0.3, 0.6, 1.18, 2.36]
# 局部视图阈值 (粒径由小到大)
LOCAL_THRESHOLDS = [0.15, 0.3, 0.6, 1.18, 2.36]

# 可视化颜色
COLORS = [
    (0, 0, 255),    # Red <0.15mm
    (0, 255, 0),    # Green 0.15-0.3mm
    (255, 0, 0),    # Blue 0.3-0.6mm
    (255, 255, 0),  # Cyan 0.6-1.18mm
    (0, 255, 255),  # Yellow 1.18-2.36mm
    (255, 0, 255)   # Purple >2.36mm
]

def load_background_model(image_type):
    """加载适当的背景模型"""
    try:
        if image_type == "global":
            bg_path = os.path.join(BACKGROUND_PATH, GLOBAL_BG_FILE)
        else:  # local
            bg_path = os.path.join(BACKGROUND_PATH, LOCAL_BG_FILE)
            
        if not os.path.exists(bg_path):
            print(f"Error: Background model file not found at {bg_path}")
            return None
            
        bg_image = cv2.imread(bg_path)
        print(f"Loaded {image_type} background from {bg_path}")
        return bg_image
    except Exception as e:
        print(f"Error loading background model: {str(e)}")
        return None

def process_image(image_path, background, image_type, debug=False):
    """处理单个沙粒图像并检测轮廓"""
    try:
        print(f"Processing image: {image_path}")
        
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not read image {image_path}")
            return {"success": False, "error": "Could not read image"}
            
        # 如果需要，将背景调整为与图像尺寸匹配
        if image.shape != background.shape:
            print(f"Resizing background to match image dimensions: {image.shape}")
            background_resized = cv2.resize(background, (image.shape[1], image.shape[0]))
        else:
            background_resized = background
            
        # 简单的背景减法
        diff = cv2.absdiff(image, background_resized)
        
        # 转换为灰度
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # 应用自适应阈值而不是固定阈值
        # 使用Otsu自动确定最佳阈值
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 增强形态学处理以更好地清理图像
        kernel = np.ones((5, 5), np.uint8)
        # 开运算去除小噪点
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        # 闭运算填充颗粒内部的小孔
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # 在处理后的图像上查找轮廓
        contours, _ = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 提高轮廓过滤标准，去除更多噪点
        min_area = 100 if image_type == "global" else 50  # 根据图像类型调整最小面积阈值
        min_perimeter = 20 if image_type == "global" else 10  # 根据图像类型调整最小周长
        
        # 同时考虑面积和周长进行过滤
        contours = [cnt for cnt in contours if (cv2.contourArea(cnt) > min_area and 
                                              cv2.arcLength(cnt, True) > min_perimeter)]
        
        # 创建可视化图像
        visualization = image.copy()
        
        # 根据图像类型设置转换因子和阈值
        mm_per_pixel = GLOBAL_MM_PER_PIXEL if image_type == "global" else LOCAL_MM_PER_PIXEL
        thresholds = GLOBAL_THRESHOLDS if image_type == "global" else LOCAL_THRESHOLDS
        
        # 初始化结果和分类容器
        grade_statistics = [{"count": 0, "percentage": 0} for _ in range(6)]
        classified_contours = [[] for _ in range(6)]
        short_list = []
        long_list = []
        area_list = []
        volume_list = []
        
        # 处理每个轮廓
        for contour in contours:
            # 获取最小面积矩形
            rect = cv2.minAreaRect(contour)
            (x, y), (width, height), angle = rect
            
            # 确保宽度是较长的尺寸
            if width < height:
                width, height = height, width
                
            # 将像素尺寸转换为毫米
            width_mm = width * mm_per_pixel
            height_mm = height * mm_per_pixel
            
            # 存储尺寸
            short_list.append(height_mm)
            long_list.append(width_mm)
            
            # 计算面积
            area = cv2.contourArea(contour)
            area_list.append(area)
            
            # 简单的体积估计（面积 * 短轴）
            volume = area * height_mm
            volume_list.append(volume)
            
            # 使用短轴长度(height_mm)来分类沙粒
            # 默认为最大粒径等级(>2.36mm)
            grade_index = 5
            
            # 根据短轴长度判断沙粒等级
            # 0: <0.15mm, 1: 0.15-0.3mm, 2: 0.3-0.6mm, 3: 0.6-1.18mm, 4: 1.18-2.36mm, 5: >2.36mm
            for i, threshold in enumerate(thresholds):
                if height_mm < threshold:
                    grade_index = i
                    break
                    
            # 调试信息，帮助验证分类是否正确
            if debug:
                print(f"Particle size: {height_mm:.4f}mm, classified as grade {grade_index}")
                    
            # 更新统计信息
            grade_statistics[grade_index]["count"] += 1
            classified_contours[grade_index].append(contour)
        
        # 计算百分比
        total_particles = len(contours)
        for i in range(6):
            grade_statistics[i]["percentage"] = grade_statistics[i]["count"] / total_particles if total_particles > 0 else 0
        
        # 在可视化图像上绘制轮廓
        for i, contours_list in enumerate(classified_contours):
            cv2.drawContours(visualization, contours_list, -1, COLORS[i], 2)
            
        # 保存可视化
        vis_filename = f"vis_{image_type}_{os.path.basename(image_path).split('.')[0]}.png"
        vis_path = os.path.join(RESULTS_PATH, vis_filename)
        cv2.imwrite(vis_path, visualization)
        
        return {
            "success": True,
            "image_path": image_path,
            "contours_count": total_particles,
            "short_list": short_list,
            "long_list": long_list,
            "area_list": area_list,
            "volume_list": volume_list,
            "grade_statistics": grade_statistics,
            "visualization_path": vis_filename,
            "visualization": visualization,  # 添加实际的可视化图像
            "image_type": image_type,
            "mm_per_pixel": mm_per_pixel
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "image_path": image_path,
            "error": str(e)
        }

def process_images_in_directory(directory_path, image_type, debug=False):
    """处理目录中的所有图像"""
    print(f"Processing {image_type} images from {directory_path}")
    
    # 加载背景模型
    background = load_background_model(image_type)
    if background is None:
        return []
    
    # 获取图像文件
    try:
        image_files = [f for f in os.listdir(directory_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        print(f"Found {len(image_files)} images in {directory_path}")
        
        if not image_files:
            print(f"No image files found in {directory_path}")
            return []
        
        # 处理每个图像
        results = []
        for i, image_file in enumerate(image_files):
            print(f"Processing image {i+1}/{len(image_files)}: {image_file}")
            image_path = os.path.join(directory_path, image_file)
            # 第一个图像开启调试模式，帮助验证分类是否正确
            debug_mode = (i == 0)
            result = process_image(image_path, background, image_type, debug=debug_mode)
            
            if result["success"]:
                # 格式化结果以匹配前端预期格式
                formatted_result = {
                    "image_path": image_path,
                    "visualization_path": result["visualization_path"],
                    "contours_count": result["contours_count"],
                    "grade_statistics": result["grade_statistics"],
                    "success": True
                }
                
                results.append(formatted_result)
            else:
                # 处理失败，添加错误信息
                results.append({
                    "image_path": image_path,
                    "success": False,
                    "error": result.get("error", "Unknown error")
                })
        
        return results
    except Exception as e:
        print(f"Error processing directory {directory_path}: {str(e)}")
        return []

def main():
    """主函数，处理沙粒图像"""
    print("开始处理沙粒图像...")
    
    # 显示使用的背景模型
    global_bg_path = os.path.join(BACKGROUND_PATH, GLOBAL_BG_FILE)
    local_bg_path = os.path.join(BACKGROUND_PATH, LOCAL_BG_FILE)
    print(f"使用全局背景模型: {global_bg_path}")
    print(f"使用局部背景模型: {local_bg_path}")
    print()
    
    # 处理全局视图图像
    global_results = []
    if os.path.exists(GLOBAL_IMAGES_PATH):
        print(f"处理全局视图图像: {GLOBAL_IMAGES_PATH}")
        global_results = process_images_in_directory(GLOBAL_IMAGES_PATH, "global")
    else:
        print(f"全局视图图像目录不存在: {GLOBAL_IMAGES_PATH}")
    
    # 处理局部视图图像
    local_results = []
    if os.path.exists(LOCAL_IMAGES_PATH):
        print(f"\n处理局部视图图像: {LOCAL_IMAGES_PATH}")
        local_results = process_images_in_directory(LOCAL_IMAGES_PATH, "local")
    else:
        print(f"局部视图图像目录不存在: {LOCAL_IMAGES_PATH}")
    
    # 汇总统计信息
    global_success_count = sum(1 for r in global_results if r["success"])
    local_success_count = sum(1 for r in local_results if r["success"])
    
    global_particles_count = sum(r["contours_count"] for r in global_results if r["success"])
    local_particles_count = sum(r["contours_count"] for r in local_results if r["success"])
    
    print("\n处理摘要:")
    print(f"全局图像: {global_success_count}/{len(global_results)} 成功处理")
    print(f"局部图像: {local_success_count}/{len(local_results)} 成功处理")
    print(f"总颗粒数: 全局={global_particles_count}, 局部={local_particles_count}")
    
    # 创建结果JSON
    results = {
        "global_results": global_results,
        "local_results": local_results,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summaryStats": {
            "global": {
                "totalImages": len(global_results),
                "successfulImages": global_success_count,
                "totalParticles": global_particles_count
            },
            "local": {
                "totalImages": len(local_results),
                "successfulImages": local_success_count,
                "totalParticles": local_particles_count
            }
        }
    }
    
    # 保存结果到JSON文件
    results_file = os.path.join(RESULTS_PATH, "processing_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"结果已保存到 {results_file}")
    
    return results

if __name__ == "__main__":
    main()
