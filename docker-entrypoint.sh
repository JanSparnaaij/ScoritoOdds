#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

echo "Entrypoint argument: $1"
echo "Running process as: $(whoami)"

# ✅ Load environment variables safely
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    set -a
    source .env
    set +a
fi

# ✅ Ensure `redis` package is installed
if ! python -c "import redis" 2>/dev/null; then
    echo "Redis module not found. Installing..."
    pip install --no-cache-dir redis
fi

# ✅ Set Redis URL properly
REDIS_URL=${REDIS_URL:-redis://redis:6379/0}
echo "Using Redis URL: $REDIS_URL"

# ✅ Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
max_retries=30
retry_count=0

until python - <<EOF
import redis, sys, os
try:
    r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), socket_timeout=5)
    r.ping()
    sys.exit(0)
except redis.ConnectionError as e:
    print(f"Connection failed: {str(e)}", file=sys.stderr)
    sys.exit(1)
EOF
do
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $max_retries ]; then
        echo "Error: Redis connection failed after $max_retries attempts. Exiting."
        exit 1
    fi
    echo "Redis is unavailable - waiting... (Attempt $retry_count/$max_retries)"
    sleep 2
done
echo "✅ Redis is ready!"

# ✅ Start the requested service
case "$1" in
    web)
        echo "🚀 Starting web service..."
        if [ "$FLASK_ENV" = "development" ]; then
            exec flask run --host=0.0.0.0 --port=${PORT:-8000}
        else
            exec gunicorn --bind 0.0.0.0:${PORT:-8000} \
                         --workers ${WORKERS:-4} \
                         --timeout 120 \
                         --access-logfile - \
                         --error-logfile - \
                         "app:create_app()"
        fi
        ;;
    worker)
        echo "🚀 Starting Celery worker..."
        exec celery -A app.celery_worker.celery worker --loglevel=info --concurrency=1
        ;;
    bash)
        echo "Opening bash shell for debugging..."
        exec bash
        ;;
    *)
        echo "Unknown command: $1"
        exit 1
        ;;
esac
