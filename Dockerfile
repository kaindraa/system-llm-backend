# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (including wget for downloading cloud-sql-proxy)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download Cloud SQL Proxy v2.18.2
RUN mkdir -p /opt/cloud-sql-proxy && \
    wget -q https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.18.2/cloud-sql-proxy.linux.amd64 \
    -O /opt/cloud-sql-proxy/cloud-sql-proxy && \
    chmod +x /opt/cloud-sql-proxy/cloud-sql-proxy && \
    echo "Cloud SQL Proxy installed"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code and project files
COPY . /app/

# Set PYTHONPATH to include the app directory
ENV PYTHONPATH=/app:$PYTHONPATH

# Create required directories
RUN mkdir -p /app/logs /app/credentials /app/storage/uploads

# Copy GCS credentials file
COPY credentials/system-llm-storage-key.json /app/credentials/system-llm-storage-key.json

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port (Cloud Run uses PORT env variable, default 8000)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run entrypoint script that manages both Cloud SQL Proxy and FastAPI
ENTRYPOINT ["/app/entrypoint.sh"]
