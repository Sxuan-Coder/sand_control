"""
测试异步图片处理功能
"""
import os
import sys
import time
import shutil
from datetime import datetime

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from control.process_control import ProcessControl

def create_test_images():
    """创建测试图片目录和示例图片"""
    test_base_path = r"c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\test_images"
    
    # 创建测试目录
    global_path = os.path.join(test_base_path, "global")
    local_path = os.path.join(test_base_path, "local")
    
    os.makedirs(global_path, exist_ok=True)
    os.makedirs(local_path, exist_ok=True)
    
    # 检查是否有现有的图片可以复制作为测试
    source_global = r"c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\data\images\global"
    source_local = r"c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\data\images\local"
    
    # 如果存在源图片，复制几张作为测试
    if os.path.exists(source_global):
        print(f"从 {source_global} 复制测试图片")
        for i, file in enumerate(os.listdir(source_global)[:3]):  # 复制前3张
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                src = os.path.join(source_global, file)
                dst = os.path.join(global_path, f"test_global_{i+1}.jpg")
                shutil.copy2(src, dst)
                print(f"复制测试图片: {dst}")
    
    if os.path.exists(source_local):
        print(f"从 {source_local} 复制测试图片")
        for i, file in enumerate(os.listdir(source_local)[:3]):  # 复制前3张
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                src = os.path.join(source_local, file)
                dst = os.path.join(local_path, f"test_local_{i+1}.jpg")
                shutil.copy2(src, dst)
                print(f"复制测试图片: {dst}")
    
    return test_base_path

def test_async_processing():
    """测试异步处理功能"""
    try:
        print("=" * 50)
        print("开始测试异步图片处理功能")
        print("=" * 50)
        
        # 创建测试图片
        test_base_path = create_test_images()
        print(f"测试图片路径: {test_base_path}")
        
        # 直接测试异步处理函数
        print("\n开始测试异步图片处理...")
        start_time = time.time()
        
        # 手动实现异步处理逻辑
        from concurrent.futures import ThreadPoolExecutor
        import json
        
        def async_process_images(photo_paths, base_path):
            """异步处理图片的函数"""
            try:
                # 导入图片处理模块
                from process_sand_images import process_images_in_directory
                
                # 获取全局和局部图片目录
                global_path = os.path.join(base_path, "global")
                local_path = os.path.join(base_path, "local")
                
                results = {}
                
                # 处理全局图片
                if os.path.exists(global_path):
                    print(f"开始异步处理全局图片: {global_path}")
                    global_results = process_images_in_directory(global_path, "global")
                    results["global"] = global_results
                    print(f"全局图片处理完成，处理了 {len(global_results)} 张图片")
                else:
                    results["global"] = []
                    print(f"全局图片目录不存在: {global_path}")
                
                # 处理局部图片
                if os.path.exists(local_path):
                    print(f"开始异步处理局部图片: {local_path}")
                    local_results = process_images_in_directory(local_path, "local")
                    results["local"] = local_results
                    print(f"局部图片处理完成，处理了 {len(local_results)} 张图片")
                else:
                    results["local"] = []
                    print(f"局部图片目录不存在: {local_path}")
                
                # 保存单次处理结果
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_result_file = os.path.join(
                    r"C:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\results",
                    f"temp_processing_results_{timestamp}.json"
                )
                
                # 计算统计信息
                global_success = sum(1 for r in results["global"] if r.get("success", False))
                local_success = sum(1 for r in results["local"] if r.get("success", False))
                global_particles = sum(r.get("contours_count", 0) for r in results["global"] if r.get("success", False))
                local_particles = sum(r.get("contours_count", 0) for r in results["local"] if r.get("success", False))
                
                temp_results = {
                    "global": results["global"],
                    "local": results["local"],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "processing_id": timestamp,
                    "summaryStats": {
                        "global": {
                            "totalImages": len(results["global"]),
                            "successfulImages": global_success,
                            "totalParticles": global_particles
                        },
                        "local": {
                            "totalImages": len(results["local"]),
                            "successfulImages": local_success,
                            "totalParticles": local_particles
                        }
                    }
                }
                
                with open(temp_result_file, 'w', encoding='utf-8') as f:
                    json.dump(temp_results, f, indent=2, ensure_ascii=False)
                
                print(f"异步处理结果临时保存到: {temp_result_file}")
                return temp_result_file
                
            except Exception as e:
                print(f"异步图片处理出错: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
        
        def consolidate_processing_results():
            """整合所有处理结果"""
            try:
                results_dir = r"C:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\results"
                
                # 查找所有临时结果文件
                temp_files = [f for f in os.listdir(results_dir) if f.startswith("temp_processing_results_")]
                
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
                        
                        # 合并数据
                        consolidated_results["global"].extend(temp_data.get("global", []))
                        consolidated_results["local"].extend(temp_data.get("local", []))
                        
                        # 记录处理会话信息
                        session_info = {
                            "processing_id": temp_data.get("processing_id", "unknown"),
                            "timestamp": temp_data.get("timestamp", "unknown"),
                            "stats": temp_data.get("summaryStats", {})
                        }
                        consolidated_results["processing_sessions"].append(session_info)
                        
                        # 更新统计信息
                        if "summaryStats" in temp_data:
                            for image_type in ["global", "local"]:
                                if image_type in temp_data["summaryStats"]:
                                    stats = temp_data["summaryStats"][image_type]
                                    consolidated_results["summaryStats"][image_type]["totalImages"] += stats.get("totalImages", 0)
                                    consolidated_results["summaryStats"][image_type]["successfulImages"] += stats.get("successfulImages", 0)
                                    consolidated_results["summaryStats"][image_type]["totalParticles"] += stats.get("totalParticles", 0)
                        
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
        
        # 测试异步处理
        with ThreadPoolExecutor(max_workers=4) as executor:
            future = executor.submit(async_process_images, [], test_base_path)
            print("异步任务已提交，等待完成...")
            
            # 等待任务完成
            result = future.result(timeout=300)  # 5分钟超时
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"\n异步处理完成!")
            print(f"处理时间: {processing_time:.2f} 秒")
            print(f"结果文件: {result}")
        
        # 测试结果整合功能
        print("\n开始测试结果整合功能...")
        consolidate_processing_results()
        
        # 检查最终结果文件
        final_result_file = r"c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\results\processing_results.json"
        if os.path.exists(final_result_file):
            print(f"最终结果文件创建成功: {final_result_file}")
            
            # 读取并显示结果摘要
            with open(final_result_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            print(f"处理摘要:")
            print(f"- 全局图片: {results['summaryStats']['global']['totalImages']} 张")
            print(f"- 局部图片: {results['summaryStats']['local']['totalImages']} 张")
            print(f"- 成功处理: 全局 {results['summaryStats']['global']['successfulImages']}, 局部 {results['summaryStats']['local']['successfulImages']}")
            print(f"- 检测颗粒: 全局 {results['summaryStats']['global']['totalParticles']}, 局部 {results['summaryStats']['local']['totalParticles']}")
            
        else:
            print("警告: 最终结果文件未创建")
        
        print("\n" + "=" * 50)
        print("测试完成!")
        print("=" * 50)
        
    except Exception as e:
        print(f"测试出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_async_processing()
