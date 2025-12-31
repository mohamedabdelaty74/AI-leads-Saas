# Lightweight Dockerfile for Railway Deployment (API Mode)
# NO GPU, NO torch, NO transformers - just HuggingFace API!

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy ONLY the lightweight requirements
COPY requirements-railway.txt .

# Install Python packages (lightweight - no ML libraries!)
RUN pip install --no-cache-dir -r requirements-railway.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/database /app/logs

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV USE_HF_API=true
ENV ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI backend (NOT Gradio - that's for local development)
# Hardcode port 8000 - Railway will map it to $PORT externally
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
