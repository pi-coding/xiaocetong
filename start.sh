#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[错误] 未检测到 python3，请先安装 Python 3.11+"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[错误] 未检测到 npm，请先安装 Node.js 18+"
  exit 1
fi

if [ ! -x backend/.venv/bin/python ]; then
  echo "[1/4] 创建后端虚拟环境并安装依赖..."
  python3 -m venv backend/.venv
  backend/.venv/bin/python -m pip install -r backend/requirements.txt
else
  echo "[1/4] 后端虚拟环境已存在，跳过安装。"
fi

if [ ! -f backend/cct.db ]; then
  echo "[2/4] 初始化数据库并生成演示数据..."
  backend/.venv/bin/python backend/scripts/init_db.py --reset
  backend/.venv/bin/python backend/scripts/seed_demo.py --force
else
  echo "[2/4] 检测到已有数据库，保留现有数据。"
fi

if [ ! -d frontend/node_modules/vite ]; then
  echo "[3/4] 安装前端依赖..."
  (cd frontend && npm install)
else
  echo "[3/4] 前端依赖已存在，跳过安装。"
fi

echo "[4/4] 启动后端与前端..."
(cd backend && .venv/bin/python run.py) &
BACKEND_PID=$!
(cd frontend && npm run dev) &
FRONTEND_PID=$!

trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' INT TERM

echo
echo "后端：http://localhost:8000"
echo "接口文档：http://localhost:8000/docs"
echo "前端：http://localhost:5173"
echo "演示账号：admin / 123456  学生 2023101 / 123456  员工 staff001 / 123456"
echo "按 Ctrl+C 停止服务。"
echo

wait