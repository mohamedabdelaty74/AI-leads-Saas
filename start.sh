#!/bin/bash
# Elite Creatif - Complete Application Startup (Linux/Mac)
# This script starts both backend and frontend

set -e  # Exit on error

echo ""
echo "========================================"
echo "  Elite Creatif - Full Stack Launch"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.10+ first"
    exit 1
fi

echo "[OK] Python found: $(python3 --version)"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed"
    echo "Please install Node.js 18+ first"
    exit 1
fi

echo "[OK] Node.js found: $(node -v)"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "[WARNING] .env file not found!"
    echo ""
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "[IMPORTANT] Please edit .env file and add your API keys:"
    echo "- GOOGLE_API_KEY"
    echo "- HUGGINGFACE_API_KEY"
    echo "- SERPAPI_KEY"
    echo ""
    echo "Press Enter to continue after editing .env..."
    read
fi

# Check if frontend is set up
if [ ! -d "frontend/node_modules" ]; then
    echo "[SETUP] Frontend not installed. Installing dependencies..."
    echo ""
    cd frontend
    npm install
    cd ..
    echo "[OK] Frontend dependencies installed"
    echo ""
fi

# Create database directory
mkdir -p database

echo ""
echo "========================================"
echo "  Starting Backend API Server"
echo "========================================="
echo ""
echo "Backend will run on: http://localhost:8000"
echo "API Docs available at: http://localhost:8000/docs"
echo ""

# Start backend in background
python3 backend/main.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

echo ""
echo "========================================"
echo "  Starting Frontend Development Server"
echo "========================================"
echo ""
echo "Frontend will run on: http://localhost:3000"
echo ""

# Start frontend in background
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "Frontend PID: $FRONTEND_PID"

# Wait a moment
sleep 3

echo ""
echo "========================================"
echo "  SUCCESS! Application is Running"
echo "========================================"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Open your browser and go to:"
echo "  http://localhost:3000"
echo ""
echo "API Documentation available at:"
echo "  http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  Backend: logs/backend.log"
echo "  Frontend: logs/frontend.log"
echo ""
echo "To stop: kill $BACKEND_PID $FRONTEND_PID"
echo "Or run: ./stop.sh"
echo ""
echo "========================================"
echo ""

# Save PIDs for stop script
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for user interrupt
echo "Press Ctrl+C to stop all services..."
wait
