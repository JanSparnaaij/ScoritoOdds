from app import create_app
from celery import Celery
import os

def create_celery_app(app=None):
    """Create and configure a Celery application instance."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ssl_cert_path = os.getenv("SSL_CERT_PATH", "/certificate.pem")

    ssl_config = {
        "ssl_cert_reqs": "CERT_OPTIONAL",  # 'CERT_REQUIRED' or 'CERT_NONE' if needed
        "ssl_ca_certs": ssl_cert_path,
    }

    celery = Celery(
        app.import_name if app else __name__,
        broker=redis_url,
        backend=redis_url,
        include=["app.tasks"],  
    )

    if redis_url.startswith("rediss://"):
        celery.conf.update(
            broker_transport_options={"ssl": ssl_config},
            redis_backend_transport_options={"ssl": ssl_config},
        )

    # General Celery configuration
    celery.conf.update({
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "timezone": "UTC",
        "enable_utc": True,
    })

    if app:
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            abstract = True

            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return super().__call__(*args, **kwargs)

        celery.Task = ContextTask

    return celery

# Create Flask app and integrate with Celery
flask_app = create_app()
celery = create_celery_app(flask_app)
