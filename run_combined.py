#!/usr/bin/env python3
"""
Combined Gradio + FastAPI Backend
Mounts the backend API into Gradio so it's accessible through the public URL
"""

import os
import sys

# Set backend URL to use relative path
os.environ["BACKEND_URL"] = "/api"

# Import FastAPI backend
from backend.main import app as fastapi_app

# Import Gradio app
from gradio_saas_integrated import create_interface, init_db, initialize_email_templates_db

print("=" * 60)
print("Starting Elite Creatif - Combined App")
print("=" * 60)

# Initialize databases
init_db()
initialize_email_templates_db()

# Create Gradio interface
gradio_app = create_interface()

# Mount FastAPI backend into Gradio
# This makes the backend accessible at /api/* through the Gradio public URL
gradio_app.mount_gradio_app = fastapi_app

print("\n✅ Backend API mounted at /api")
print("✅ Gradio UI ready")
print("\nStarting combined server...")

# Launch with both Gradio and FastAPI
gradio_app.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=True,
    show_error=True
)
