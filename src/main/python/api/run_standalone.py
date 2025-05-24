import uvicorn

if __name__ == "__main__":
    print("Starting Sand Image Processing API on http://0.0.0.0:8000")
    uvicorn.run("sand_api:app", host="0.0.0.0", port=8000, reload=True)
