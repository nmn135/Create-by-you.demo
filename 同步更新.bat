@echo off
chcp 65001 >nul
title 封印之殿 · 同步最新代码
cd /d "%~dp0"

echo ============================================
echo   封印之殿 · 同步最新代码
echo ============================================
echo.

REM [0/3] 检查 git
where git >nul 2>&1
if errorlevel 1 (
  echo 错误：未检测到 git。请先安装 https://git-scm.com/
  pause
  exit /b 1
)

REM [1/3] 确保 upstream 指向主仓库 nmn135
git remote get-url upstream >nul 2>&1
if errorlevel 1 (
  echo [1/3] 首次运行：添加主仓库为 upstream ...
  git remote add upstream https://github.com/nmn135/Create-by-you.demo.git
  if errorlevel 1 (
    echo 错误：添加 upstream 失败。
    pause
    exit /b 1
  )
) else (
  echo [1/3] upstream 已配置 ✓
)

REM [2/3] 确保在 main 分支
git checkout main >nul 2>&1

REM [3/3] 拉取并合并主仓库最新
echo [2/3] 拉取主仓库最新提交 ...
git fetch upstream main
if errorlevel 1 (
  echo 错误：拉取失败。请检查网络连接。
  pause
  exit /b 1
)

echo [3/3] 合并到本地 main ...
git merge upstream/main
if errorlevel 1 (
  echo.
  echo 同步失败：本地有未提交改动或冲突。
  echo 请让 AI 处理（先 commit 本地改动，再解决冲突）。
  pause
  exit /b 1
)

echo.
echo 同步完成 ✓  现在可以双击《启动第七天.bat》运行最新版。
pause
