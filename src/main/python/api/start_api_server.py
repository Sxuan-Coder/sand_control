"""
启动沙粒图像处理API服务器
"""
import uvicorn
import os
import sys

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)  # python目录
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# 设置端口
PORT = 8000

if __name__ == "__main__":
    print(f"正在启动沙粒图像处理API服务器，端口: {PORT}")
    print(f"项目根目录: {backend_dir}")
    try:
        # 启动API服务器
        uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)
    except Exception as e:
        print(f"启动服务器失败: {e}")
