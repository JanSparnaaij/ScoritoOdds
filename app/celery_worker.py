from celery import Celery
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
        
        # Dynamically register tasks to avoid circular imports
        with app.app_context():
            import app.tasks  # Import tasks explicitly
            celery.autodiscover_tasks(["app.tasks"])  # Auto-discover tasks in app.tasks

    # Explicitly discover tasks
    celery.autodiscover_tasks(["app.tasks"])

    return celery

# Define a global Celery instance
celery = create_celery_app()
