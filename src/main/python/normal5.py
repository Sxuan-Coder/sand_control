import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.optimize import minimize
from scipy.optimize import fsolve

def plot_normal_distributions(distributions,volume_percentages=None,show_figure=False, return_curve_data=False):
    # 创建图形
    if show_figure:
        plt.figure(figsize=(12, 6))        # 存储交叉点
    intersection_points = []
    intersection_cdf_values = []
    
    # 如果需要返回曲线数据，则创建一个列表用于存储
    curve_data = [] if return_curve_data else None
    
    for i, (mean1, std_dev1,cout) in enumerate(distributions[:-1]):
        mean2, std_dev2,cout = distributions[i + 1]
        volume_ratio = 1
        if volume_percentages is not None:
            volume_ratio = volume_percentages[i]/ volume_percentages[i + 1]
 
        # 生成数据点 - 增加采样点数量以提高曲线精度
        x = np.linspace(min(mean1 - 4*std_dev1, mean2 - 4*std_dev2), max(mean1 + 4*std_dev1, mean2 + 4*std_dev2), 2000)
        
        # 计算两个正态分布的概率密度
        y_pdf1 = (1 / (std_dev1 * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean1) / std_dev1) ** 2)
        y_pdf2 = (1 / (std_dev2 * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean2) / std_dev2) ** 2)
        
        # 数据归一化
        y_pdf1 = y_pdf1 / np.max(y_pdf1)
        y_pdf2 = y_pdf2 / np.max(y_pdf2)
        
        # 如果需要返回曲线数据，收集数据点
        if return_curve_data:
            if i == 0:  # 添加第一条曲线的数据
                # Normalize the values for better visualization
                max_pdf1 = max(y_pdf1)
                normalized_y_pdf1 = [y / max_pdf1 for y in y_pdf1]
                
                # Filter out negative or very small x values
                filtered_points1 = []
                for xx, yy in zip(x, normalized_y_pdf1):
                    # 更严格的数据过滤
                    if xx >= 0 and yy >= 0.001:  # 降低阈值到0.1%以保留更多细节
                        # 数据归一化到[0,1]范围
                        filtered_points1.append({
                            "size": float(xx), 
                            "percentage": float(yy)
                        })
                
                curve_data.append({
                    "group_id": i + 1,
                    "mean": float(mean1),
                    "std": float(std_dev1),
                    "points": filtered_points1
                })
            
            # 添加第二条曲线的数据
            max_pdf2 = max(y_pdf2)
            normalized_y_pdf2 = [y / max_pdf2 for y in y_pdf2]
            
            # Filter out negative or very small x values
            filtered_points2 = []
            for xx, yy in zip(x, normalized_y_pdf2):
                # 对第二条曲线应用相同的过滤和归一化
                if xx >= 0 and yy >= 0.001:  # 保持与第一条曲线相同的阈值
                    filtered_points2.append({
                        "size": float(xx), 
                        "percentage": float(yy)
                    })
                    
            curve_data.append({
                "group_id": i + 2,
                "mean": float(mean2),
                "std": float(std_dev2),
                "points": filtered_points2
            })
        
        if show_figure:
            # 绘制概率密度函数 (PDF)，使用更好的视觉样式
            plt.plot(x, y_pdf1, label=f'分布 {i+1}\nMean: {mean1:.2f}\nStd Dev: {std_dev1:.2f}', 
                    linestyle='-', alpha=0.8, linewidth=2)
            plt.plot(x, y_pdf2, label=f'分布 {i+2}\nMean: {mean2:.2f}\nStd Dev: {std_dev2:.2f}', 
                    linestyle='-', alpha=0.8, linewidth=2)
            
        # 定义两个PDF相等的函数
        def pdf_equal(x):
            return (1 / (std_dev1 * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean1) / std_dev1) ** 2) - \
                   (1 / (std_dev2 * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean2) / std_dev2) ** 2)
        
        # 使用fsolve找到交叉点
        initial_guess = (mean1 + mean2) / 2
        intersection = fsolve(pdf_equal, initial_guess)
        intersection_points.append(intersection[0])

        
        
        # 计算交叉点处的累计值
        left_right_cdf = 1 - norm.cdf(intersection, mean1, std_dev1)
        right_left_cdf = norm.cdf(intersection, mean2, std_dev2)
        intersection_cdf_values.append({
            'intersection': intersection[0],
            'left_right_cdf': left_right_cdf[0],
            'right_left_cdf': right_left_cdf[0]
        })
        
        if show_figure:
            # 增强交叉点的可视化效果
            intersection_y = y_pdf1[np.argmin(np.abs(x - intersection))]
            plt.scatter(intersection, intersection_y, color='red', s=100, zorder=5, alpha=0.7)
            
            # 添加交叉点标注
            plt.annotate(
                f'交叉点: {intersection[0]:.1f}μm',
                xy=(intersection, intersection_y),
                xytext=(10, 10),
                textcoords='offset points',
                ha='left',
                va='bottom',
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.3),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            
            # 在交叉点处画一条竖线
            plt.axvline(x=intersection[0], color='g', linestyle='--', label=f'Intersection Point: {intersection[0]:.2f}')
        
    # 对每个分布的均值的左右一个标准差处画竖线，并输出这些点的CDF值
    for i, (mean, std_dev,cout) in enumerate(distributions):
        # 左侧一个标准差
        left_point = mean - std_dev
        left_cdf = norm.cdf(left_point, mean, std_dev)
        
        # 右侧一个标准差
        right_point = mean + std_dev
        right_cdf = norm.cdf(right_point, mean, std_dev)
        
        if show_figure:
            # 画竖线
            plt.axvline(x=left_point, color='b', linestyle='--', label=f'Mean - Std Dev: {left_point:.2f}')
            plt.axvline(x=right_point, color='r', linestyle='--', label=f'Mean + Std Dev: {right_point:.2f}')
            
        # 打印这些点的CDF值
        print(f"Distribution {i}:")
        print(f"Mean - Std Dev: {left_point:.2f}, CDF: {left_cdf:.4f}")
        print(f"Mean + Std Dev: {right_point:.2f}, CDF: {right_cdf:.4f}")
    if show_figure:
        plt.title('沙粒尺寸分布曲线（带交叉点和标准差范围）')
        plt.xlabel('粒径大小 (μm)')
        plt.ylabel('归一化密度')
        plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()  # 自动调整布局
        plt.show()
    
    # 打印交叉点及其累计值
    for i, data in enumerate(intersection_cdf_values):
        print(f"Intersection point between distribution {i} and {i+1}: {data['intersection']:.2f}")
        print(f"Right CDF of left distribution at intersection point: {data['left_right_cdf']:.4f}")
        print(f"Left CDF of right distribution at intersection point: {data['right_left_cdf']:.4f}")
    
    if return_curve_data:
        return intersection_cdf_values, curve_data
    else:
        return intersection_cdf_values

def plot_histogram(data, distributions, bins=100, title="沙粒尺寸分布直方图"):
    """
    绘制数据的直方图和对应的正态分布曲线
    
    Args:
        data: 原始数据列表
        distributions: 分布参数列表 [[mean1, std1, count1], [mean2, std2, count2], ...]
        bins: 直方图的区间数量
        title: 图表标题
    """
    plt.figure(figsize=(12, 6))
    
    # 计算整体数据范围
    all_data = []
    for d in data:
        all_data.extend(d)
    min_val = min(all_data)
    max_val = max(all_data)
    
    # 绘制直方图
    plt.hist(all_data, bins=bins, density=True, alpha=0.5, color='gray', 
             label='实际数据分布', edgecolor='black', linewidth=0.5)
    
    # 为每个分布绘制正态分布曲线
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'brown']
    x = np.linspace(min_val, max_val, 2000)
    
    for i, (mean, std_dev, count) in enumerate(distributions):
        y_pdf = (1 / (std_dev * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / std_dev) ** 2)
        plt.plot(x, y_pdf, 
                color=colors[i % len(colors)], 
                linestyle='-', 
                linewidth=2,
                alpha=0.8,
                label=f'分布 {i+1}\nμ={mean:.1f}\nσ={std_dev:.1f}\nn={count}')
    
    plt.title(title, fontsize=12, pad=20)
    plt.xlabel('粒径大小 (μm)', fontsize=10)
    plt.ylabel('归一化密度', fontsize=10)
    plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    # 示例使用
    distributions = [
        [16.415, 4.6175, 10000],
        [30.27, 5.3100, 8000],
        [63.785, 14.09535, 6000],
        [119.520, 26.76924, 4000],
        [230.44, 42.5178, 2000],
        [410.355, 68.9563, 1000]
    ]

    plot_normal_distributions(distributions)