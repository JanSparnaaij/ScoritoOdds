from app import create_app
from celery import Celery
import os

def create_celery_app(app=None):
    """Create and configure a Celery application instance."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ssl_cert_path = os.getenv("SSL_CERT_PATH", None)
    environment = os.getenv("FLASK_ENV", "development")  # Default to development

    celery = Celery(
        app.import_name if app else __name__,
        broker=redis_url,
        backend=redis_url,
        include=["app.tasks"],  # Include your Celery tasks
    )

    # Configure SSL for Redis
    if redis_url.startswith("rediss://"):
        ssl_config = {"ssl_cert_reqs": None} if environment == "development" else {"ssl_cert_reqs": "required"}
        if ssl_cert_path:
            ssl_config["ssl_ca_certs"] = ssl_cert_path
        celery.conf.update(
            broker_transport_options={"ssl": ssl_config},
            redis_backend_transport_options={"ssl": ssl_config},
        )

    # Updated Celery configuration
    celery.conf.update({
        "result_backend": redis_url,  # Updated from CELERY_RESULT_BACKEND
        "broker_url": redis_url,
        "worker_concurrency": 2,
        "worker_prefetch_multiplier": 1,
        "task_acks_late": True,
        "task_soft_time_limit": 300,
        "task_time_limit": 360,
        "broker_heartbeat": 10,
        "broker_connection_retry": True,  # Still supported in Celery 5.x
        "broker_connection_retry_on_startup": True,  # Required for Celery 6.x+
        "broker_connection_max_retries": 5,
    })

    # Integrate Flask app context
    if app:
        celery.conf.update(app.config)

        TaskBase = celery.Task

        class ContextTask(TaskBase):
            abstract = True
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)

        celery.Task = ContextTask

    return celery

# Flask app integration
flask_app = create_app()
celery = create_celery_app(flask_app)
