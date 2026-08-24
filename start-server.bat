@echo off
title Watermarks Remover Studio
echo =========================================================
echo   Starting Watermarks Remover & Document Studio
echo =========================================================
echo.
echo Opening Web Studio in your default browser...
echo Address: http://localhost:8765
echo.

start "" "http://localhost:8765"

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py service/scripts/server.py --host 127.0.0.1 --port 8765
) else (
    python service/scripts/server.py --host 127.0.0.1 --port 8765
)
pause
