from celery import Celery
import os

def create_celery_app(app=None):
    """Create and configure a Celery application instance."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ssl_cert_path = os.getenv("SSL_CERT_PATH", None)
    environment = os.getenv("FLASK_ENV", "development")  # Default to development
    print(environment)
    
    celery = Celery(
        app.import_name if app else __name__,
        broker=redis_url,
        backend=redis_url,
        include=["app.tasks"],
    )

    # Update configuration for SSL if using rediss://
    if redis_url.startswith("rediss://"):
        if environment == "production":
            # Strict SSL validation for production
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
        celery.conf.update({"broker_connection_retry_on_startup": True})

    return celery

# Instantiate Celery without Flask app context
celery = create_celery_app()
