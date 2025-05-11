"""
测试模块导入
"""
import sys

def test_imports():
    """测试模块导入功能"""
    print("\n=== 开始测试导入 ===\n")

    # 测试配置模块导入
    print("1. 测试配置模块导入...")
    try:
        from config.default_config import WGD_IP, WGD_PORT
        print(f"   成功: WGD_IP={WGD_IP}, WGD_PORT={WGD_PORT}")
    except ImportError as e:
        print(f"   失败: {e}")

    # 测试相机SDK导入
    print("\n2. 测试相机SDK导入...")
    try:
        from camera.MvImport.MvCameraControl_class import MvCamera
        from camera.MvImport.CameraParams_header import MV_CC_DEVICE_INFO_LIST
        print("   成功")
    except ImportError as e:
        print(f"   失败: {e}")

    # 测试modbus_tk导入
    print("\n3. 测试modbus_tk导入...")
    try:
        import modbus_tk
        print("   成功")
    except ImportError as e:
        print(f"   失败: {e}")

    # 测试工具函数导入
    print("\n4. 测试工具函数导入...")
    try:
        from utils.modbus_utils import triggle_or_save_action
        print("   成功导入modbus_utils")
    except ImportError as e:
        print(f"   失败导入modbus_utils: {e}")

    try:
        from utils.socket_utils import connect_socket
        print("   成功导入socket_utils")
    except ImportError as e:
        print(f"   失败导入socket_utils: {e}")

    try:
        from utils.sensor_utils import connect_device
        print("   成功导入sensor_utils")
    except ImportError as e:
        print(f"   失败导入sensor_utils: {e}")

    # 测试控制模块导入
    print("\n5. 测试控制模块导入...")
    try:
        from control.clean_control import CleanSandControl
        print("   成功导入clean_control")
    except ImportError as e:
        print(f"   失败导入clean_control: {e}")

    try:
        from control.camera_control import CameraControl
        print("   成功导入camera_control")
    except ImportError as e:
        print(f"   失败导入camera_control: {e}")

    try:
        from control.process_control import ProcessControl
        print("   成功导入process_control")
    except ImportError as e:
        print(f"   失败导入process_control: {e}")

    print("\n=== 测试结束 ===\n")

if __name__ == "__main__":
    test_imports() 