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

# ✅ Ensure Playwright is installed
if ! python -c "import playwright" 2>/dev/null; then
    echo "Playwright module not found. Installing..."
    pip install --no-cache-dir playwright
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

# ✅ Playwright Setup for Celery Worker
if [ "$1" = "worker" ]; then
    echo "Ensuring Playwright browsers are installed for the worker..."
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright-browsers playwright install --with-deps
fi

# ✅ Drop Root Privileges for Celery (Security Best Practice)
if [ "$1" = "worker" ] && [ "$(id -u)" = "0" ]; then
    echo "⚠️ WARNING: Running Celery as root is not recommended. Switching to a non-root user..."
    useradd -m celeryuser
    chown -R celeryuser:celeryuser /app /ms-playwright-browsers
    exec su celeryuser -c "celery -A app.celery_worker.celery worker --loglevel=info --concurrency=1"
fi

# ✅ Start the requested service
case "$1" in
    web)
        echo "🚀 Starting Flask web service..."
        exec flask run --host=0.0.0.0 --port=${PORT:-8000}
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
        echo "Executing custom command: $@"
        exec "$@"
        ;;
esac
