#!/bin/bash

echo "================================"
echo "wasai 短剧出海剪辑工具启动脚本"
echo "================================"

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装后端依赖..."
pip install -r requirements.txt -q

# 启动后端服务
echo ""
echo "启动后端服务 (http://localhost:8000)..."
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 2

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

# 启动前端服务
echo ""
echo "启动前端服务 (http://localhost:5173)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "================================"
echo "服务已启动!"
echo "前端: http://localhost:5173"
echo "后端: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo "================================"
echo "按 Ctrl+C 停止所有服务"
echo ""

# 捕获 Ctrl+C 信号
trap "echo '停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# 等待
wait
