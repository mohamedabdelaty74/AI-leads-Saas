# Elite Creatif - Docker Container for Vast.ai GPU
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV TRANSFORMERS_CACHE=/app/models
ENV HF_HOME=/app/models

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install --upgrade pip setuptools wheel

# Copy requirements first (for Docker caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/models \
    /app/database \
    /app/scraped_data \
    /app/logs

# Expose ports
# 8000: Backend API
# 7860: Gradio UI
EXPOSE 8000 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:7860 || exit 1

# Default command - run Gradio app
CMD ["python3", "gradio_saas_integrated.py"]
