import socket
import time


def connect_socket(port):
    """建立socket连接"""
    HOST = ''  # 定义侦听本地地址口（多个IP地址情况下），这里表示侦听所有
    PORT = port  # Server端开放的服务端口
    server = socket.socket()  # 使用TCP协议
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    server.bind((HOST, PORT))
    server.listen(6)
    print("Socket服务器开始运行....")
    return server


def calc_crc(string):
    """CRC校验计算"""
    data = bytearray.fromhex(string)
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for i in range(8):
            if (crc & 1) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    hex_crc = hex(((crc & 0xff) << 8) + (crc >> 8))  # 返回十六进制
    crc_0 = crc & 0xff
    crc_1 = crc >> 8
    str_crc_0 = '{:02x}'.format(crc_0).upper()
    str_crc_1 = '{:02x}'.format(crc_1).upper()
    return str_crc_0 + " " + str_crc_1  # 返回两部分十六进制字符


def valve_controller(s, index, open_or_close):
    """阀门控制功能"""
    if open_or_close:
        command = "11 05 00" + " " + index + " " + "FF 00"
    else:
        command = "11 05 00" + " " + index + " " + "00 00"

    print(command)
    command += " " + calc_crc(command)
    command = bytearray.fromhex(command)
    print(command)
    s.send(command)


def shensuogan_hui(conn):
    """伸缩杆回缩控制"""
    valve_controller(conn, '02', False)
    time.sleep(1)
    valve_controller(conn, '03', False)
    time.sleep(1)
    valve_controller(conn, '04', True)
    time.sleep(1)
    valve_controller(conn, '05', True)
    time.sleep(1)


def shensuogan_shen(conn):
    """伸缩杆伸出控制"""
    valve_controller(conn, '04', False)
    time.sleep(1)
    valve_controller(conn, '05', False)
    time.sleep(1)
    valve_controller(conn, '02', True)
    time.sleep(1)
    valve_controller(conn, '03', True)
    time.sleep(1)
