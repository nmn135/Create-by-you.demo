@echo off
chcp 65001 >nul
title Sealed Hall - One-Click Playtest (全新开局)
cd /d D:\Create by you.demo\game-prototypes

echo ============================================
echo   封印之殿 一键试玩（每次全新开局）
echo ============================================

echo [0/4] 清理旧服务器进程（保证全新状态）...
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Create by you.demo\game-prototypes\kill_old_servers.ps1"
ping -n 2 127.0.0.1 >nul

echo [1/4] 启动游戏服务器 (http://localhost:8080) ...
powershell -NoProfile -Command "Start-Process -FilePath 'C:\Python314\python.exe' -ArgumentList '-X','utf8','server.py' -WorkingDirectory 'D:\Create by you.demo\game-prototypes' -WindowStyle Hidden"
echo   - 等待服务器就绪 5 秒...
ping -n 6 127.0.0.1 >nul

echo [2/4] 重置为 stage=0（新开局，NPC 依次入场）...
curl -s -X POST http://localhost:8080/api/reset >nul 2>&1

echo [3/4] 验证状态...
curl -s http://localhost:8080/api/state | findstr /C:"current_stage"

echo [4/4] 开始游戏...
start http://localhost:8080

echo.
echo ============================================
echo   操作提示
echo   移动: WASD / 视角: 鼠标 / Shift 奔跑 / 空格跳
echo         Z 蹲 / C 切换视角 / V 系统提示 / M 地图 / H 帮助
echo   流程: 看完开场剧情 → 大厅中央等按钮 → 依次靠近 NPC 对话
echo   模型替换指南: 见 docs 目录 mixamo-model-guide.md
echo ============================================
pause
