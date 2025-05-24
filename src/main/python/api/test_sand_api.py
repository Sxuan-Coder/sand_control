"""
沙粒图像处理API测试脚本
"""
import requests
import json
import time
import os
import sys

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)  # python目录
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# API基础URL
API_BASE_URL = "http://localhost:8000"

def test_analyze_sand_data():
    """测试分析沙粒数据API"""
    print("\n--- 测试分析沙粒数据API ---")
    url = f"{API_BASE_URL}/api/sand/analyze"
    data = {
        "view": "local",
        "gradeNames": [0.075, 0.15, 0.3, 0.6, 1.18, 2.36],
        "gradeEnabled": [1, 1, 1, 1, 1, 1],
        "volume_corrections": [1, 1, 1, 1, 1, 1]
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print("API调用成功!")
            print(f"总粒子数: {result.get('total_particles', 0)}")
            print(f"MX值: {result.get('mx_value', 0)}")
            
            # 显示分布情况
            distribution = result.get('distribution', [])
            if distribution:
                print("\n粒径分布:")
                for item in distribution:
                    print(f"  {item['range']}: {item['percentage']:.2f}%, {item.get('count', 0)} 颗粒")
            
            return True
        else:
            print(f"API调用失败! 状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
    except Exception as e:
        print(f"API调用异常: {str(e)}")
        return False

def poll_task_status(task_id, max_attempts=30, interval=2):
    """轮询任务状态"""
    url = f"{API_BASE_URL}/api/sand/task-status/{task_id}"
    
    for i in range(max_attempts):
        try:
            response = requests.get(url)
            result = response.json()
            
            # 打印进度
            status = result.get("status", "unknown")
            progress = result.get("progress", 0)
            message = result.get("message", "")
            
            print(f"任务状态: {status}, 进度: {progress}%, 消息: {message}")
            
            if status in ["completed", "error"]:
                return result
                
            time.sleep(interval)
        except Exception as e:
            print(f"轮询任务状态出错: {str(e)}")
            time.sleep(interval)
    
    print("任务轮询超时!")
    return None

def find_image_files(directory, pattern="*.jpg", limit=3):
    """查找图像文件"""
    import glob
    files = glob.glob(os.path.join(directory, pattern))
    return files[:limit] if limit else files

def test_process_directory():
    """测试批量处理目录"""
    print("\n--- 测试批量处理目录API ---")
    
    # 获取示例图像目录
    # 这里假设有一个示例图像目录，如果没有，请修改为实际目录
    example_dir = os.path.join(backend_dir, "example_images")
    if not os.path.exists(example_dir):
        print(f"示例图像目录不存在: {example_dir}")
        print("请修改脚本中的路径或创建示例目录")
        return False
    
    url = f"{API_BASE_URL}/api/sand/process-directory"
    data = {
        "directory_path": example_dir,
        "image_type": "global",
        "sample_index": "0.3",
        "file_pattern": "*.jpg",
        "limit": 3,
        "save_results": True,
        "output_path": os.path.join(backend_dir, "result", "test_output")
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print("API调用成功!")
            
            task_id = result.get("task_id")
            print(f"任务ID: {task_id}")
            print(f"处理图像数: {result.get('image_count', 0)}")
            
            # 轮询任务状态
            final_status = poll_task_status(task_id)
            
            if final_status and final_status.get("status") == "completed":
                print("\n任务完成!")
                results = final_status.get("results", {})
                print(f"处理图像数: {results.get('processed_images', 0)}")
                print(f"成功处理数: {results.get('success_count', 0)}")
                print(f"总粒子数: {results.get('total_particles', 0)}")
                print(f"平均尺寸: {results.get('average_size', 0):.4f} mm")
                
                # 显示粒径统计
                grade_stats = results.get("grade_statistics", [])
                if grade_stats:
                    print("\n粒径统计:")
                    grade_names = ["0.075-0.15", "0.15-0.3", "0.3-0.6", "0.6-1.18", "1.18-2.36", "2.36-4.75"]
                    for i, stats in enumerate(grade_stats):
                        if i < len(grade_names):
                            print(f"  {grade_names[i]}: {stats.get('count', 0)} 颗粒, {stats.get('percentage', 0)*100:.2f}%")
                
                return True
            else:
                print("\n任务未完成或出错!")
                return False
        else:
            print(f"API调用失败! 状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
    except Exception as e:
        print(f"API调用异常: {str(e)}")
        return False

if __name__ == "__main__":
    print("===== 开始测试沙粒图像处理API =====")
    print(f"API基础URL: {API_BASE_URL}")
    
    # 测试分析沙粒数据
    test_analyze_sand_data()
    
    # 可以添加更多测试
    # test_process_directory()
    
    print("\n===== 测试完成 =====")
