# Dockerfile
FROM python:3.10-slim

# Set labels
LABEL maintainer="RezHive"
LABEL version="13.3.0"
LABEL description="Phoenix Kernel - Sovereign AI Trading Swarm"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash rezuser

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=rezuser:rezuser . .

# Create necessary directories
RUN mkdir -p data/memory data/event_store data/backups logs && \
    chown -R rezuser:rezuser data logs

# Switch to non-root user
USER rezuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Expose ports
EXPOSE 8002

# Run the application
CMD ["python", "phoenix_kernel_v14c.py"]