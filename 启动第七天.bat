@echo off
chcp 65001 >nul
title 封印之殿 · 《第七天》 2D 叙事 Demo
cd /d "%~dp0game-prototypes\2d-narrative-demo"

echo ============================================
echo   封印之殿 · 《第七天》 2D 叙事 Demo
echo ============================================

echo [1/2] 检查 Node.js ...
node -v >nul 2>&1
if errorlevel 1 (
  echo   错误：未检测到 Node.js（需要 18+）。请先安装 https://nodejs.org/
  pause
  exit /b 1
)

echo [2/2] 启动服务器 http://localhost:8890 ...
echo   启动完成后会自动打开浏览器。关闭本窗口即停止游戏。
start "" http://localhost:8890
node server.js

pause
