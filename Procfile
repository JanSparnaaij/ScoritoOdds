release: playwright install
web: hypercorn "app:create_app()" --bind 0.0.0.0:$PORT --timeout 120
worker: celery -A app.celery_worker worker --loglevel=info
