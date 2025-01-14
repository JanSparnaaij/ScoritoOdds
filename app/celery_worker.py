from celery import Celery
import os
import warnings

def create_celery_app(app=None):
    """
    Create and configure a Celery application instance.

    Args:
        app: Flask application instance (optional)

    Returns:
        Configured Celery instance
    """
    celery = Celery(
        app.import_name if app else __name__,
        broker=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),  # Message broker
        backend=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),  # Result backend
    )

    if app:
        celery.conf.update(app.config)

    celery.autodiscover_tasks(["app.tasks"])  # Discover tasks in `app.tasks`
    return celery

# Suppress SSL certificate warnings
warnings.filterwarnings(
    "ignore", 
    message="Setting ssl_cert_reqs=CERT_NONE when connecting to redis means that celery will not validate the identity of the redis broker"
)

celery = create_celery_app()
