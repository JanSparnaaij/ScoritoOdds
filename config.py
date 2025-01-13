import os
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    
    # Only replace if DATABASE_URL is non-empty
    SQLALCHEMY_DATABASE_URI = (
        DATABASE_URL.replace("postgres://", "postgresql://")
        if DATABASE_URL
        else "sqlite:///site.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

