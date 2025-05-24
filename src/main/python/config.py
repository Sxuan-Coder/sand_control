from  samples_labels import LABELS

# 像素到毫米的转换因子
global_mm_per_pixel = 0.0351  # 全局视图: 1像素 = 0.0351mm
local_mm_per_pixel = 0.00351  # 局部视图: 1像素 = 0.00351mm

# 参与计算的区间， 0.075~0.15、 0.15~0.3、 0.3~0.6、 0.6~1.18、 1.18~2.36、 2.36~4.75
main_gradeEnabled = [1,1,1,1,1,1]

# 文本数据保存地址
main_data_path = r"H:\features"
# main_data_path = r"F:\University\Laboratory\projects\sand_grading\calculate_sand_zsh_last\data\new_text_data"

# 背景模型路径
background_path = r"C:\Users\ASUS\Desktop\test"
# 输入图像路径
main_input_image_path = r"F:\sand_data\test"

main_view = 'global'
# main_distributions = calculate_mean_and_variance_origin()

main_distributions = []
# intersection_cdf_values = normal5.plot_normal_distributions(main_distributions,None,True)

if main_view == 'global':
    main_gradeEnabled[0] = 0
    main_gradeEnabled[1] = 0
# 类别名
main_gradeNames = [0.075, 0.15, 0.3, 0.6, 1.18, 2.36]

# 根据参与计算的区间动态计算占比
main_LABELS = [[a * b for a, b in zip(row, main_gradeEnabled)] for row in LABELS]
main_LABELS = [[a / sum(row) for a in row] for row in main_LABELS]

# 修正体积占比
# main_volume_corrections = [1.25, 1.4, 1.1, 1, 0.92, 0.80]
main_volume_corrections = [1, 1, 1, 1, 1, 1]
# main_volume_corrections = [1, 1, 1.1, 1, 0.92, 0.80]
# 动态修正
# volume_corrections = [a * b for a, b in zip(volume_corrections, gradeEnabled)]



# 一像素等于多少物理长度(单位毫米)
global_mm_per_pixel = 0.0351   # 全局横向 1mm = 28.44   1像素 = 0.0351mm    全局纵向 1mm = 28.25   1像素 = 0.0354
local_mm_per_pixel = 0.0066    # 局部横向 1mm = 150     1像素 = 0.0066mm    局部纵向 1mm = 152     1像素 = 0.0066

global_pixel_per_mm = 1/global_mm_per_pixel
local_pixel_per_mm = 1/local_mm_per_pixel
# 全局物理采样范围3.8cm * 2.6cm
# 局部物理采样范围10.9cm * 7.5cm


# 局部是否结合全局
to_link = False

# 采用什么样本计算
mixture_sample_index = 5
# 0 是不含分割的文本特征
# 1 包含分割，但是样本中出现了nan和inf以及e-的情况
# 2 处理了1的问题，把len(contour)的判断条件改为了>5
# 3 用两个参数来判断形状因子
# 4 在3的基础上继续对形状因子进行优化处理，分割效果在0~4中最好


# True 表示计算error误差，False表示计算累计筛余量
calculate_type = False


