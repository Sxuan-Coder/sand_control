# Add the following endpoints to the sand_image_api.py file
from fastapi import APIRouter
from fastapi.responses import JSONResponse, FileResponse
import os
import json
import sys

# 创建APIRouter实例
router = APIRouter()

# backend_dir 设置为 python 目录的绝对路径
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@router.post("/sand/custom-processing")
async def process_custom_images():
    """
    Process sand particle images with specified background models
    """
    import subprocess
    import sys
    
    try:
        # Get the python executable path
        python_executable = sys.executable
        
        # Get the script path
        script_path = os.path.join(backend_dir, "process_sand_images.py")
        
        # Run the script as a subprocess
        process = subprocess.Popen(
            [python_executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for the process to complete
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"Script execution failed: {stderr}"
                },
                status_code=500
            )
        
        return JSONResponse(
            content={
                "success": True,
                "message": "Images processed successfully",
                "output": stdout
            }
        )
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"Error processing images: {str(e)}"
            },
            status_code=500
        )

@router.get("/sand/processing-results")
async def get_processing_results():
    """
    Get the results of the custom image processing
    """
    import json
    
    try:
        # Results file path
        results_path = os.path.join("C:\\Users\\ASUS\\Desktop\\SandControl\\results", "processing_results.json")
        
        # Check if the file exists
        if not os.path.exists(results_path):
            return JSONResponse(
                content={
                    "success": False,
                    "error": "No processing results found"
                },
                status_code=404
            )
        
        # Read the results file
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        return JSONResponse(content=results)
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"Error getting processing results: {str(e)}"
            },
            status_code=500
        )

@app.get("/sand/image/{image_filename:path}")
async def get_image(image_filename: str):
    """
    Serve an image file
    """
    try:
        # Construct the file path from the results directory
        image_path = os.path.join("C:\\Users\\ASUS\\Desktop\\SandControl\\results", image_filename)
        
        # Check if the file exists
        if not os.path.isfile(image_path):
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"Image not found: {image_filename}"
                },
                status_code=404
            )
        
        # Return the image file
        return FileResponse(image_path)
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"Error getting image: {str(e)}"
            },
            status_code=500
        )
