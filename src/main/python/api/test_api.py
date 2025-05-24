from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import random
import uvicorn

# 创建FastAPI应用
app = FastAPI(
    title="测试API",
    description="沙粒控制系统的测试API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义请求和响应模型
class TestRequest(BaseModel):
    name: str
    value: Optional[float] = None

class TestResponse(BaseModel):
    message: str
    timestamp: str
    data: dict

# 模拟数据
mock_data = {
    "temperature": 25.5,
    "humidity": 60.2,
    "pressure": 1013.25,
    "status": "正常"
}

# API根端点
@app.get("/")
def root():
    """API根端点"""
    return {"message": "测试API服务器正在运行"}

# 测试GET接口
@app.get("/api/test", response_model=TestResponse)
def test_get():
    """简单的GET测试接口"""
    return {
        "message": "GET请求成功",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": mock_data
    }

# 测试带参数的GET接口
@app.get("/api/test/{item_id}")
def test_get_with_param(item_id: int, query: Optional[str] = None):
    """带路径参数和查询参数的GET测试接口"""
    return {
        "message": "带参数的GET请求成功",
        "item_id": item_id,
        "query": query,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# 测试POST接口
@app.post("/api/test", response_model=TestResponse)
def test_post(request: TestRequest):
    """POST测试接口"""
    return {
        "message": f"POST请求成功，收到名称: {request.name}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": {
            "name": request.name,
            "value": request.value,
            "random": random.random()
        }
    }

# 测试错误处理
@app.get("/api/error")
def test_error(code: int = 400):
    """测试错误响应"""
    error_messages = {
        400: "错误的请求",
        401: "未授权",
        403: "禁止访问",
        404: "资源不存在",
        500: "服务器内部错误"
    }
    
    message = error_messages.get(code, "未知错误")
    raise HTTPException(status_code=code, detail=message)

# 模拟长时间运行的任务
@app.get("/api/long-task")
async def long_task():
    """模拟长时间运行的任务"""
    import asyncio
    await asyncio.sleep(2)  # 模拟2秒延迟
    return {
        "message": "长时间任务完成",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# 健康检查接口
@app.get("/health")
def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import sys
    
    # 确保中文输出正常显示
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    print("启动测试API服务器，地址: 0.0.0.0:8001")
    print("使用Ctrl+C停止服务器")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
