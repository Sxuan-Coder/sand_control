"""
沙粒图像处理 API 服务器
提供沙粒图像处理的 API 接口
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import subprocess
import sys

# 创建 FastAPI 应用
app = FastAPI(title="沙粒图像处理 API")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义路径
RESULTS_PATH = r"C:\Users\ASUS\Desktop\SandControl\results"
SCRIPT_PATH = r"C:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\process_sand_images.py"

@app.post("/process")
async def process_images():
    """
    使用指定的背景模型处理沙粒图像
    """
    try:
        # 获取 Python 可执行文件路径
        python_executable = sys.executable
        
        # 设置脚本的工作目录
        script_dir = os.path.dirname(SCRIPT_PATH)
        
        # 以子进程运行脚本
        process = subprocess.Popen(
            [python_executable, SCRIPT_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=script_dir  # 设置工作目录
        )
        
        # 等待进程完成
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"脚本执行失败: {stderr}"
                },
                status_code=500
            )
        
        return JSONResponse(
            content={
                "success": True,
                "message": "图像处理成功",
                "output": stdout
            }
        )
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"处理图像时出错: {str(e)}"
            },
            status_code=500
        )

@app.get("/results")
async def get_results():
    """
    获取自定义图像处理的结果
    """
    try:
        # 结果文件路径
        results_path = os.path.join(RESULTS_PATH, "processing_results.json")
        
        # 检查文件是否存在
        if not os.path.exists(results_path):
            return JSONResponse(
                content={
                    "success": False,
                    "error": "未找到处理结果"
                },
                status_code=404
            )
        
        # 读取结果文件
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        return JSONResponse(content=results)
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"获取处理结果时出错: {str(e)}"
            },
            status_code=500
        )

@app.get("/image/{image_filename:path}")
async def get_image(image_filename: str):
    """
    提供图像文件
    """
    try:
        # 从结果目录构建文件路径
        image_path = os.path.join(RESULTS_PATH, image_filename)
        
        # 检查文件是否存在
        if not os.path.isfile(image_path):
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"未找到图像: {image_filename}"
                },
                status_code=404
            )
        
        # 返回图像文件
        return FileResponse(image_path)
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"获取图像时出错: {str(e)}"
            },
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
