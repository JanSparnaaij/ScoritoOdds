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
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Configure Celery with Redis as broker and backend
    celery = Celery(
        app.import_name if app else __name__,
        broker=redis_url,
        backend=redis_url,
    )

    # Update Celery configuration with Flask app settings
    if app:
        celery.conf.update(app.config)
        celery.conf.update({'broker_connection_retry_on_startup': True})

    celery.autodiscover_tasks(["app.tasks"])  # Discover tasks in `app.tasks`
    return celery

# Suppress SSL certificate warnings for development
warnings.filterwarnings("ignore")

# Create Celery app
celery = create_celery_app()
