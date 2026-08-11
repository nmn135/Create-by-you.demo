@echo off
rem ============================================
rem  Sealed Hall - one-click launcher
rem  Run server then open browser automatically
rem ============================================
cd /d "%~dp0"

where python >/dev/null 2>&1
if %errorlevel%==0 (
  start "Sealed Hall Server" cmd /k python -X utf8 server.py
) else (
  where py >/dev/null 2>&1
  if %errorlevel%==0 (
    start "Sealed Hall Server" cmd /k py -X utf8 server.py
  ) else (
    echo [ERROR] Python not found. Please install Python or run:
    echo   "C:\Python314\python.exe" -X utf8 server.py
    pause
    exit /b 1
  )
)

timeout /t 3 /nobreak >/dev/null
start "" "http://localhost:8080"
echo.
echo Server started: http://localhost:8080
echo Close the black server window to stop the game.
pause
