@echo off
rem ============================================
rem  Sealed Hall - one-click launcher
rem  Kill old server on 8080 first -> always fresh stage 0
rem ============================================
cd /d "%~dp0"

rem --- Clear any existing server on port 8080 (fresh start) ---
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
  taskkill /F /PID %%p >nul 2>&1
)

where python >nul 2>&1
if %errorlevel%==0 (
  start "Sealed Hall Server" cmd /k python -X utf8 server.py
) else (
  where py >nul 2>&1
  if %errorlevel%==0 (
    start "Sealed Hall Server" cmd /k py -X utf8 server.py
  ) else (
    echo [ERROR] Python not found. Please install Python or run:
    echo   "C:\Python314\python.exe" -X utf8 server.py
    pause
    exit /b 1
  )
)

timeout /t 3 /nobreak >nul
start "" "http://localhost:8080"
echo.
echo Server started: http://localhost:8080  (fresh stage 0)
echo Close the black server window to stop the game.
pause
