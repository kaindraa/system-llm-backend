#!/bin/bash

# Entrypoint script for Cloud Run
# This script starts Cloud SQL Proxy and FastAPI application

set -e

# Debug output
echo "=== Starting System LLM Backend ==="
echo "Database URL: ${DATABASE_URL}"
echo "Cloud SQL Instance: ${CLOUD_SQL_INSTANCES}"
echo "Port: ${PORT:-8000}"

# Start Cloud SQL Proxy if CLOUD_SQL_INSTANCES is set
if [ -n "$CLOUD_SQL_INSTANCES" ]; then
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
        echo "Error: Cloud SQL Proxy failed to start"
        exit 1
    fi
else
    echo "Warning: CLOUD_SQL_INSTANCES not set - proxy will not start"
fi

echo "Starting FastAPI application..."

# Start FastAPI with uvicorn
# Use PORT env var (Cloud Run default 8080), fallback to 8000
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000}
