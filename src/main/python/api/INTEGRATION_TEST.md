# 沙粒图像处理API与前端集成测试指南

本文档提供了测试沙粒图像处理API与前端集成的步骤。

## 后端API启动

### 方法1: 使用批处理脚本启动

双击运行 `start_api.bat` 文件。该脚本会自动启动API服务器。

### 方法2: 使用命令行启动

打开命令行窗口，导航到API目录并运行以下命令：

```powershell
cd c:\Users\ASUS\Desktop\SandControl\sand-nb-master\src\main\python\api
python app.py
```

### 方法3: 通过Electron应用启动

启动Electron应用，它会自动启动后端API服务器。

## 前端测试

前端调用API的路径已经设置为 `/api/sand/*` 格式。请确保后端API服务器正确挂载在 `/api` 路径下。

1. 启动前端开发服务器或Electron应用
2. 导航到数据报表页面
3. 点击"刷新数据"按钮，这将调用 `loadRealData()` 方法
4. 观察API调用是否成功并返回数据

## API路径修正

以下是API路径修正的摘要：

1. 在主应用 `app.py` 中，沙粒图像API被挂载到 `/api` 路径：
   ```python
   app.mount("/api", sand_image_app)
   ```

2. 在沙粒图像API `sand_image_api.py` 中，路由定义去掉了重复的 `/api` 前缀：
   ```python
   @app.post("/sand/process-images")
   @app.get("/sand/task-status/{task_id}")
   @app.post("/sand/process-directory")
   @app.post("/sand/refine-data")
   @app.post("/sand/draw-grades")
   @app.post("/sand/analyze")
   ```

3. 前端API调用路径保持不变，已配置为 `/api/sand/*` 格式

## 故障排除

如果在测试过程中遇到问题，请检查：

1. API服务器是否正常启动（查看控制台输出）
2. 前端API调用是否成功（查看浏览器开发者工具中的网络请求）
3. API路径是否正确配置（检查路由定义和挂载点）
4. CORS设置是否正确（确保API允许跨域请求）

## 测试API端点

您可以使用以下URL测试API端点是否可用：

- 分析沙粒数据: http://localhost:8000/api/sand/analyze
- 任务状态: http://localhost:8000/api/sand/task-status/{task_id}
- 处理目录: http://localhost:8000/api/sand/process-directory
- 绘制沙粒等级: http://localhost:8000/api/sand/draw-grades

使用Postman或curl等工具发送POST请求进行测试。
