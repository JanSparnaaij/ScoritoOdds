web: docker-entrypoint.sh web
worker: PYTHONPATH=./app celery -A app.tasks worker --loglevel=info