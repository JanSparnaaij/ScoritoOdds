from celery import Celery
import os

def create_celery_app(app=None):
    celery = Celery(
        app.import_name if app else __name__,
        broker=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        backend=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    )

    if app:
        celery.conf.update(app.config)

    celery.autodiscover_tasks(["app.tasks"])
    return celery

celery = create_celery_app()
