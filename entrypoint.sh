#!/bin/bash

# Entrypoint script for Cloud Run / Docker
# This script starts Cloud SQL Proxy (if needed) and FastAPI application

set -e

# Debug output
echo "=== Starting System LLM Backend ==="
echo "Database URL: ${DATABASE_URL}"
echo "Cloud SQL Instance: ${CLOUD_SQL_INSTANCES}"
echo "Port: ${PORT:-8000}"

# Only start Cloud SQL Proxy if:
# 1. CLOUD_SQL_INSTANCES is set
# 2. DATABASE_URL points to 127.0.0.1 (localhost)
# 3. Credentials available (gcloud auth for Cloud Run)
# 4. SKIP_PROXY not set (for docker-compose with separate proxy container)

if [ -n "$CLOUD_SQL_INSTANCES" ] && [ -z "$SKIP_PROXY" ]; then
    # Check if we have gcloud credentials
    if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ] || [ -d "$HOME/.config/gcloud" ]; then
        echo "Starting Cloud SQL Proxy for: ${CLOUD_SQL_INSTANCES}"

        # Start Cloud SQL Proxy in background
        # It will listen on 127.0.0.1:5432 (localhost:5432)
        /opt/cloud-sql-proxy/cloud-sql-proxy \
            --address 127.0.0.1 \
            --port 5432 \
            ${CLOUD_SQL_INSTANCES} &

        PROXY_PID=$!
        echo "Cloud SQL Proxy started with PID: ${PROXY_PID}"

        # Wait a moment for proxy to start
        sleep 2

        # Check if proxy started successfully
        if ! kill -0 $PROXY_PID 2>/dev/null; then
            echo "Warning: Cloud SQL Proxy failed to start, but continuing..."
        fi
    else
        echo "Note: Skipping Cloud SQL Proxy (no credentials found)"
        echo "For docker-compose.cloudsql.yml: proxy runs as separate container"
    fi
else
    echo "Note: Proxy startup skipped (SKIP_PROXY or separate proxy container in use)"
fi

echo "Starting FastAPI application..."

# Start FastAPI with uvicorn
# Use PORT env var (Cloud Run default 8080), fallback to 8000
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000}
