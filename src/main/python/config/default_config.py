from  samples_labels import LABELS

# 像素到毫米的转换因子
global_mm_per_pixel = 0.0351  # 全局视图: 1像素 = 0.0351mm
local_mm_per_pixel = 0.00351  # 局部视图: 1像素 = 0.00351mm

# 通信配置
USRIO_PORT = 50007  # 有人设备端口号
WGD_PORT: int = 1000  # 振动盘端口号
WGD_IP = "192.168.1.88"
OUT_SAND = '00'  # 有人控制序号
BAMPER = '02'

# 振动盘动作寄存器地址
START = 1
STOP = 0
ACTONS_ADDR = 0
STORE = 1
BACK_LIGHT = 2
SINGLE_ACTION_ADDR = 4
SAVE_SINGLE_ACTION = 12
SAVE_ACTIONS = 13
SAVE_LIGHT = 14
SAVE_STORE = 15
SAVE_BALANCE = 19
UP_INTENSITY = 20
DOWN_INTENSITY = 21
LEFT_INTENSITY = 22
RIGHT_INTENSITY = 23
L_UP_INTENSITY = 24
L_DOWN_INTENSITY = 25
R_UP_INTENSITY = 26
R_DOWN_INTENSITY = 27
ACROSS_INTENSITY = 28

# 参与计算的区间， 0.075~0.15、 0.15~0.3、 0.3~0.6、 0.6~1.18、 1.18~2.36、 2.36~4.75
main_gradeEnabled = [1,1,1,1,1,1]

# 文本数据保存地址
main_data_path = r"H:\features"

# 背景模型路径
background_path = r"C:\Users\ASUS\Desktop\test"

# 输入图像路径
main_input_image_path = r"F:\\sand_data\\test"

# 结果保存路径
RESULTS_PATH = r"C:\Users\ASUS\Desktop\SandControl\results"

# 视图设置
main_view = 'global'

# 主分布列表 (从旧config.py合并)
main_distributions = []

if main_view == 'global':
    main_gradeEnabled[0] = 0
    main_gradeEnabled[1] = 0

# 类别名
main_gradeNames = [0.075, 0.15, 0.3, 0.6, 1.18, 2.36]

# 根据参与计算的区间动态计算占比
main_LABELS = [[a * b for a, b in zip(row, main_gradeEnabled)] for row in LABELS]
main_LABELS = [[a / sum(row) for a in row] for row in main_LABELS]

# 体积修正
main_volume_corrections = [1, 1, 1, 1, 1, 1]
VERTICAL_INTENSITY = 29
DISPERSE_INTENSITY = 30
ACTIONS_1 = 31
ACTIONS_2 = 32
ACTIONS_3 = 33
ACTIONS_4 = 34
ACTIONS_5 = 35
TIMES_1 = 36
TIMES_2 = 38
TIMES_3 = 40
TIMES_4 = 42
TIMES_5 = 44
BACK_LIGHT_INTENSITY = 46
STORE_INTENSITY = 48
STORE_TIMES = 49
UP_F = 60
DOWN_F = 61
LEFT_F = 62
RIGHT_F = 63
L_UP_F = 64
L_DOWN_F = 65
R_UP_F = 66
R_DOWN_F = 67
ACROSS_F = 68
VERTICAL_F = 69
DISPERSE_F = 70
STORE_F = 71
BALANCE_1 = 72
BALANCE_2 = 73
BALANCE_3 = 74
BALANCE_4 = 75

# 计算类型控制
mixture_sample_index = 5  # 0: 不含分割的文本特征, 1: 包含分割但有nan和inf, 2: len(contour)>5, 3: 两参数判断形状因子, 4: 优化形状因子
calculate_type = False  # True: 计算error误差, False: 计算累计筛余量

# 像素物理长度换算(单位毫米)
global_pixel_per_mm = 1/global_mm_per_pixel  # 全局横向 1mm = 28.44, 全局纵向 1mm = 28.25
local_pixel_per_mm = 1/local_mm_per_pixel    # 局部横向 1mm = 150, 局部纵向 1mm = 152

# 连接设置
to_link = False  # 局部是否结合全局

# 物理采样范围说明
# 全局物理采样范围: 3.8cm * 2.6cm
# 局部物理采样范围: 10.9cm * 7.5cm