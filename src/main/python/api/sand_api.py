from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import subprocess
import sys

# Create FastAPI app
app = FastAPI(title="Sand Image Processing API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define paths
RESULTS_PATH = r"C:\Users\ASUS\Desktop\SandControl\results"
SCRIPT_PATH = r"C:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\process_sand_images.py"

@app.post("/process")
async def process_images():
    """
    Process sand particle images with specified background models
    """
    try:
        # Get the python executable path
        python_executable = sys.executable
        
        # Run the script as a subprocess
        process = subprocess.Popen(
            [python_executable, SCRIPT_PATH],
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

@app.get("/results")
async def get_results():
    """
    Get the results of the custom image processing
    """
    try:
        # Results file path
        results_path = os.path.join(RESULTS_PATH, "processing_results.json")
        
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

@app.get("/image/{image_filename:path}")
async def get_image(image_filename: str):
    """
    Serve an image file
    """
    try:
        # Construct the file path from the results directory
        image_path = os.path.join(RESULTS_PATH, image_filename)
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
