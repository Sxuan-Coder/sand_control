"""
启动独立沙粒图像处理 API 服务器
"""
import uvicorn

if __name__ == "__main__":
    print("启动沙粒图像处理 API 服务器，访问地址：http://localhost:8000")
    print("按 Ctrl+C 停止服务器")
    uvicorn.run("standalone_api:app", host="0.0.0.0", port=8000, reload=False)
