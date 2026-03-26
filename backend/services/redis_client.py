import os
import redis

_redis = None


def get_redis():
    global _redis
    if _redis is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis = redis.from_url(redis_url, decode_responses=True)
    return _redis


def publish(channel: str, message: str):
    client = get_redis()
    client.publish(channel, message)


def subscribe(channel: str):
    client = get_redis()
    pubsub = client.pubsub()
    pubsub.subscribe(channel)
    return pubsub
