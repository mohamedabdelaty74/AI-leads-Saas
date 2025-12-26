#!/bin/bash
# Production startup script for Linux/Mac
# This runs the backend with multiple workers for better concurrency

echo "========================================="
echo "Starting Elite Creatif API in PRODUCTION MODE"
echo "========================================="
echo ""

# Set environment to production
export ENV=production

# Start the backend
cd "$(dirname "$0")"
python backend/main.py
