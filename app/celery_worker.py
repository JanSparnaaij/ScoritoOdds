from celery import Celery
import os

def create_celery_app(app=None):
    """Create and configure a Celery application instance."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    celery = Celery(
        app.import_name if app else __name__,
        broker=redis_url,
        backend=redis_url,
        include=["app.tasks"],
    )

    # Update configuration for SSL if using rediss://
    if redis_url.startswith("rediss://"):
        celery.conf.update(
            broker_use_ssl={
                "ssl_cert_reqs": "required",
                "ssl_ca_certs": "/certificate.pem",  # Ensure this matches your Dockerfile path
            },
            redis_backend_use_ssl={
                "ssl_cert_reqs": "required",
                "ssl_ca_certs": "/certificate.pem",
            }
        )

    # Update with Flask app configuration if app is provided
    if app:
        celery.conf.update(app.config)
        celery.conf.update({"broker_connection_retry_on_startup": True})

    return celery

# Instantiate Celery without Flask app context
celery = create_celery_app()
