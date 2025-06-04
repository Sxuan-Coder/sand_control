"""
创建测试图片
"""
import os
import cv2
import numpy as np

def create_sample_images():
    """创建示例图片用于测试"""
    
    # 创建测试目录
    test_base_path = r"c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\test_images"
    global_path = os.path.join(test_base_path, "global")
    local_path = os.path.join(test_base_path, "local")
    
    os.makedirs(global_path, exist_ok=True)
    os.makedirs(local_path, exist_ok=True)
    
    # 创建简单的测试图片
    def create_test_image(width=640, height=480, num_circles=10):
        # 创建黑色背景
        img = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 添加一些白色圆形模拟沙粒
        for i in range(num_circles):
            center_x = np.random.randint(50, width - 50)
            center_y = np.random.randint(50, height - 50)
            radius = np.random.randint(5, 25)
            cv2.circle(img, (center_x, center_y), radius, (255, 255, 255), -1)
            
            # 添加一些随机噪声点
            for j in range(np.random.randint(5, 15)):
                noise_x = center_x + np.random.randint(-radius*2, radius*2)
                noise_y = center_y + np.random.randint(-radius*2, radius*2)
                if 0 <= noise_x < width and 0 <= noise_y < height:
                    cv2.circle(img, (noise_x, noise_y), np.random.randint(1, 3), (200, 200, 200), -1)
        
        return img
    
    # 创建全局图片
    for i in range(3):
        img = create_test_image(800, 600, 15)
        filename = os.path.join(global_path, f"test_global_{i+1}.png")
        cv2.imwrite(filename, img)
        print(f"创建测试图片: {filename}")
    
    # 创建局部图片
    for i in range(3):
        img = create_test_image(640, 480, 20)
        filename = os.path.join(local_path, f"test_local_{i+1}.png")
        cv2.imwrite(filename, img)
        print(f"创建测试图片: {filename}")
    
    print(f"测试图片创建完成，保存在: {test_base_path}")
    return test_base_path

if __name__ == "__main__":
    create_sample_images()
