import uvicorn
import argparse
import sys
import os


def main():
    """启动FastAPI服务器"""
    # 添加项目根目录到Python路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # 设置Python模块导入的基础路径
    backend_dir = os.path.abspath(os.path.join(current_dir, '..'))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    parser = argparse.ArgumentParser(description="沙粒控制系统API服务器")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="启用热重载（仅用于开发环境）")
    parser.add_argument("--mock", action="store_true", help="使用模拟模式，不连接实际硬件")
    args = parser.parse_args()

    # 启动前处理模拟模式
    if args.mock:
        os.environ["USE_MOCK_MODE"] = "1"
        print("使用模拟模式启动，不会连接实际硬件")

    print(f"启动沙粒控制系统API服务器，地址: {args.host}:{args.port}")

    # 使用绝对导入路径启动
    uvicorn.run(
        "api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
