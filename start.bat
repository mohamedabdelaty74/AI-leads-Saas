@echo off
REM Elite Creatif - Complete Application Startup (Windows)
REM This script starts both backend and frontend

echo.
echo ========================================
echo   Elite Creatif - Full Stack Launch
echo ========================================
echo.

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Check if Node.js is installed
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

echo [OK] Node.js found
node -v
echo.

REM Check if .env exists
if not exist .env (
    echo [WARNING] .env file not found!
    echo.
    echo Creating .env from .env.example...
    copy .env.example .env >nul
    echo.
    echo [IMPORTANT] Please edit .env file and add your API keys:
    echo - GOOGLE_API_KEY
    echo - HUGGINGFACE_API_KEY
    echo - SERPAPI_KEY
    echo.
    echo Press any key to open .env file in notepad...
    pause >nul
    notepad .env
    echo.
)

REM Check if frontend is set up
if not exist frontend\node_modules (
    echo [SETUP] Frontend not installed. Installing dependencies...
    echo.
    cd frontend
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Frontend installation failed
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo [OK] Frontend dependencies installed
    echo.
)

REM Create database directory
if not exist database mkdir database

echo.
echo ========================================
echo   Starting Backend API Server
echo ========================================
echo.
echo Backend will run on: http://localhost:8000
echo API Docs available at: http://localhost:8000/docs
echo.

REM Start backend in new window
start "Elite Creatif - Backend API" cmd /k "python backend\main.py"

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   Starting Frontend Development Server
echo ========================================
echo.
echo Frontend will run on: http://localhost:3000
echo.

REM Start frontend in new window
start "Elite Creatif - Frontend" cmd /k "cd frontend && npm run dev"

REM Wait a moment
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   SUCCESS! Application is Starting
echo ========================================
echo.
echo Two terminal windows have opened:
echo   1. Backend API (Python/FastAPI)
echo   2. Frontend UI (Next.js/React)
echo.
echo Open your browser and go to:
echo   http://localhost:3000
echo.
echo API Documentation available at:
echo   http://localhost:8000/docs
echo.
echo To stop: Close both terminal windows
echo.
echo ========================================
echo.
pause
