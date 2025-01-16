#!/bin/bash
set -e

echo "Entrypoint argument: $1" >> /tmp/entrypoint-debug.log
echo "Running process as: $(whoami)" >> /tmp/entrypoint-debug.log

case "$1" in
    web)
        echo "Starting web service..."
        flask db upgrade && exec hypercorn --bind 0.0.0.0:${PORT} run:app
        ;;
    worker)
        echo "Starting worker service..."
        exec celery -A app.celery_worker worker --loglevel=info
        ;;
    bash)
        echo "Starting bash shell for debugging..."
        exec bash
        ;;
    *)
        echo "Invalid argument: $1"
        echo "Usage: docker-entrypoint.sh [web|worker|bash]"
        exit 1
        ;;
esac
