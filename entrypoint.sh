#!/bin/bash
set -e

echo "🚀 Starting System LLM Backend Initialization..."

# Wait for database to be ready (retry logic for Cloud Run)
echo "⏳ Waiting for database connection..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if python -c "from app.core.database import engine; engine.connect()" 2>/dev/null; then
        echo "✅ Database is ready!"
        break
    fi
    echo "  Attempt $attempt/$max_attempts - Database not ready yet, retrying in 2 seconds..."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Failed to connect to database after $max_attempts attempts"
    exit 1
fi

# Run database migrations (if alembic exists)
if [ -f "alembic.ini" ]; then
    echo "🔄 Running database migrations..."
    alembic upgrade head || echo "⚠️  Migrations failed or already up to date"
fi

# Create admin user if ADMIN_EMAIL is set
if [ -n "$ADMIN_EMAIL" ]; then
    echo "👤 Creating admin user..."
    python -m app.scripts.seed_admin || echo "⚠️  Admin creation failed (may already exist)"
fi

echo "✅ Initialization complete!"
echo "🎯 Starting FastAPI server..."

# Start the FastAPI application
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
