@echo off
REM Elite Creatif Frontend - Quick Installation Script (Windows)
REM Run this script to set up your frontend in one command

echo.
echo ========================================
echo   Elite Creatif Frontend Setup
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

REM Display Node version
echo [OK] Node.js detected
node -v
echo.

REM Install dependencies
echo [STEP 1/3] Installing dependencies...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed
echo.

REM Create .env.local if it doesn't exist
echo [STEP 2/3] Setting up environment...
if not exist .env.local (
    echo Creating .env.local file...
    copy .env.local.example .env.local >nul
    echo [OK] .env.local created
) else (
    echo [INFO] .env.local already exists
)

echo.
echo [STEP 3/3] Setup complete!
echo.
echo ========================================
echo   Next Steps:
echo ========================================
echo.
echo 1. Ensure your backend is running on http://localhost:8000
echo 2. Run 'npm run dev' to start the development server
echo 3. Open http://localhost:3000 in your browser
echo.
echo ========================================
echo   Documentation:
echo ========================================
echo.
echo - README.md - Complete documentation
echo - SETUP.md - Quick start guide
echo - COMPONENTS.md - Component reference
echo - COMPLETE-GUIDE.md - Full implementation guide
echo - FEATURES-SHOWCASE.md - Visual feature guide
echo.
echo Happy coding!
echo.
pause
