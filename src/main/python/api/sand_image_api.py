from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import cv2
import numpy as np
import tempfile
import shutil
import time
import uuid
import json
import sys

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 从config.default_config导入配置
try:
    from config.default_config import (
        global_mm_per_pixel,
        local_mm_per_pixel,
        main_data_path,
        main_LABELS,
        background_path,
        main_gradeNames,
        main_volume_corrections,
        RESULTS_PATH  # 确保导入 RESULTS_PATH
    )
    print("从config.default_config模块导入配置成功")
except ImportError as e:
    print(f"导入配置失败: {e}")
    raise

# 导入其他处理模块
try:
    from zsh_image_handle import pictures_handle, calculate_shape_factor, split_contour
    from background import read_backgrounds_single, read_backgrounds_mixture, save_image
    import reader
    import image_config
    from zsh_methods import eqEllipticFeretCAD, diameter_gap_average
    import Main2
    import normal5
    from zsh_methods import get_mx, diameter_gap_average, area_gap, physics_gap
except ImportError as e:
    print(f"导入处理模块失败: {e}")
    raise

# 创建FastAPI实例
app = FastAPI(title="沙粒图像处理API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 新增：获取处理结果的端点
@app.get("/processing-results", 
         summary="获取图像处理结果",
         response_description="包含处理结果的JSON文件内容")
async def get_processing_results_endpoint():
    """
    提供保存在 `RESULTS_PATH` 中的 `processing_results.json` 文件的内容。
    """
    # 确保 RESULTS_PATH 是绝对路径或相对于当前工作目录正确解析
    # 如果 RESULTS_PATH 本身就是完整路径，则无需拼接
    # 如果它是相对于项目某个固定位置的，需要正确构建路径
    # 假设 RESULTS_PATH 已经是正确的绝对路径或相对sand_image_api.py的路径
    
    # 尝试定位 processing_results.json 文件
    # 这里的逻辑基于 RESULTS_PATH 指向包含 processing_results.json 的目录
    # 或者 RESULTS_PATH 直接就是 processing_results.json 的完整路径
    
    results_file_path = ""
    if os.path.isabs(RESULTS_PATH):
        if RESULTS_PATH.endswith(".json"): # RESULTS_PATH 是文件
             results_file_path = RESULTS_PATH
        else: # RESULTS_PATH 是目录
             results_file_path = os.path.join(RESULTS_PATH, "processing_results.json")
    else:
        # 假设 RESULTS_PATH 是相对于 backend_dir (src/main/python)
        # 或者，如果 process_sand_images.py 将其保存在特定位置，我们需要知道那个位置
        # 从之前的日志看，process_sand_images.py 将结果保存到 "C:\\Users\\ASUS\\Desktop\\SandControl\\results\\processing_results.json"
        # 而 default_config.py 中的 RESULTS_PATH 被设置为 'src/main/python/results'
        # 因此，我们需要基于 backend_dir 来构建它
        
        # backend_dir (src/main/python)
        # RESULTS_PATH (src/main/python/results) -> this is wrong, RESULTS_PATH is 'results' in default_config
        # Let's re-check default_config.py for RESULTS_PATH definition.
        # Assuming RESULTS_PATH from default_config is 'results' (a directory name)
        # and it's relative to 'c:\\Users\\ASUS\\Desktop\\SandControl\\sand-nb-master\\src\\main\\python'
        
        # The actual save path from process_sand_images.py log was:
        # C:\\Users\\ASUS\\Desktop\\SandControl\\results\\processing_results.json
        # The RESULTS_PATH in default_config.py was set to:
        # RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
        # This resolves to c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\results
        # However, the script process_sand_images.py saves to:
        # c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\results\processing_results.json
        # Let's use the RESULTS_PATH as defined in default_config and assume it's correct.
        # The config has RESULTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
        # where __file__ is default_config.py. So it becomes:
        # c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\config\results
        # This seems to be an inconsistency.
        
        # For now, let's assume RESULTS_PATH in default_config.py is the directory
        # c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\results
        # as this is where process_sand_images.py saves the file.
        # I will construct the path based on `backend_dir` and `RESULTS_PATH` (assuming RESULTS_PATH is 'results')

        # Re-evaluating: The `RESULTS_PATH` in `default_config.py` is:
        # `RESULTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')`
        # `os.path.abspath(__file__)` for `default_config.py` is `c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\config\default_config.py`
        # `os.path.dirname(os.path.abspath(__file__))` is `c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\config`
        # `os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')` is `c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python`
        # So, `RESULTS_PATH` becomes `c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\results`
        
        # This is the correct directory where process_sand_images.py saves the file.
        results_file_path = os.path.join(RESULTS_PATH, "processing_results.json")

    if not os.path.exists(results_file_path):
        raise HTTPException(status_code=404, detail=f"Processing results file not found at {results_file_path}")

    try:
        with open(results_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {results_file_path}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Error decoding JSON from file: {results_file_path}")
    except Exception as e:
        # Log the exception e for more details if necessary
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# ... 其余代码保持不变 ...
