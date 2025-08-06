#!/usr/bin/env bash
set -e

echo "🚀 Starting ChatAPI with bundled workers..."

# Run database migrations and pre-start checks
echo "📊 Running database migrations..."
python /chatapi/app/api_pre_start.py

# Start Celery worker in the background
echo "🔧 Starting Celery worker..."
celery -A app.core.celery_app worker -l info -Q main-queue -c 1 --detach

# Start Celery beat scheduler in the background
echo "⏰ Starting Celery beat scheduler..."
celery -A app.core.celery_app beat --loglevel=info --detach

# Give workers a moment to start
sleep 2

# Start FastAPI server in the foreground
echo "🌐 Starting FastAPI server..."
exec fastapi run --workers 4 app/main.py
