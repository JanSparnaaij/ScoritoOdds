from celery import Celery
import os
import warnings
from urllib.parse import urlparse

def create_celery_app(app=None):
    """
    Create and configure a Celery application instance.

    Args:
        app: Flask application instance (optional)

    Returns:
        Configured Celery instance
    """
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    parsed_url = urlparse(redis_url)

    # Set SSL options if the Redis URL scheme is 'rediss'
    ssl_options = {}
    if parsed_url.scheme == 'rediss':
        ssl_options = {'ssl_cert_reqs': 'CERT_NONE'}

    # Configure Celery with Redis as broker and backend
    celery = Celery(
        app.import_name if app else __name__,
        broker=redis_url,
        backend=redis_url,
        broker_use_ssl=ssl_options if parsed_url.scheme == 'rediss' else None,
        redis_backend_use_ssl=ssl_options if parsed_url.scheme == 'rediss' else None,
    )

    # Update Celery configuration with Flask app settings
    if app:
        celery.conf.update(app.config)
        celery.conf.update({
            'broker_connection_retry_on_startup': True,
        })

    celery.autodiscover_tasks(["app.tasks"])  # Discover tasks in `app.tasks`
    return celery

# Suppress SSL certificate warnings for development
warnings.filterwarnings("ignore")

# Create Celery app
celery = create_celery_app()
