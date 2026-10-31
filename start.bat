@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ==========================================
echo   校厕通 · 校园厕所智能管家
echo ==========================================

where python >nul 2>nul
if errorlevel 1 (
  echo [错误] 未检测到 python 命令，请先安装 Python 3.11+ 并加入 PATH。
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [错误] 未检测到 npm 命令，请先安装 Node.js 18+。
  pause
  exit /b 1
)

if not exist "backend\.venv\Scripts\python.exe" (
  echo [1/4] 创建后端虚拟环境并安装依赖，首次可能需要几分钟...
  python -m venv backend\.venv
  if errorlevel 1 goto :error
  backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
  if errorlevel 1 goto :error
) else (
  echo [1/4] 后端虚拟环境已存在，跳过安装。
)

if not exist "backend\cct.db" (
  echo [2/4] 初始化数据库并生成演示数据...
  backend\.venv\Scripts\python.exe backend\scripts\init_db.py --reset
  if errorlevel 1 goto :error
  backend\.venv\Scripts\python.exe backend\scripts\seed_demo.py --force
  if errorlevel 1 goto :error
) else (
  echo [2/4] 检测到已有数据库，保留现有数据。
)

if not exist "frontend\node_modules\vite" (
  echo [3/4] 安装前端依赖...
  pushd frontend
  call npm install
  if errorlevel 1 goto :error
  popd
) else (
  echo [3/4] 前端依赖已存在，跳过安装。
)

echo [4/4] 启动后端与前端...
start "校厕通-后端" /D "%~dp0backend" cmd /k ".venv\Scripts\python.exe run.py"
start "校厕通-前端" /D "%~dp0frontend" cmd /k "npm run dev"

echo.
echo 后端地址：http://localhost:8000
echo 接口文档：http://localhost:8000/docs
echo 前端地址：http://localhost:5173
echo.
echo 演示账号：admin / 123456   学生 2023101 / 123456   员工 staff001 / 123456
echo 关闭对应的命令窗口即可停止服务。
echo.

timeout /t 6 >nul
start "" http://localhost:5173
exit /b 0

:error
echo.
echo [失败] 启动过程中出现错误，请检查上方的提示信息。
pause
exit /b 1