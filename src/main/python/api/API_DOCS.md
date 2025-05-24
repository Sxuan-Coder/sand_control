# 沙粒图像处理API文档

## 概述

本文档描述了沙粒图像处理API的接口和使用方法。API用于处理沙粒图像，进行沙粒识别、分割，并提取信息。

## API基础URL

- 开发环境：`http://localhost:8000`
- 生产环境：与应用相同的域名

## 接口列表

### 1. 处理上传的沙粒图像

处理一个或多个上传的沙粒图像，进行沙粒识别和特征提取。

- **URL:** `/api/sand/process-images`
- **方法:** POST
- **Content-Type:** multipart/form-data
- **参数:**
  - `files`: 图像文件（可多个）
  - `image_type`: 图像类型，"global"或"local"
  - `sample_index`: 样本索引，如"0.075"、"0.15"等
  - `save_results`: 是否保存结果，布尔值，默认true
  - `output_path`: 输出路径（可选）

- **返回示例:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "沙粒图像处理任务已创建，正在后台处理",
  "status": "processing"
}
```

### 2. 检查任务状态

获取特定任务的处理状态和结果。

- **URL:** `/api/sand/task-status/{task_id}`
- **方法:** GET
- **参数:**
  - `task_id`: 任务ID（路径参数）

- **返回示例:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "message": "处理完成",
  "progress": 100,
  "start_time": 1625000000,
  "end_time": 1625000060,
  "results": {
    "processed_images": 5,
    "success_count": 5,
    "total_particles": 1250,
    "average_size": 0.32,
    "median_size": 0.29,
    "grade_statistics": [
      {"count": 200, "percentage": 0.16},
      {"count": 300, "percentage": 0.24},
      {"count": 350, "percentage": 0.28},
      {"count": 250, "percentage": 0.20},
      {"count": 100, "percentage": 0.08},
      {"count": 50, "percentage": 0.04}
    ],
    "timestamp": "2023-06-30 15:30:45"
  }
}
```

### 3. 批量处理目录

批量处理指定目录中的图像文件。

- **URL:** `/api/sand/process-directory`
- **方法:** POST
- **Content-Type:** application/json
- **请求体:**
```json
{
  "directory_path": "/path/to/images",
  "image_type": "global",
  "sample_index": "0.3",
  "file_pattern": "*.jpg",
  "limit": 10,
  "save_results": true,
  "output_path": "/path/to/output"
}
```

- **返回示例:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "批量处理任务已创建，正在后台处理",
  "status": "processing",
  "image_count": 10
}
```

### 4. 分析沙粒数据

分析已有的沙粒数据，计算分布和统计信息。

- **URL:** `/api/sand/analyze`
- **方法:** POST
- **Content-Type:** application/json
- **请求体:**
```json
{
  "view": "local",
  "gradeNames": [0.075, 0.15, 0.3, 0.6, 1.18, 2.36],
  "gradeEnabled": [1, 1, 1, 1, 1, 1],
  "volume_corrections": [1, 1, 1, 1, 1, 1]
}
```

- **返回示例:**
```json
{
  "view": "local",
  "gradeNames": [0.075, 0.15, 0.3, 0.6, 1.18, 2.36],
  "distribution": [
    {"range": "0.075-0.15", "percentage": 15.5, "count": 245},
    {"range": "0.15-0.3", "percentage": 25.2, "count": 320},
    {"range": "0.3-0.6", "percentage": 30.1, "count": 380},
    {"range": "0.6-1.18", "percentage": 18.3, "count": 220},
    {"range": "1.18-2.36", "percentage": 8.4, "count": 95},
    {"range": "2.36-4.75", "percentage": 2.5, "count": 30}
  ],
  "mx_value": 2.75,
  "total_particles": 1290,
  "distributions": [
    {"mean": 0.12, "std": 0.02},
    {"mean": 0.25, "std": 0.05},
    {"mean": 0.45, "std": 0.08},
    {"mean": 0.85, "std": 0.15},
    {"mean": 1.55, "std": 0.25},
    {"mean": 3.15, "std": 0.65}
  ],
  "analysis_time": "2023-06-30 15:35:30"
}
```

### 5. 精炼图像数据

处理并精炼已有的图像数据。

- **URL:** `/api/sand/refine-data`
- **方法:** POST
- **Content-Type:** multipart/form-data
- **参数:**
  - `input_path`: 输入数据路径
  - `output_path`: 输出数据路径
  - `step`: 处理步骤，默认1

- **返回示例:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "数据精炼任务已创建，正在后台执行",
  "status": "processing"
}
```

### 6. 绘制沙粒等级

根据图像绘制沙粒等级分布。

- **URL:** `/api/sand/draw-grades`
- **方法:** POST
- **Content-Type:** multipart/form-data
- **参数:**
  - `image_path`: 图像路径
  - `sample_index`: 样本索引
  - `is_global`: 是否全局视图，布尔值，默认true
  - `is_single`: 是否单级配样本，布尔值，默认true
  - `output_path`: 输出路径（可选）

- **返回示例:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "沙粒绘制任务已创建，正在后台执行",
  "status": "processing"
}
```

## 使用示例

### JavaScript (前端)

```javascript
// 导入API
import sandImageApi from '@/api/sandImageApi'

// 分析沙粒数据
async function analyzeSandData() {
  try {
    const result = await sandImageApi.analyzeSandData({
      view: 'local',
      gradeNames: [0.075, 0.15, 0.3, 0.6, 1.18, 2.36]
    })
    console.log('分析结果:', result)
  } catch (error) {
    console.error('分析失败:', error)
  }
}

// 上传并处理图像
async function processImages(files) {
  try {
    // 开始处理任务
    const response = await sandImageApi.uploadAndProcessImages(
      files, 
      'global', 
      '0.3'
    )
    
    // 获取任务ID
    const taskId = response.task_id
    
    // 等待任务完成
    const result = await sandImageApi.pollTaskUntilComplete(taskId)
    console.log('处理完成:', result)
  } catch (error) {
    console.error('处理失败:', error)
  }
}
```

### Python (后端测试)

```python
import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

# 分析沙粒数据
def analyze_sand_data():
    url = f"{API_BASE_URL}/api/sand/analyze"
    data = {
        "view": "local",
        "gradeNames": [0.075, 0.15, 0.3, 0.6, 1.18, 2.36],
        "gradeEnabled": [1, 1, 1, 1, 1, 1],
        "volume_corrections": [1, 1, 1, 1, 1, 1]
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 轮询任务状态
def poll_task_status(task_id, max_attempts=30, interval=2):
    url = f"{API_BASE_URL}/api/sand/task-status/{task_id}"
    
    for _ in range(max_attempts):
        response = requests.get(url)
        result = response.json()
        
        if result["status"] in ["completed", "error"]:
            return result
            
        time.sleep(interval)
    
    raise Exception("任务轮询超时")

# 测试
result = analyze_sand_data()
print(json.dumps(result, indent=2, ensure_ascii=False))
```
