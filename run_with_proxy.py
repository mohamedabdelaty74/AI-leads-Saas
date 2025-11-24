#!/usr/bin/env python3
"""
Run Gradio app with backend API proxy
This makes the backend accessible through the Gradio public URL
"""

import subprocess
import sys
import time

def main():
    print("=" * 60)
    print("Starting Elite Creatif with API Proxy")
    print("=" * 60)

    # Start backend in background
    print("\n[1/2] Starting backend API...")
    backend_process = subprocess.Popen(
        [sys.executable, "backend/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # Wait for backend to start
    time.sleep(5)
    print("✅ Backend API started")

    # Start Gradio with API proxy
    print("\n[2/2] Starting Gradio with proxy...")

    # Import gradio app
    import gradio_saas_integrated

if __name__ == "__main__":
    main()
