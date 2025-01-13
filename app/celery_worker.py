from celery import Celery

def create_celery_app(app=None):
    celery = Celery(
        app.import_name,
        broker=app.config.get("CACHE_REDIS_URL"),
        backend=app.config.get("CACHE_REDIS_URL"),
    )
    if app:
        celery.conf.update(app.config)
    return celery
