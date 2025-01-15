#!/bin/bash

set -e

# Check the first argument to determine the role
if [ "$1" = "web" ]; then
    echo "Starting web service..."
    flask db upgrade && hypercorn --bind 0.0.0.0:${PORT} run:app
elif [ "$1" = "worker" ]; then
    echo "Starting worker service..."
    celery -A app.celery_worker.celery worker --loglevel=info
else
    # Default behavior
    exec "$@"
fi
