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
        include=["app.tasks"],
    )

    # Update configuration for SSL if using rediss://
    if redis_url.startswith("rediss://"):
        if environment == "production":
            ssl_config = {"ssl_cert_reqs": "required"}
            if ssl_cert_path:
                ssl_config["ssl_ca_certs"] = ssl_cert_path
        else:
            # Relaxed SSL validation for local development
            ssl_config = {"ssl_cert_reqs": "none"}

        celery.conf.update(
            broker_use_ssl=ssl_config,
            redis_backend_use_ssl=ssl_config,
        )

    # Update with Flask app configuration if app is provided
    if app:
        celery.conf.update(app.config)

    celery.conf.update(
        worker_concurrency=2,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_soft_time_limit=300,
        task_time_limit=360,
        broker_heartbeat=10,
        broker_connection_retry=True,
        broker_connection_max_retries=5,
    )

    return celery

celery = create_celery_app()
