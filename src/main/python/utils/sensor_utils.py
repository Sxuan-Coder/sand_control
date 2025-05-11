import serial
from pymodbus import framer
from pymodbus.client import ModbusSerialClient


def connect_device(reconnect_only=False):
    """连接舵机和传感器设备"""
    try:
        # 传感器连接
        client = ModbusSerialClient(
            port='COM5',  # 串口号
            framer=framer.FramerType.RTU,  # 使用 RTU 协议
            baudrate=9600,  # 波特率
            parity='N',  # 校验位
            stopbits=1,  # 停止位
        )
        connection = client.connect()
        if not connection:
            raise ConnectionError("传感器串口(COM5)连接失败，请检查设备连接状态")

        # 只有在不是重新连接模式时才连接舵机
        if not reconnect_only:
            # 舵机连接
            try:
                ser = serial.Serial('COM7', 115200)  # 根据实际情况设置串口号和波特率
            except serial.SerialException as e:
                raise ConnectionError(f"舵机串口(COM7)连接失败: {str(e)}")
                
            if not ser.is_open:
                raise ConnectionError("舵机串口(COM7)打开失败，请检查设备连接状态")
        else:
            ser = None
            
        return ser, client
        
    except Exception as e:
        if isinstance(e, ConnectionError):
            raise
        raise ConnectionError(f"设备连接过程中发生错误: {str(e)}")