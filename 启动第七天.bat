@echo off
chcp 65001 >nul
title 封印之殿 · 《第七天》 2D 叙事 Demo
cd /d "%~dp0game-prototypes\2d-narrative-demo"

REM --- 杀掉正在占用 8890 端口的旧进程，避免 EADDRINUSE ---
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8890 " ^| findstr "LISTENING"') do (
  echo [0/3] 关闭旧服务器进程 PID %%a ...
  taskkill /f /pid %%a >nul 2>&1
)

echo ============================================
echo   封印之殿 · 《第七天》 2D 叙事 Demo
echo ============================================

echo [1/3] 检查 Node.js ...
node -v >nul 2>&1
if errorlevel 1 (
  echo   错误：未检测到 Node.js（需要 18+）。请先安装 https://nodejs.org/
  pause
  exit /b 1
)

echo [2/3] 启动服务器 http://localhost:8890 ...
echo   启动完成后会自动打开浏览器。关闭本窗口即停止游戏。
set AUTO_OPEN_BROWSER=1
node server.js

pause
