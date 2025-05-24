# 测试pymodbus导入
import sys
print(f"Python版本: {sys.version}")

try:
    print("尝试导入: from pymodbus.client import ModbusSerialClient")
    from pymodbus.client import ModbusSerialClient
    print("导入成功!")
    print(f"ModbusSerialClient类: {ModbusSerialClient}")
except ImportError as e:
    print(f"导入失败: {str(e)}")

try:
    print("\n尝试导入: from pymodbus.client.sync import ModbusSerialClient")
    from pymodbus.client.sync import ModbusSerialClient
    print("导入成功!")
    print(f"ModbusSerialClient类: {ModbusSerialClient}")
except ImportError as e:
    print(f"导入失败: {str(e)}")

# 检查已安装的pymodbus版本
try:
    import pymodbus
    print(f"\npymodbus版本: {pymodbus.__version__}")
except (ImportError, AttributeError) as e:
    print(f"\n无法获取pymodbus版本: {str(e)}")

# 列出pymodbus模块内容
print("\npymodbus模块内容:")
for item in dir(pymodbus):
    print(f"  - {item}")

# 检查client模块
try:
    import pymodbus.client
    print("\npymodbus.client模块内容:")
    for item in dir(pymodbus.client):
        print(f"  - {item}")
except ImportError as e:
    print(f"\n无法导入pymodbus.client: {str(e)}")
