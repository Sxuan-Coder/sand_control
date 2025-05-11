import serial
from pymodbus.client import ModbusSerialClient
import time

def process_weight(registers):
    """处理寄存器数据为重量值"""
    # 从两个寄存器中获取32位整数，高位在前
    value = (registers[0] << 16) | registers[1]
    
    # 处理补码表示的负数
    if value & 0x80000000:  # 如果最高位为1，说明是负数
        value = -((~value + 1) & 0xFFFFFFFF)
    
    return value / 1000.0  # 返回克值（原始值为毫克）

def test_scale():
    # 创建ModbusClient
    try:
        port = "COM5"  # 使用COM5串口
        print(f"尝试连接电子秤，串口：{port}")
        
        # 尝试直接使用串口连接，不使用ModbusClient
        try:
            # 尝试打开串口以验证连接
            ser = serial.Serial(
                port=port,
                baudrate=9600,
                stopbits=1,
                bytesize=8,
                parity='N',
                timeout=1.0
            )
            
            if ser.is_open:
                ser.close()  # 关闭串口，稍后由ModbusClient重新打开
                print(f"串口 {port} 连接测试成功")
            else:
                print(f"串口 {port} 无法打开")
                return
        except Exception as e:
            print(f"串口 {port} 连接测试失败: {str(e)}")
            return
        
        # 创建ModbusClient
        client = ModbusSerialClient(
            port=port,
            baudrate=9600,
            stopbits=1,
            bytesize=8,
            parity='N',
            timeout=1.0
        )
        
        print(f"ModbusSerialClient创建完成，尝试连接...")
        connection_result = client.connect()
        print(f"连接结果: {connection_result}")
        
        if connection_result:
            # 连接成功后等待设备就绪
            time.sleep(0.5)
            
            # 从站地址
            slave_address = 0x01
            
            # 重量数据寄存器地址 - 使用0x50（十进制80）
            register_address = 0x50
            
            # 读取10次重量数据
            for i in range(10):
                try:
                    # 读取保持寄存器（功能码03H）
                    result = client.read_holding_registers(address=register_address, count=2, slave=slave_address)
                    print(f"读取结果: {result}")
                    
                    if result and not result.isError():
                        weight = process_weight(result.registers)
                        print(f"成功读取重量: {weight}g")
                    else:
                        print(f"读取重量失败: {result}")
                except Exception as e:
                    print(f"读取重量时发生异常: {str(e)}")
                
                # 等待1秒再次读取
                time.sleep(1)
            
            # 关闭连接
            client.close()
            print("测试完成，已断开连接")
        else:
            print(f"无法连接到串口 {port}")
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    test_scale()
