import time
import modbus_tk.defines as cst

from utils.socket_utils import valve_controller


def work_handle(master, work_num, values, t=1):
    """发送数据到设备"""
    # work_num: 寄存器地址   output_value: 状态控制0停止，1触发/参数控制：参数值
    #  cst.WRITE_SINGLE_REGISTER  modbus控制向PLC 的某个寄存器写入一个值
    master.execute(10, cst.WRITE_SINGLE_REGISTER, work_num, output_value=values)
    time.sleep(t)

def triggle_or_save_action(master, addr, t=1):
    """触发其他动作（背光源等）/保存动作或动作组合"""
    work_handle(master, addr, 1, t)

def stop_action(master, addr):
    """停止动作（动作组合、背光源等）"""
    work_handle(master, addr, 0, 1)

def triggle_single_action(master, idx, t=1):
    """触发单一动作，寄存器地址4，args: 1-11（11个单一动作）0: 停止"""
    work_handle(master, 4, idx, t)

def stop_single_action(master, t=1):
    """停止单一动作"""
    work_handle(master, 4, 0, t)

def set_servo_angle(angle, port, Time):
    """设置舵机角度"""
    # 角度范围限制在 0-270 度之间
    pwm1 = int(angle * (1000 / 135) + 1500)  # 计算所需脉冲大小
    # 设定保护值，在 510~2490 范围内的波特率能够正常工作
    cmd = f"#{port}P{pwm1}T{Time}!"  # 发送控制指令
    return cmd

def servo_write(ser, *args):
    """写入舵机命令"""
    if len(args) == 1:
        cmd = args[0]  # 单个字符串，直接赋值
    else:
        cmd = '{' + ' '.join(args) + '}'  # 多个字符串，用 { } 括起来
    print(cmd)  # 示例：打印 cmd
    ser.write(cmd.encode())  # 发送指令到控制板
    time.sleep(0.01)

def servo_control(master, ser, client, once_count):
    """控制舵机进行给料操作，并监控给料量"""
    while True:
        try:
            # 读取传感器数据
            response = client.read_holding_registers(83, 1, 1)
            if not response.isError():
                # 获取传感器数据
                data = response.registers

                if data[0] >= once_count * 1000:
                    print("传感器数据：", data[0])
                    # 停止给料
                    master.execute(10, cst.WRITE_SINGLE_REGISTER, 5, output_value=0)
                    time.sleep(1)
                    # 下料翻转
                    cmd0 = set_servo_angle(135, '000', '0100')
                    servo_write(ser, cmd0)
                    time.sleep(1.5)
                    # 复位
                    cmd1 = set_servo_angle(-75, '004', '0100')
                    cmd2 = set_servo_angle(40, '005', '0100')
                    cmd3 = set_servo_angle(0, '000', '0100')
                    servo_write(ser, cmd1, cmd2, cmd3)
                    time.sleep(2)
                    break
            else:
                print("读取传感器数据失败:", response)
        except Exception as e:
            print(f"控制过程出错: {e}")
            break

def get_sand(ser, client, master, once_count):
    """执行给料操作"""
    # 打开给料阀门
    cmd1 = set_servo_angle(135, '004', '0100')
    cmd2 = set_servo_angle(-135, '005', '0100')
    # 初始化舵机角度 0
    cmd3 = set_servo_angle(0, '000', '0100')

    servo_write(ser, cmd1, cmd2, cmd3)
    time.sleep(1)

    # 启动给料
    master.execute(10, cst.WRITE_SINGLE_REGISTER, 5, output_value=1)
    # 监控给料量
    servo_control(master, ser, client, once_count)

def shensuogan_hui(conn):
    """伸缩杆回缩控制"""
    # 这里对伸缩杆进行控制
    valve_controller(conn, '03', False)
    time.sleep(1)
    valve_controller(conn, '05', False)
    time.sleep(1)
    valve_controller(conn, '02', False)
    time.sleep(1)
    valve_controller(conn, '04', False)

def shensuogan_shen(conn):
    """伸缩杆伸出控制"""
    # 这里对伸缩杆进行控制
    valve_controller(conn, '02', True)
    time.sleep(1)
    valve_controller(conn, '04', True)
    time.sleep(1)
    valve_controller(conn, '05', True)
    time.sleep(1)
    valve_controller(conn, '03', True)

def out_sand(master, s, addr, bamper):
    """出料控制"""
    # 开启出料口
    valve_controller(s, addr, True)

    # 出料动作执行----下---2（寄存器地址）
    triggle_single_action(master, 2, 1)
    # 调用伸缩杆出料
    shensuogan_shen(s)
    time.sleep(2)
    shensuogan_hui(s)
    # 完成出料，停止----0
    triggle_single_action(master, 0, 1)
    valve_controller(s, addr, False) 