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

# Add project root to sys.path to allow for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..')) # Adjust if script moves
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from config.default_config import (
        background_path as BACKGROUND_PATH,
        main_input_image_path, # Assuming this contains separate global/local paths or needs adjustment
        global_mm_per_pixel,
        local_mm_per_pixel,
        RESULTS_PATH
    )
    # Adjust GLOBAL_IMAGES_PATH and LOCAL_IMAGES_PATH based on main_input_image_path
    # This might require main_input_image_path to be a dict or have a specific structure
    # For now, we'll assume main_input_image_path is the base, and we append 'global' or 'local'
    # This part needs to align with how main_input_image_path is structured in default_config.py
    GLOBAL_IMAGES_PATH = os.path.join(main_input_image_path, "global")
    LOCAL_IMAGES_PATH = os.path.join(main_input_image_path, "local")
    
    # RESULTS_PATH should also ideally come from config or be a subdirectory of the project
    # For now, keeping it as defined if not in config, or define a new config var for it.
    # Example: from config.default_config import results_path as RESULTS_PATH
    # If not in config, define it relative to the project or as an absolute path.
    # RESULTS_PATH = os.path.join(project_root, "results") # Example: making it relative
    os.makedirs(RESULTS_PATH, exist_ok=True) # Ensure results directory exists

    # Import other necessary modules AFTER path setup
    from zsh_image_handle import pictures_handle 
    from background import read_backgrounds_single, read_backgrounds_mixture

except ImportError as e:
    print(f"Error importing configuration or modules: {e}")
    print("Please ensure 'config.default_config.py' is correctly set up and accessible.")
    print("And other dependencies like 'zsh_image_handle' and 'background' are in the Python path.")
    sys.exit(1)

# 指定背景模型文件名
GLOBAL_BG_FILE = "G1.bmp"
LOCAL_BG_FILE = "L1.bmp"

# Define conversion factors (pixels to mm)
# GLOBAL_MM_PER_PIXEL = 0.0351  # Global view: 1 pixel = 0.0351mm
# LOCAL_MM_PER_PIXEL = 0.0066   # Local view: 1 pixel = 0.0066mm

# Thresholds for particle classification (单位: mm)
# 调整为更合理的阈值，以便更好地分类沙粒
# 全局视图阈值 (粒径由小到大)
GLOBAL_THRESHOLDS = [0.15, 0.3, 0.6, 1.18, 2.36]
# 局部视图阈值 (粒径由小到大)
LOCAL_THRESHOLDS = [0.15, 0.3, 0.6, 1.18, 2.36]

# Visualization colors
COLORS = [
    (0, 0, 255),    # Red 0.075~0.15
    (0, 255, 0),    # Green 0.15~0.3
    (255, 0, 0),    # Blue 0.3~0.6
    (255, 255, 0),  # Cyan 0.6~1.18
    (0, 255, 255),  # Yellow 1.18~2.36
    (255, 0, 255)   # Purple 2.36~4.75
]

def load_background_model(image_type):
    """Load the appropriate background model based on image type"""
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
    """处理单个图像"""
    try:
        print(f"Processing image: {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "error": "无法读取图像"}

        # 根据图像类型选择对应的mm_per_pixel值
        mm_per_pixel = global_mm_per_pixel if image_type == "global" else local_mm_per_pixel

        # Resize background to match image dimensions if needed
        if img.shape != background.shape:
            print(f"Resizing background to match image dimensions: {img.shape}")
            background_resized = cv2.resize(background, (img.shape[1], img.shape[0]))
        else:
            background_resized = background
            
        # Simple background subtraction
        diff = cv2.absdiff(img, background_resized)
        
        # Convert to grayscale
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # 使用Otsu自动确定最佳阈值
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 增强形态学处理以更好地清理图像
        kernel = np.ones((5, 5), np.uint8)
        # 开运算去除小噪点
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=3)
        # 闭运算填充颗粒内部的小孔
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Find contours on the processed image
        contours, _ = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 提高轮廓过滤标准，去除更多噪点
        min_area = 200  # 增加最小面积阈值
        min_perimeter = 30  # 最小周长
        # 同时考虑面积和周长进行过滤
        contours = [cnt for cnt in contours if (cv2.contourArea(cnt) > min_area and 
                                              cv2.arcLength(cnt, True) > min_perimeter)]
        
        # Create visualization image
        visualization = img.copy()
        
        # Set conversion factor and thresholds based on image type
        thresholds = GLOBAL_THRESHOLDS if image_type == "global" else LOCAL_THRESHOLDS
        
        # Initialize results and classification containers
        grade_statistics = [{"count": 0, "percentage": 0} for _ in range(6)]
        classified_contours = [[] for _ in range(6)]
        short_list = []
        long_list = []
        area_list = []
        volume_list = []
        
        # Process each contour
        for contour in contours:
            # Get the minimum area rectangle
            rect = cv2.minAreaRect(contour)
            (x, y), (width, height), angle = rect
            
            # Ensure width is the longer dimension
            if width < height:
                width, height = height, width
                
            # Convert pixel dimensions to mm
            width_mm = width * mm_per_pixel
            height_mm = height * mm_per_pixel
            
            # Store dimensions
            short_list.append(height_mm)
            long_list.append(width_mm)
            
            # Calculate area
            area = cv2.contourArea(contour)
            area_list.append(area)
            
            # Simple volume estimation (area * short axis)
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
                    
            # Update statistics
            grade_statistics[grade_index]["count"] += 1
            classified_contours[grade_index].append(contour)
        
        # Calculate percentages
        total_particles = len(contours)
        for i in range(6):
            grade_statistics[i]["percentage"] = grade_statistics[i]["count"] / total_particles if total_particles > 0 else 0
        
        # Draw contours on visualization image
        for i, contours_list in enumerate(classified_contours):
            cv2.drawContours(visualization, contours_list, -1, COLORS[i], 2)
          # Save visualization
        vis_filename = f"vis_{os.path.basename(image_path)}"
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
            "visualization_path": vis_path,
            "visualization": visualization,  # Add the actual visualization image
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
    results = [] # Initialize results as an empty list
    """Process all images in a directory"""
    print(f"Processing {image_type} images from {directory_path}")
    
    # Load background model
    background = load_background_model(image_type)
    if background is None:
        print(f"Failed to load background for {image_type}, returning empty results.")
        return results # Return the initialized empty list
    
    # Get image files
    try:
        image_files = [f for f in os.listdir(directory_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        print(f"Found {len(image_files)} images in {directory_path}")
    except Exception as e:
        print(f"读取目录时出错: {e}")
        return results # Return the initialized empty list
        
    if not image_files: # Corrected indentation for this block
        print(f"No image files found in {directory_path}")
        return results # Return the initialized empty list
        
    # Process each image
    # Removed re-initialization of results: results = []
    for i, image_file in enumerate(image_files):
        print(f"Processing image {i+1}/{len(image_files)}: {image_file}")
        image_path = os.path.join(directory_path, image_file)
        # 第一个图像开启调试模式，帮助验证分类是否正确
        debug_mode = (i == 0)
        result = process_image(image_path, background, image_type, debug=debug_mode)
            
        if result["success"]:
            # Generate visualization image path
            vis_filename = f"vis_{image_type}_{os.path.splitext(image_file)[0]}.png"
            vis_path = os.path.join(RESULTS_PATH, vis_filename)
                
            # Save visualization image if not already saved and if visualization data exists
            if not os.path.exists(vis_path) and result.get("visualization") is not None:
                cv2.imwrite(vis_path, result["visualization"])
            # print(f"Visualization saved to: {vis_filename}") # Optional: can be noisy
                
            # Format results to match frontend expected format
            formatted_result = {
                "image_path": image_path,
                "visualization_path": vis_filename, # Use the generated vis_filename
                "contours_count": result["contours_count"],
                "grade_statistics": result["grade_statistics"],
                "success": True
            }
            results.append(formatted_result)
        else:
            # Handle processing failure for an image
            results.append({
                "image_path": image_path,
                "success": False,
                "error": result.get("error", "Unknown error during image processing")
            })
    return results

def main():
    """Main function to process sand particle images"""
    try:
        print("开始处理沙粒图像...")
        print(f"使用全局背景模型: {os.path.join(BACKGROUND_PATH, GLOBAL_BG_FILE)}")
        print(f"使用局部背景模型: {os.path.join(BACKGROUND_PATH, LOCAL_BG_FILE)}")
        
        # 检查背景模型文件是否存在
        global_bg_path = os.path.join(BACKGROUND_PATH, GLOBAL_BG_FILE)
        local_bg_path = os.path.join(BACKGROUND_PATH, LOCAL_BG_FILE)
        
        if not os.path.exists(global_bg_path):
            print(f"错误: 全局背景模型文件不存在: {global_bg_path}")
            return
            
        if not os.path.exists(local_bg_path):
            print(f"错误: 局部背景模型文件不存在: {local_bg_path}")
            return
        
        # 处理全局视图图像
        if os.path.exists(GLOBAL_IMAGES_PATH):
            print(f"\n处理全局视图图像: {GLOBAL_IMAGES_PATH}")
            global_results = process_images_in_directory(GLOBAL_IMAGES_PATH, "global")
        else:
            print(f"警告: 全局图像目录不存在: {GLOBAL_IMAGES_PATH}")
            global_results = []
            
        # 处理局部视图图像
        if os.path.exists(LOCAL_IMAGES_PATH):
            print(f"\n处理局部视图图像: {LOCAL_IMAGES_PATH}")
            local_results = process_images_in_directory(LOCAL_IMAGES_PATH, "local")
        else:
            print(f"警告: 局部图像目录不存在: {LOCAL_IMAGES_PATH}")
            local_results = []
        
        # 计算统计数据
        global_success = sum(1 for r in global_results if r.get("success", False))
        local_success = sum(1 for r in local_results if r.get("success", False))
        
        global_particles = sum(r.get("contours_count", 0) for r in global_results if r.get("success", False))
        local_particles = sum(r.get("contours_count", 0) for r in local_results if r.get("success", False))
        
        # 组合结果为前端期望的格式
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
        
        # 保存结果到JSON文件
        results_file = os.path.join(RESULTS_PATH, "processing_results.json")
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print("\n处理摘要:")
        print(f"全局图像: {global_success}/{len(global_results)} 成功处理")
        print(f"局部图像: {local_success}/{len(local_results)} 成功处理")
        print(f"总颗粒数: 全局={global_particles}, 局部={local_particles}")
        print(f"结果已保存到 {results_file}")
        
        return all_results
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"处理图像时出错: {str(e)}")
        return []
    
    # Save results to JSON file
    results_file = os.path.join(RESULTS_PATH, "processing_results.json")
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print("\nProcessing Summary:")
    print(f"Global images: {global_success}/{len(global_results)} successfully processed")
    print(f"Local images: {local_success}/{len(local_results)} successfully processed")
    print(f"Total particles: Global={global_particles}, Local={local_particles}")
    print(f"Results saved to {results_file}")
    
    return all_results

if __name__ == "__main__":
    main()
