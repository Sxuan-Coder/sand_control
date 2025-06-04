import ctypes
import os
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from ctypes import cast, memset, c_ubyte, memmove
from _ctypes import POINTER, byref, sizeof

import cv2
import numpy as np
from modbus_tk import modbus_tcp
from PIL import Image
from camera.MvImport.CameraParams_const import MV_GIGE_DEVICE, MV_USB_DEVICE, MV_ACCESS_Exclusive
from camera.MvImport.CameraParams_header import MV_CC_DEVICE_INFO_LIST, MV_CC_DEVICE_INFO, MV_FRAME_OUT
from camera.MvImport.MvCameraControl_class import MvCamera
from config.default_config import WGD_IP, WGD_PORT
from utils.modbus_utils import triggle_single_action, stop_single_action


# 直接从Camera.MvImport导入，这里假设您已经将相机SDK文件迁移到相应位置
class CameraControl:
    def __init__(self):
        """初始化相机控制类"""
        self.master = modbus_tcp.TcpMaster(host=WGD_IP, port=WGD_PORT)
        self.cameras = []
        self.b_is_open = False
        self.b_is_grab = False
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.image_queues = [queue.Queue() for _ in range(2)]  # 为每个相机创建一个队列
        self.is_running = True
        self.save_threads = []
        self.tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        self.deviceList = MV_CC_DEVICE_INFO_LIST()
        self._enum_devices()
        self._open_devices()

        # 启动保存工作线程
        for i in range(len(self.cameras)):
            save_thread = threading.Thread(target=self._save_worker, args=(i,))
            save_thread.daemon = True
            save_thread.start()
            self.save_threads.append(save_thread)

    def initialize(self):
        """初始化相机"""
        try:
            # 设置Modbus连接
            if not self.master:
                self.master = modbus_tcp.TcpMaster(host=WGD_IP, port=WGD_PORT)
                
            # 枚举并打开设备
            self._enum_devices()
            self._open_devices()
            
            # 启动保存工作线程
            for i in range(len(self.cameras)):
                save_thread = threading.Thread(target=self._save_worker, args=(i,))
                save_thread.daemon = True
                save_thread.start()
                self.save_threads.append(save_thread)
                
            return True
        except Exception as e:
            print(f"相机初始化失败: {str(e)}")
            return False

    # 枚举设备
    def _enum_devices(self):
        """枚举可用的相机设备"""
        ret = MvCamera.MV_CC_EnumDevices(self.tlayerType, self.deviceList)
        if ret != 0:
            raise Exception("枚举设备失败! ret[0x%x]" % ret)

        if self.deviceList.nDeviceNum == 0:
            raise Exception("未找到设备!")

        print("找到 %d 个设备!" % self.deviceList.nDeviceNum)
        for i in range(0, self.deviceList.nDeviceNum):
            mvcc_dev_info = cast(self.deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                print("\nGigE设备: [%d]" % i)
                model_name = self._decoding_char(mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName)
                print("设备型号名: %s" % model_name)
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                print("\nUSB设备: [%d]" % i)
                model_name = self._decoding_char(mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName)
                print("设备型号名: %s" % model_name)

    @staticmethod
    def _decoding_char(c_ubyte_value):
        """解码字符"""
        c_char_p_value = ctypes.cast(c_ubyte_value, ctypes.c_char_p)
        try:
            decode_str = c_char_p_value.value.decode('gbk')
        except UnicodeDecodeError:
            decode_str = str(c_char_p_value.value)
        return decode_str

    # 打开设备
    def _open_devices(self):
        """打开相机设备"""
        if self.b_is_open:
            return

        for i in range(0, self.deviceList.nDeviceNum):
            cam = MvCamera()
            stDeviceList = cast(self.deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents

            ret = cam.MV_CC_CreateHandle(stDeviceList)
            if ret != 0:
                print("创建句柄失败! ret[0x%x]" % ret)
                continue

            ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
            if ret != 0:
                print("打开设备失败! ret[0x%x]" % ret)
                cam.MV_CC_DestroyHandle()
                continue

            # 设置曝光时间（单位：微秒）
            ret = cam.MV_CC_SetFloatValue("ExposureTime", 3000.0)  # 可以根据需要调整这个值
            if ret != 0:
                print("设置曝光时间失败! ret[0x%x]" % ret)
            
            # 设置增益
            ret = cam.MV_CC_SetFloatValue("Gain", 0.0)  # 可以根据需要调整这个值（范围通常是0-15）
            if ret != 0:
                print("设置增益失败! ret[0x%x]" % ret)

            self.cameras.append(cam)
            print("相机 %d 打开成功!" % i)

        self.b_is_open = True if self.cameras else False

    # 捕获图像
    def capture_images(self, base_path, count):
        """捕获图像并保存，返回拍摄的图片路径列表"""
        try:
            # 确保目录存在
            for folder_name in ["global", "local"]:
                save_dir = f"{base_path}/{folder_name}"
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

            # 开始抓取图像
            self.start_grabbing()

            # 创建同步事件，确保两个相机同时拍摄
            sync_event = threading.Event()
            
            futures = []
            captured_image_paths = []
            
            # 获取图像数据并提交到线程池，确保同步拍摄
            def prepare_capture(cam_index):
                nonlocal sync_event
                # 等待同步事件，确保所有相机线程准备就绪
                sync_event.wait()
                # 开始捕获
                self._capture_single_camera(cam_index, self.cameras[cam_index], base_path, count)
                
                # 构建图片路径
                folder_name = "global" if cam_index == 1 else "local"  # 修复local和global的对应关系
                image_path = f"{base_path}/{folder_name}/{count}.jpg"
                return image_path
            
            # 提交所有捕获任务到线程池
            for i in range(len(self.cameras)):
                future = self.thread_pool.submit(prepare_capture, i)
                futures.append(future)
            
            # 设置同步事件，触发所有相机同时开始捕获
            sync_event.set()
            
            # 等待所有捕获操作完成并收集图片路径
            for future in futures:
                image_path = future.result()
                if image_path:
                    captured_image_paths.append(image_path)

            # 等待图片保存完成（给保存线程一些时间）
            time.sleep(0.8)
            
            # 返回实际存在的图片路径
            existing_paths = []
            for path in captured_image_paths:
                if os.path.exists(path):
                    existing_paths.append(path)
                else:
                    print(f"警告：图片文件不存在: {path}")
            
            return existing_paths if existing_paths else None

        except Exception as e:
            print(f"图像捕获失败: {str(e)}")
            return None

    def _capture_single_camera(self, cam_index, cam, base_path, count):
        """处理单个相机的图像捕获"""
        try:
            stOutFrame = MV_FRAME_OUT()
            memset(byref(stOutFrame), 0, sizeof(stOutFrame))

            ret = cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
            if ret != 0:
                print(f"相机 {cam_index} 获取图像缓冲失败! ret[0x%x]" % ret)
                return

            # 创建图像数据的深拷贝
            frame_data = (c_ubyte * stOutFrame.stFrameInfo.nFrameLen)()
            memmove(frame_data, cast(stOutFrame.pBufAddr, POINTER(c_ubyte)), stOutFrame.stFrameInfo.nFrameLen)
            
            # 将图像数据转换为numpy数组并进行处理
            image = np.asarray(frame_data)
            image = image.reshape((stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nWidth, 1))
            image = cv2.cvtColor(image, cv2.COLOR_BAYER_GB2BGR)  # Bayer格式转换为BGR
            
            # 立即释放原始图像缓冲
            cam.MV_CC_FreeImageBuffer(stOutFrame)

            # 将处理后的图像数据放入队列
            self.image_queues[cam_index].put((image, stOutFrame.stFrameInfo, base_path, count))

        except Exception as e:
            print(f"相机 {cam_index} 捕获图像时出错: {str(e)}")

    def _save_worker(self, cam_index):
        """处理图像保存的工作线程"""
        while self.is_running:
            try:
                # 从队列获取图像数据，设置超时以避免一直阻塞
                save_data = self.image_queues[cam_index].get(timeout=1)
                if save_data is None:
                    continue
                
                image, frame_info, base_path, count = save_data
                
                try:
                    # 根据相机索引选择不同的文件夹名称
                    folder_name = "global" if cam_index == 1 else "local"  # 修复local和global的对应关系
                    file_path = f"{base_path}/{folder_name}/{count}"
                    
                    # 确保目录存在
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # OpenCV使用BGR格式，需要转换为RGB
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    
                    # 使用Pillow进行高效压缩和保存
                    pil_image = Image.fromarray(rgb_image)
                    # 使用优化的JPEG压缩设置
                    pil_image.save(
                        file_path + ".jpg",
                        "JPEG",
                        quality=85,  # 较好的质量与压缩比平衡
                        optimize=True,  # 启用优化
                        subsampling=0  # 更好的色彩质量
                    )
                    
                    print(f"相机 {cam_index} 图像已保存到 {file_path}.jpg")
                    
                except Exception as e:
                    print(f"相机 {cam_index} 保存图像时出错: {str(e)}")
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"保存工作线程 {cam_index} 发生错误: {str(e)}")

    # 抓取图像
    def start_grabbing(self):
        """开始抓取图像"""
        if not self.b_is_open or self.b_is_grab:
            return

        def grab_camera(cam, i):
            ret = cam.MV_CC_StartGrabbing()
            if ret != 0:
                print("相机 %d 开始抓取失败! ret[0x%x]" % (i, ret))
            else:
                self.b_is_grab = True
                print("相机 %d 开始抓取!" % i)

        threads = []
        for i, cam in enumerate(self.cameras):
            thread = threading.Thread(target=grab_camera, args=(cam, i))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    # 停止抓取图像
    def stop_grabbing(self):
        """停止抓取图像"""
        if not self.b_is_open or not self.b_is_grab:
            return

        for i, cam in enumerate(self.cameras):
            ret = cam.MV_CC_StopGrabbing()
            if ret != 0:
                print("相机 %d 停止抓取失败! ret[0x%x]" % (i, ret))
            else:
                self.b_is_grab = False
                print("相机 %d 停止抓取!" % i)

    # 关闭系统资源
    def close(self):
        """关闭系统资源"""
        try:
            self.is_running = False
            if hasattr(self, 'save_threads'):
                for thread in self.save_threads:
                    if thread.is_alive():
                        thread.join(timeout=1)

            if hasattr(self, 'cameras'):
                # 停止抓取
                self.stop_grabbing()
                
                # 关闭设备
                for i, cam in enumerate(self.cameras):
                    ret = cam.MV_CC_CloseDevice()
                    if ret != 0:
                        print("相机 %d 关闭设备失败! ret[0x%x]" % (i, ret))
                    
                    ret = cam.MV_CC_DestroyHandle()
                    if ret != 0:
                        print("相机 %d 销毁句柄失败! ret[0x%x]" % (i, ret))
                
                self.cameras = []
                self.b_is_open = False
                
            if hasattr(self, 'thread_pool'):
                self.thread_pool.shutdown()
                
            print("相机资源已释放")
        except Exception as e:
            print(f"关闭相机资源时出错: {str(e)}")