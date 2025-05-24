import serial
import time

def test_serial_connection():
    try:
        # 尝试连接COM5串口
        port = "COM5"
        print(f"尝试连接串口：{port}")
        
        # 打开串口
        ser = serial.Serial(
            port=port,
            baudrate=9600,
            stopbits=1,
            bytesize=8,
            parity='N',
            timeout=1.0
        )
        
        if ser.is_open:
            print(f"成功打开串口 {port}")
            
            # 发送一些测试数据（这里使用Modbus RTU格式的读取保持寄存器命令）
            # 从站地址01，功能码03，起始地址0x0050，寄存器数量0002，CRC校验
            command = bytes([0x01, 0x03, 0x00, 0x50, 0x00, 0x02, 0xC4, 0x1A])
            
            # 循环读取10次
            for i in range(10):
                print(f"\n--- 第 {i+1} 次测试 ---")
                
                # 清空接收缓冲区
                ser.reset_input_buffer()
                
                # 发送命令
                ser.write(command)
                print(f"已发送命令: {command.hex()}")
                
                # 等待响应
                time.sleep(0.1)
                
                # 读取响应
                if ser.in_waiting:
                    response = ser.read(ser.in_waiting)
                    print(f"收到响应: {response.hex()}")
                    
                    # 如果响应符合Modbus RTU格式（至少5个字节）
                    if len(response) >= 7:
                        # 检查从站地址和功能码
                        if response[0] == 0x01 and response[1] == 0x03:
                            # 数据长度
                            data_len = response[2]
                            if data_len == 4:  # 两个寄存器，每个2字节
                                # 提取数据
                                reg1 = (response[3] << 8) | response[4]
                                reg2 = (response[5] << 8) | response[6]
                                
                                # 组合为32位整数
                                value = (reg1 << 16) | reg2
                                
                                # 处理补码表示的负数
                                if value & 0x80000000:  # 如果最高位为1，说明是负数
                                    value = -((~value + 1) & 0xFFFFFFFF)
                                
                                # 转换为克
                                weight = value / 1000.0
                                print(f"解析的重量: {weight}g")
                else:
                    print("未收到响应")
                
                # 等待1秒再次测试
                time.sleep(1)
            
            # 关闭串口
            ser.close()
            print("\n测试完成，已关闭串口")
        else:
            print(f"无法打开串口 {port}")
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    test_serial_connection()
