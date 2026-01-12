@echo off
cd /d %~dp0
echo Starting Whisper Server...
powershell -NoProfile -ExecutionPolicy Bypass -File "run.ps1"
if %errorlevel% neq 0 (
    echo.
    echo Server exited with error.
    pause
)
