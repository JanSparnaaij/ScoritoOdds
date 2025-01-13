from celery import Celery
import os

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
        broker=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),  # Broker URL
        backend=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),  # Result backend
    )
    if app:
        celery.conf.update(app.config)  # Load Flask app configuration into Celery
        # Register tasks dynamically here to avoid circular import
        with app.app_context():
            from app import tasks  # Import tasks within the app context
            celery.autodiscover_tasks(["app.tasks"])  # Register all tasks from app.tasks
    return celery
