@echo off
REM Production startup script for Windows
REM This runs the backend with multiple workers for better concurrency

echo =========================================
echo Starting Elite Creatif API in PRODUCTION MODE
echo =========================================
echo.

REM Set environment to production
set ENV=production

REM Start the backend
cd /d "%~dp0"
python backend/main.py
