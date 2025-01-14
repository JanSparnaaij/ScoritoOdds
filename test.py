from redis import Redis
import os

# redis_url = "rediss://:pd0b34a6a19e46593bffc8b735ba51e0527546f14206207a0559ed66166173f0c@ec2-3-226-89-44.compute-1.amazonaws.com:14790"
redis_url = os.getenv("REDIS_URL")
try:
    redis_client = Redis.from_url(
        redis_url,
        ssl_cert_reqs="required",
        ssl_ca_certs=r"C:\Users\JanSparnaaijDenofDat\source\repos\ScoritoOdds\certificate.pem"
    )
    print("Redis connected:", redis_client.ping())
except Exception as e:
    print(f"Redis connection failed: {e}")

