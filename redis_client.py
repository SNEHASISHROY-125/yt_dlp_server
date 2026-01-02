# redis_client.py
import redis.asyncio as redis
import os

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST","localhost"),
    port=os.getenv("REDIS_PORT",6379),
    decode_responses=True
)

