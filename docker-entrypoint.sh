#!/bin/bash
set -e
echo "Entrypoint script executed with argument: $1"

case "$1" in
  web)
    echo "Starting web service..."
    flask db upgrade && hypercorn --bind 0.0.0.0:${PORT} run:app
    ;;
  worker)
    echo "Starting worker service..."
    celery -A app.celery_worker.celery worker --loglevel=info
    ;;
  *)
    echo "Invalid argument: $1"
    echo "Usage: docker-entrypoint.sh [web|worker]"
    exit 1
    ;;
esac
