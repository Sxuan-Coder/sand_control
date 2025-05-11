import os
import time
from modbus_tk import modbus_tcp
import modbus_tk.defines as cst
from concurrent.futures import ThreadPoolExecutor
from control.camera_control import CameraControl
from config.default_config import WGD_IP, WGD_PORT
from control.clean_control import CleanSandControl
from utils.modbus_utils import triggle_or_save_action, triggle_single_action, stop_single_action, stop_action
from utils.sensor_utils import connect_device
from utils.socket_utils import connect_socket
from camera.MvImport.MvCameraControl_class import *
import socket


class ProcessControl:
    def __init__(self):
        """初始化流程控制类"""
        self.master = None
        self.socket_client = None
        self.conn = None
        self.addr = None
        self.ser = None
        self.client = None
        self.camera = None
        self.cleaner = None
        self.thread_pool = None

        try:
            # 1. 初始化共享的 modbus 连接
            try:
                self.master = modbus_tcp.TcpMaster(WGD_IP, WGD_PORT)
                self.master.set_timeout(10.0)
                # 测试连接
                print("已连接到控制台")
            except Exception as e:
                raise Exception(f"控制台连接失败: {str(e)}")

            # 2. 初始化共享的 socket 连接
            try:
                self.socket_client = connect_socket(50007)
                print("等待Socket客户端连接...")

                # 使用超时版本的accept
                self.conn, self.addr = self.socket_client.accept()
                print("Socket连接已建立")


            except Exception as e:
                raise Exception(f"Socket连接失败: {str(e)}")

            # 3. 初始化给料控制
            try:
                self.ser, self.client = connect_device()  # 连接舵机和传感器
                print("给料控制器初始化完成")
            except Exception as e:
                raise Exception(f"给料控制器初始化失败: {str(e)}")

            # 4. 初始化相机
            try:
                # 创建线程池
                self.thread_pool = ThreadPoolExecutor(max_workers=4)

                # 初始化相机SDK
                ret = MvCamera.MV_CC_Initialize()
                if ret != 0:
                    raise Exception("相机SDK初始化失败! ret[0x%x]" % ret)

                # 初始化相机控制
                self.camera = CameraControl()  # 直接使用CameraControl类
                self.camera.master = self.master  # 传递已存在的modbus连接
                # self.camera.initialize()  # 初始化相机

                # 验证相机是否正确初始化
                if not self.camera.cameras:
                    raise Exception("没有找到可用的相机")

                print("相机控制初始化完成")
            except Exception as e:
                raise Exception(f"相机初始化失败: {str(e)}")

            # 5. 初始化清砂控制
            try:
                self.cleaner = CleanSandControl()
                self.cleaner.master = self.master
                self.cleaner.socket_client = self.socket_client
                self.cleaner.conn = self.conn
                self.cleaner.addr = self.addr
                print("清砂控制初始化完成")
            except Exception as e:
                raise Exception(f"清砂控制初始化失败: {str(e)}")

            print("清砂控制初始化完成")

        except Exception as e:
            # 确保在任何错误发生时都清理资源
            self.close()
            # 重新抛出异常
            raise Exception(f"清砂控制初始化失败: {str(e)}")

    def set_servo_angle(self, angle, port, Time):
        """设置舵机角度"""
        pwm1 = int(angle * (1000 / 135) + 1500)
        cmd = f"#{port}P{pwm1}T{Time}!"
        return cmd

    def servo_write(self, *args):
        """写入舵机命令"""
        if len(args) == 1:
            cmd = args[0]
        else:
            cmd = '{' + ' '.join(args) + '}'
        print(f"舵机命令: {cmd}")
        self.ser.write(cmd.encode())
        time.sleep(0.01)

    def servo_control(self, once_count):
        """控制给料量"""
        while True:
            try:
                # 读取传感器数据
                response = self.client.read_holding_registers(83)
                if not response.isError():
                    data = response.registers
                    if data[0] >= once_count * 1000:
                        print("传感器数据：", data[0])
                        # 停止给料
                        self.master.execute(10, cst.WRITE_SINGLE_REGISTER, 5, output_value=0)
                        time.sleep(1)
                        # 下料翻转
                        cmd0 = self.set_servo_angle(135, '000', '0100')
                        self.servo_write(cmd0)
                        time.sleep(1.5)
                        # 复位
                        cmd1 = self.set_servo_angle(-75, '004', '0100')
                        cmd2 = self.set_servo_angle(40, '005', '0100')
                        cmd3 = self.set_servo_angle(0, '000', '0100')
                        self.servo_write(cmd1, cmd2, cmd3)
                        time.sleep(2)
                        break
                else:
                    print("读取传感器数据失败:", response)
            except Exception as e:
                print(f"控制过程出错: {e}")
                break

    def start_feeding(self, once_count=1.2):
        """开始给料"""
        try:
            # 设置初始舵机角度
            cmd1 = self.set_servo_angle(135, '004', '0100')
            cmd2 = self.set_servo_angle(-135, '005', '0100')
            cmd3 = self.set_servo_angle(0, '000', '0100')
            self.servo_write(cmd1, cmd2, cmd3)
            time.sleep(1)

            print(f"开始给料 {once_count}克...")
            # 启动给料
            self.master.execute(10, cst.WRITE_SINGLE_REGISTER, 5, output_value=1)
            # 监控给料量
            self.servo_control(once_count)
            print("给料完成")

        except Exception as e:
            print(f"给料过程出错: {e}")
            self.stop_feeding()

    def stop_feeding(self):
        """停止给料"""
        try:
            self.master.execute(10, cst.WRITE_SINGLE_REGISTER, 5, output_value=0)
            time.sleep(1)
            # 重置舵机位置
            cmd = self.set_servo_angle(0, '000', '0100')
            self.servo_write(cmd)
            print("给料已停止")
        except Exception as e:
            print(f"停止给料时出错: {e}")

    def _get_last_group_number(self, base_path):
        """
        获取指定目录下已存在的最大组号
        """
        try:
            max_group = 0
            # 检查global和local两个目录
            for folder in ["global", "local"]:
                folder_path = os.path.join(base_path, folder)
                if not os.path.exists(folder_path):
                    continue

                # 遍历目录中的所有文件
                for filename in os.listdir(folder_path):
                    if filename.endswith('.jpg'):
                        # 文件名格式为: "组号_照片号.jpg"
                        try:
                            group_num = int(filename.split('_')[0])
                            max_group = max(max_group, group_num)
                        except (ValueError, IndexError):
                            continue

            return max_group
        except Exception as e:
            print(f"获取最大组号时出错: {str(e)}")
            return 0

    def execute_process(self, base_path, sand_total=500, once_count=0.1, start_group=None, photos_per_group=5):
        """
        执行完整的拍照和清砂流程

        Args:
            base_path: 保存图片的基础路径
            sand_total: 总砂量（克）
            once_count: 每次给料量（克）
            start_group: 起始组号，如果为None则自动获取下一组号
            photos_per_group: 每组照片数，默认为5
        """
        try:
            print("\n开始执行拍照和清砂流程...")
            total_start_time = time.time()

            # 如果没有指定起始组号，则自动获取下一组号
            if start_group is None:
                last_group = self._get_last_group_number(base_path)
                group_count = last_group + 1
            else:
                group_count = start_group

            print(f"从第 {group_count} 组开始拍摄...")
            total = sand_total / once_count  # 计算总次数

            # 开启背光源
            triggle_or_save_action(self.master, 2, 1)

            while total > 0:
                # 1. 给料
                self.start_feeding(once_count)
                time.sleep(0.3)  # 等待给料稳定

                # 2. 向左振动（移到给料后执行）
                triggle_single_action(self.master, 3, 1)
                stop_single_action(self.master, 0.3)

                # 3. 执行拍照和振动循环
                photo_count = 1
                while photo_count <= photos_per_group:  # 使用传入的每组照片数
                    # 初始振动
                    if photo_count == 1:
                        triggle_single_action(self.master, 11, 5)
                    # 振动
                    print(f"第 {photo_count} 次振动...")
                    triggle_single_action(self.master, 11, 0.5)
                    stop_single_action(self.master, 0.6)

                    # 拍照 - 使用CameraControl的方法拍照
                    photo_start_time = time.time()
                    try:
                        # 创建保存路径
                        photo_name = f"{group_count}_{photo_count}"

                        # 调用camera_control中的拍照方法
                        if self.camera.capture_images(base_path, photo_name):
                            photo_end_time = time.time()
                            photo_duration = photo_end_time - photo_start_time
                            print(f"第 {group_count} 组第 {photo_count} 张照片拍摄完成，耗时: {photo_duration:.3f} 秒")
                        else:
                            print(f"第 {group_count} 组第 {photo_count} 张照片拍摄失败")

                    except Exception as e:
                        print(f"拍照错误: {str(e)}")
                        print(f"第 {group_count} 组第 {photo_count} 张照片拍摄失败")

                    photo_count += 1

                # 4. 执行清砂操作
                print(f"\n第 {group_count} 组照片拍摄完成，开始清理沙石...")
                if self.cleaner.execute_clean_sequence():
                    print("沙石清理完成")
                else:
                    print("沙石清理失败")

                time.sleep(8)

                total -= 1
                group_count += 1
                print(f"剩余次数: {total}")

            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            print(f"\n总耗时: {total_duration:.3f} 秒")

        except Exception as e:
            print(f"流程执行出错: {str(e)}")
            raise
        finally:
            # 确保停止所有振动动作
            stop_single_action(self.master, 0.3)  # 停止向左振动
            triggle_single_action(self.master, 0, 1)  # 停止散料振动
            # 关闭背光源
            triggle_single_action(self.master, 0, 1)

    def _release_camera_resources(self):
        """释放相机资源"""
        try:
            if hasattr(self, 'camera'):
                self.camera.close()
        except Exception as e:
            print(f"释放相机资源时出错: {str(e)}")
            pass

    def light_open(self):
        triggle_or_save_action(self.master, 2, 1)

    def light_close(self):
        stop_action(self.master, 2)

    def close(self):
        """关闭所有资源"""
        try:
            if self.camera:
                self.camera.close()
            if self.ser:
                self.ser.close()
            if self.conn:
                self.conn.close()
            if self.socket_client:
                self.socket_client.close()
            if self.master:
                self.master.close()
            if self.thread_pool:
                self.thread_pool.shutdown()
        except Exception as e:
            print(f"关闭资源时出错: {str(e)}")
        finally:
            self.camera = None
            self.ser = None
            self.client = None
            self.conn = None
            self.socket_client = None
            self.master = None
            self.thread_pool = None
