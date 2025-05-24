import time

import serial

from config.default_config import USRIO_PORT
from utils.modbus_utils import set_servo_angle, servo_write
from utils.socket_utils import valve_controller, connect_socket

# usrio_port = USRIO_PORT
# 配置串口
ser = serial.Serial(
    port='COM7',  # 串口设备名称（根据实际情况修改）
    baudrate=115200,      # 波特率
)

# pwm = 0
# pwm = 2000
# port = '001'
# Time = '0100'
# cmd = f"#{port}P{pwm}T{Time}!\n"
# ser.write(cmd.encode())

# set_servo_angle(ser,90,'000','0100')
# ser, client = connect_Device()
# set_servo_angle(ser, 0, '001', '0100')

# 开
# cmd1 = set_servo_angle(135, '004', '0100')
# cmd2 = set_servo_angle(-135, '005', '0100')
cmd5 = set_servo_angle(0, '000', '0100')

servo_write(ser,cmd5)



# servo_write(ser,cmd3)
# count = 0
# while count < 256:
#     # 将 count 转换为字符串，并补零到 3 位
#     count_str = str(count).zfill(3)
#     print(count_str)
#     set_servo_angle(ser, 0, count_str, '0100')
#     time.sleep(2)
#
#     count += 1
# ser, client = connect_Device()
# response = client.read_holding_registers(83, 1, 1)
# if not response.isError():
#     # 获取传感器数据
#     data = response.registers
#
#     print(data[0])
# usrio_client = connectSocket(usrio_port)
# conn, addr = usrio_client.accept()
#
# valve_controller(conn, '01', True)
# time.sleep(1)
# valve_controller(conn, '06', True)
# time.sleep(0.2)
# valve_controller(conn, '07', True)
# time.sleep(0.5)
# valve_controller(conn, '02', True)
# time.sleep(3)
#
# valve_controller(conn, '07', False)
# time.sleep(0.2)
# valve_controller(conn, '06', False)
# time.sleep(0.2)
# valve_controller(conn, '02', False)
# time.sleep(0.2)
# valve_controller(conn, '01', False)