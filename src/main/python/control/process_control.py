import os
import time
import json
import serial
import serial.tools.list_ports
import subprocess
from datetime import datetime
from modbus_tk import modbus_tcp
import modbus_tk.defines as cst
from concurrent.futures import ThreadPoolExecutor, Future
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
        self.processing_tasks = []  # 存储异步处理任务
        self.is_running = False  # 控制实验状态
        self.should_stop = False  # 停止标志
        
        # 实验进度状态
        self.current_group = 0  # 当前组号
        self.current_photo = 0  # 当前照片号
        self.total_photos = 0  # 已拍摄的总照片数

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
                self.thread_pool = ThreadPoolExecutor(max_workers=8)  # 增加线程数以支持异步处理

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
            print(f"停止给料时出错: {str(e)}")

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

    def _async_process_single_image(self, image_path, image_type):
        """异步处理单张图片的函数"""
        try:
            import sys
            # 添加项目根目录到路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # 导入图片处理模块
            from process_sand_images import process_image, load_background_model
            
            print(f"开始异步处理单张图片: {image_path} (类型: {image_type})")
            
            # 检查图片文件是否存在
            if not os.path.exists(image_path):
                print(f"图片文件不存在: {image_path}")
                return None
            
            # 加载背景模型
            background = load_background_model(image_type)
            if background is None:
                print(f"无法加载 {image_type} 背景模型")
                return None
            
            # 处理单张图片
            result = process_image(image_path, background, image_type, debug=False)
            
            if result["success"]:
                # 保存单次处理结果
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 包含毫秒
                temp_result_file = os.path.join(
                    r"C:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\results",
                    f"temp_single_result_{timestamp}.json"
                )
                
                # 构建单张图片的结果数据
                single_result = {
                    "image_path": image_path,
                    "image_type": image_type,
                    "original_path": result["original_path"],
                    "classified_path": result["classified_path"],
                    "segmented_path": result["segmented_path"],
                    "contours_count": result["contours_count"],
                    "grade_statistics": result["grade_statistics"],
                    "success": True,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "processing_id": timestamp
                }
                
                # 确保results目录存在
                os.makedirs(os.path.dirname(temp_result_file), exist_ok=True)
                
                with open(temp_result_file, 'w', encoding='utf-8') as f:
                    json.dump(single_result, f, indent=2, ensure_ascii=False)
                
                print(f"单张图片处理完成，结果保存到: {temp_result_file}")
                return temp_result_file
            else:
                print(f"单张图片处理失败: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"异步处理单张图片出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _consolidate_processing_results(self):
        """整合所有处理结果"""
        try:
            results_dir = r"C:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\results"
            
            # 查找所有临时结果文件（包括单张图片和批量处理）
            temp_files = [f for f in os.listdir(results_dir) 
                         if f.startswith("temp_single_result_") or f.startswith("temp_processing_results_")]
            
            if not temp_files:
                print("没有找到待整合的临时结果文件")
                return
            
            print(f"找到 {len(temp_files)} 个临时结果文件，开始整合...")
            
            # 初始化整合结果
            consolidated_results = {
                "global": [],
                "local": [],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "processing_sessions": [],
                "summaryStats": {
                    "global": {
                        "totalImages": 0,
                        "successfulImages": 0,
                        "totalParticles": 0
                    },
                    "local": {
                        "totalImages": 0,
                        "successfulImages": 0,
                        "totalParticles": 0
                    }
                }
            }
            
            # 整合所有临时文件
            for temp_file in sorted(temp_files):
                temp_path = os.path.join(results_dir, temp_file)
                try:
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        temp_data = json.load(f)
                    
                    # 处理单张图片结果
                    if temp_file.startswith("temp_single_result_"):
                        image_type = temp_data.get("image_type", "unknown")
                        if image_type in ["global", "local"]:
                            # 转换单张图片结果为列表格式
                            result_item = {
                                "image_path": temp_data.get("image_path"),
                                "original_path": temp_data.get("original_path"),
                                "classified_path": temp_data.get("classified_path"),
                                "segmented_path": temp_data.get("segmented_path"),
                                "contours_count": temp_data.get("contours_count", 0),
                                "grade_statistics": temp_data.get("grade_statistics", []),
                                "success": temp_data.get("success", False)
                            }
                            consolidated_results[image_type].append(result_item)
                            
                            # 更新统计信息
                            consolidated_results["summaryStats"][image_type]["totalImages"] += 1
                            if temp_data.get("success", False):
                                consolidated_results["summaryStats"][image_type]["successfulImages"] += 1
                                consolidated_results["summaryStats"][image_type]["totalParticles"] += temp_data.get("contours_count", 0)
                    
                    # 处理批量结果（保持向后兼容）
                    elif temp_file.startswith("temp_processing_results_"):
                        # 合并数据
                        consolidated_results["global"].extend(temp_data.get("global", []))
                        consolidated_results["local"].extend(temp_data.get("local", []))
                        
                        # 更新统计信息
                        if "summaryStats" in temp_data:
                            for image_type in ["global", "local"]:
                                if image_type in temp_data["summaryStats"]:
                                    stats = temp_data["summaryStats"][image_type]
                                    consolidated_results["summaryStats"][image_type]["totalImages"] += stats.get("totalImages", 0)
                                    consolidated_results["summaryStats"][image_type]["successfulImages"] += stats.get("successfulImages", 0)
                                    consolidated_results["summaryStats"][image_type]["totalParticles"] += stats.get("totalParticles", 0)
                    
                    # 记录处理会话信息
                    session_info = {
                        "processing_id": temp_data.get("processing_id", "unknown"),
                        "timestamp": temp_data.get("timestamp", "unknown"),
                        "file_type": "single" if temp_file.startswith("temp_single_result_") else "batch"
                    }
                    consolidated_results["processing_sessions"].append(session_info)
                    
                    print(f"整合临时文件: {temp_file}")
                    
                except Exception as e:
                    print(f"整合文件 {temp_file} 时出错: {str(e)}")
                    continue
            
            # 保存整合结果
            final_result_file = os.path.join(results_dir, "processing_results.json")
            with open(final_result_file, 'w', encoding='utf-8') as f:
                json.dump(consolidated_results, f, indent=2, ensure_ascii=False)
            
            print(f"结果整合完成，保存到: {final_result_file}")
            print(f"总计处理: 全局图片 {consolidated_results['summaryStats']['global']['totalImages']} 张, "
                  f"局部图片 {consolidated_results['summaryStats']['local']['totalImages']} 张")
            
            # 清理临时文件
            for temp_file in temp_files:
                temp_path = os.path.join(results_dir, temp_file)
                try:
                    os.remove(temp_path)
                    print(f"删除临时文件: {temp_file}")
                except Exception as e:
                    print(f"删除临时文件 {temp_file} 时出错: {str(e)}")
            
        except Exception as e:
            print(f"整合处理结果时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def stop_process(self):
        """停止实验流程"""
        print("收到停止实验信号...")
        self.should_stop = True
        self.is_running = False
        
        # 重置实验进度状态
        self.current_group = 0
        self.current_photo = 0
        self.total_photos = 0
        
        # 立即停止所有设备动作
        try:
            if self.master:
                # 停止所有振动动作
                stop_single_action(self.master, 0.1)  # 停止向左振动
                triggle_single_action(self.master, 0, 1)  # 停止散料振动
                
                # 关闭背光源
                try:
                    self.master.execute(10, WRITE_SINGLE_REGISTER, 2, output_value=0)
                except:
                    pass
                
                # 确保停止给料
                try:
                    self.stop_feeding()
                except:
                    pass
                
                print("已停止所有设备动作")
        except Exception as e:
            print(f"停止设备动作时出错: {str(e)}")
        
        # 停止相机抓取
        try:
            if hasattr(self, 'camera') and self.camera:
                self.camera.stop_grabbing()
        except Exception as e:
            print(f"停止相机抓取时出错: {str(e)}")
        
        print("实验停止信号已发出，正在安全退出...")

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

            # 检查关键组件状态并在需要时重新初始化
            if self.master is None or self.camera is None or self.cleaner is None:
                print("检测到关键组件未初始化，正在重新初始化...")
                if not self.reinitialize():
                    raise Exception("重新初始化失败，无法继续执行")

            self.is_running = True
            self.should_stop = False
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

            while total > 0 and not self.should_stop:
                # 检查停止信号
                if self.should_stop:
                    print("检测到停止信号，正在安全停止实验...")
                    break
                
                # 1. 给料
                self.start_feeding(once_count)
                time.sleep(0.3)  # 等待给料稳定

                # 检查停止信号
                if self.should_stop:
                    print("给料后检测到停止信号，正在安全停止实验...")
                    break

                # 2. 向左振动（移到给料后执行）
                triggle_single_action(self.master, 3, 1)
                stop_single_action(self.master, 0.3)

                # 3. 执行拍照和振动循环
                photo_count = 1
                while photo_count <= photos_per_group and not self.should_stop:  # 添加停止检查
                    # 检查停止信号
                    if self.should_stop:
                        print("拍照循环中检测到停止信号，正在安全停止实验...")
                        break
                    
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
                        captured_images = self.camera.capture_images(base_path, photo_name)
                        if captured_images:
                            photo_end_time = time.time()
                            photo_duration = photo_end_time - photo_start_time
                            print(f"第 {group_count} 组第 {photo_count} 张照片拍摄完成，耗时: {photo_duration:.3f} 秒")
                            
                            # 更新状态数据
                            self.current_group = group_count
                            self.current_photo = photo_count
                            self.total_photos += 1  # 每拍一张照片就加1
                            
                            # 立即启动单张图片的异步处理任务
                            self._process_captured_images(captured_images, group_count, photo_count)
                        else:
                            print(f"第 {group_count} 组第 {photo_count} 张照片拍摄失败")

                    except Exception as e:
                        print(f"拍照错误: {str(e)}")
                        print(f"第 {group_count} 组第 {photo_count} 张照片拍摄失败")

                    photo_count += 1

                # 检查停止信号（拍照完成后）
                if self.should_stop:
                    print("拍照完成后检测到停止信号，跳过清砂操作...")
                    break

                # 4. 执行清砂操作
                print(f"\n第 {group_count} 组照片拍摄完成，开始清理沙石...")
                if self.cleaner.execute_clean_sequence():
                    print("沙石清理完成")
                else:
                    print("沙石清理失败")

                # 检查停止信号（清砂后）
                if self.should_stop:
                    print("清砂后检测到停止信号，正在安全停止实验...")
                    break

                time.sleep(8)

                total -= 1
                group_count += 1
                print(f"剩余次数: {total}")

            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            
            if self.should_stop:
                print(f"\n实验已被用户停止，总耗时: {total_duration:.3f} 秒")
            else:
                print(f"\n实验正常完成，总耗时: {total_duration:.3f} 秒")

        except Exception as e:
            print(f"流程执行出错: {str(e)}")
            raise
        finally:
            # 确保停止所有振动动作
            try:
                stop_single_action(self.master, 0.3)  # 停止向左振动
                triggle_single_action(self.master, 0, 1)  # 停止散料振动
                # 关闭背光源
                triggle_single_action(self.master, 0, 1)
            except Exception as e:
                print(f"停止设备动作时出错: {str(e)}")
            
            # 等待剩余的异步处理任务完成并整合结果
            try:
                if hasattr(self, 'processing_tasks') and self.processing_tasks:
                    print(f"实验结束，等待剩余 {len(self.processing_tasks)} 个图片处理任务完成...")
                    completed_tasks = 0
                    failed_tasks = 0
                    
                    for i, task in enumerate(self.processing_tasks):
                        try:
                            # 减少超时时间，避免长时间等待
                            result = task.result(timeout=60)  # 1分钟超时
                            if result:
                                completed_tasks += 1
                                print(f"处理任务 {i+1} 完成: {os.path.basename(result) if result else 'Unknown'}")
                            else:
                                failed_tasks += 1
                                print(f"处理任务 {i+1} 失败")
                        except Exception as e:
                            failed_tasks += 1
                            print(f"等待处理任务 {i+1} 时出错: {str(e)}")
                    
                    print(f"图片处理任务完成统计: 成功 {completed_tasks}, 失败 {failed_tasks}")
                    self.processing_tasks.clear()
                
                # 在实验结束时整合所有结果
                print("实验完成，开始整合所有图片处理结果...")
                self._consolidate_processing_results()
                print("图片处理结果整合完成")
                
            except Exception as e:
                print(f"实验结束时处理异步任务和结果整合出错: {str(e)}")
                import traceback
                traceback.print_exc()

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
        """
        Closes all control systems and connections with proper cleanup.
        """
        try:
            # Close feeding control
            if hasattr(self, 'feeding_control') and self.feeding_control:
                try:
                    self.feeding_control.close()
                except Exception as e:
                    print(f"Error closing feeding control: {str(e)}")
                self.feeding_control = None
                time.sleep(0.5)

            # Close camera control
            if hasattr(self, 'camera_control') and self.camera_control:
                try:
                    self.camera_control.close()
                except Exception as e:
                    print(f"Error closing camera control: {str(e)}")
                self.camera_control = None
                time.sleep(0.5)

            # Close clean control
            if hasattr(self, 'clean_control') and self.clean_control:
                try:
                    self.clean_control.close()
                except Exception as e:
                    print(f"Error closing clean control: {str(e)}")
                self.clean_control = None
                time.sleep(0.5)

            print("All systems successfully closed")
            return True

        except Exception as e:
            print(f"Error during close operation: {str(e)}")
            return False

    def reinitialize(self):
        """
        Reinitializes all control systems and connections.
        Includes improved error handling and retry mechanism.
        """
        try:
            # First, ensure proper cleanup
            self.close()
            time.sleep(1)  # Allow time for resources to be released

            # Check if COM5 is available
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            if 'COM5' not in available_ports:
                # Try to force release COM5 if it's stuck
                subprocess.run(['powershell', '-Command', 
                    "Get-WmiObject Win32_Process | " + 
                    "Where-Object {$_.CommandLine -like '*COM5*'} | " + 
                    "ForEach-Object { $_.Terminate() }"], 
                    capture_output=True)
                time.sleep(2)  # Wait for port to be released

            # Initialize components with retries
            max_retries = 3
            retry_delay = 2

            for attempt in range(max_retries):
                try:
                    print(f"Initialization attempt {attempt + 1}/{max_retries}")
                    
                    # Initialize feeding control
                    self.feeding_control = FeedingControl()
                    time.sleep(0.5)

                    # Initialize camera control
                    self.camera_control = CameraControl()
                    time.sleep(0.5)

                    # Initialize clean control
                    self.clean_control = CleanControl()
                    time.sleep(0.5)

                    # Initialize peripheral components
                    self.reinit_peripheral()

                    print("All systems successfully reinitialized")
                    return True

                except Exception as e:
                    print(f"Initialization attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise Exception(f"Failed to reinitialize after {max_retries} attempts: {str(e)}")

        except Exception as e:
            print(f"Fatal error during reinitialization: {str(e)}")
            return False

    def _process_captured_images(self, captured_images, group_count, photo_count):
        """处理拍摄的图片（单张处理模式）"""
        if not captured_images:
            print(f"第 {group_count} 组第 {photo_count} 张: 没有图片需要处理")
            return
            
        print(f"第 {group_count} 组第 {photo_count} 张: 开始异步处理 {len(captured_images)} 张图片")
        
        # 为每张图片启动异步处理任务
        for image_path in captured_images:
            try:
                # 根据文件名判断图片类型
                filename = os.path.basename(image_path).lower()
                if 'global' in filename or '_g_' in filename or filename.startswith('g_'):
                    image_type = "global"
                elif 'local' in filename or '_l_' in filename or filename.startswith('l_'):
                    image_type = "local"
                else:
                    # 如果无法从文件名判断，则根据路径判断
                    if 'global' in image_path.lower():
                        image_type = "global"
                    elif 'local' in image_path.lower():
                        image_type = "local"
                    else:
                        print(f"警告: 无法确定图片类型，跳过处理: {image_path}")
                        continue
                
                # 检查图片文件是否存在
                if not os.path.exists(image_path):
                    print(f"警告: 图片文件不存在: {image_path}")
                    continue
                
                # 提交异步处理任务
                future = self.thread_pool.submit(self._async_process_single_image, image_path, image_type)
                self.processing_tasks.append(future)
                
                print(f"已提交异步处理任务: {image_path} (类型: {image_type})")
                
            except Exception as e:
                print(f"提交异步处理任务失败 {image_path}: {str(e)}")
                import traceback
                traceback.print_exc()
