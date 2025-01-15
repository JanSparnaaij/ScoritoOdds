import redis
redis_url = "rediss://:<password>@ec2-3-226-89-44.compute-1.amazonaws.com:14790/0"
r = redis.StrictRedis.from_url(redis_url, ssl=True, ssl_ca_certs="/certificate.pem")
print(r.ping())
