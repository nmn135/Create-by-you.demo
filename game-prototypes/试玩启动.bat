@echo off
title Sealed Hall - One-Click Playtest
cd /d D:\Create by you.demo\game-prototypes

echo ============================================
echo   封印之殿 一键试玩
echo ============================================

echo [0/4] 清理旧进程...
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Create by you.demo\game-prototypes\kill_old_servers.ps1"
ping -n 2 127.0.0.1 >nul

echo [1/4] 启动游戏服务器 (http://localhost:8080) ...
powershell -NoProfile -Command "Start-Process -FilePath 'C:\Python314\python.exe' -ArgumentList '-X','utf8','server.py' -WorkingDirectory 'D:\Create by you.demo\game-prototypes' -WindowStyle Hidden"
echo   - 等待服务器就绪 5 秒...
ping -n 6 127.0.0.1 >nul

echo [2/4] 重置为 stage=0 (新开局, NPC 逐个入场) ...
curl -s -X POST http://localhost:8080/api/reset >nul 2>&1

echo [3/4] 验证状态...
curl -s http://localhost:8080/api/state | findstr /C:"current_stage"

echo [4/4] 开始游戏...
start http://localhost:8080

echo.
echo ============================================
echo   游玩提示
echo   操作: WASD 移动 / 鼠标转视角 / Shift 奔跑 / 空格跳跃
echo         V 关系网 / M 记忆 / H 帮助
echo   开场: 黑屏打字剧情 → 点任意处推进 → 点「进入大殿」
echo         进入后点「等待」按钮让冒险者逐个入场
echo   模型替换指引: 见 docs 目录 mixamo-model-guide.md / game-feel-reference.md
echo ============================================
pause
