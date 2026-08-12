@echo off
chcp 65001 >nul
title 封印之殿 — 12:00 试玩前冒烟体检
echo 正在运行一键冒烟（13 项体检）... 请确保 server.py 已启动（http://localhost:8080）
cd /d D:\tools\playwright
node cdp_smoke_1200.js
echo.
echo 全绿 🟢 直接开玩；有 ❌ 看上面那一行。
pause
