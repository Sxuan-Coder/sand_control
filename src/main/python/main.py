import time
import sys
import os

from control.process_control import ProcessControl


def main():
    """主入口函数"""
    process = None
    try:
        # 创建流程控制实例
        process = ProcessControl()
        
        # 设置参数
        base_path = r"F:\sand_data\test\SAND_2.36"  # 保存图片的基础路径，根据需要修改
        sand_total = 7  # 总共要下料的克数
        once_count = 7  # 每次下料的克数
        start_group = 1  # 设置起始组号，可以根据需要修改

        # 执行流程
        process.execute_process(base_path, sand_total, once_count, start_group)
        
        # 流程执行完成后等待一段时间
        time.sleep(30)

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
    finally:
        # 确保所有资源都被正确关闭
        if process:
            process.close()

if __name__ == "__main__":
    """程序入口"""
    # 记录开始时间
    start_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"流程控制程序启动... 开始时间: {start_time}")
    
    try:
        main()
    finally:
        # 记录结束时间
        end_time = time.strftime("%Y-%m-%d %H:%M:%S")
        # 计算运行时长
        duration = time.time() - time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M:%S"))
        print(f"\n程序结束时间: {end_time}")
        print(f"总运行时长: {duration:.2f} 秒 ({duration/3600:.2f} 小时)") 