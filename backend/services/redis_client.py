import os
import logging
import threading
import time

import redis

logger = logging.getLogger(__name__)
_redis = None
_redis_lock = threading.Lock()


class InMemoryRedis:
    def __init__(self):
        self._data = {}
        self._expires = {}
        self._sets = {}

    def _purge_expired(self):
        now = time.time()
        for key in list(self._expires.keys()):
            if self._expires.get(key) is not None and self._expires[key] <= now:
                self._data.pop(key, None)
                self._sets.pop(key, None)
                self._expires.pop(key, None)

    def get(self, key):
        self._purge_expired()
        return self._data.get(key)

    def set(self, key, value, ex=None):
        self._purge_expired()
        self._data[key] = str(value)
        if ex is not None:
            self._expires[key] = time.time() + int(ex)

    def setex(self, key, seconds, value):
        self.set(key, value, ex=seconds)

    def exists(self, key):
        self._purge_expired()
        return 1 if key in self._data or key in self._sets else 0

    def sadd(self, key, member):
        self._purge_expired()
        if key not in self._sets:
            self._sets[key] = set()
        self._sets[key].add(member)

    def incr(self, key):
        self._purge_expired()
        value = int(self._data.get(key, "0"))
        value += 1
        self._data[key] = str(value)
        return value

    def expire(self, key, seconds):
        self._purge_expired()
        if key in self._data or key in self._sets:
            self._expires[key] = time.time() + int(seconds)
            return True
        return False

    def ping(self):
        return True

    def pipeline(self):
        return InMemoryPipeline(self)

    def dbsize(self):
        self._purge_expired()
        keys = set(self._data.keys()) | set(self._sets.keys())
        return len(keys)


class InMemoryPipeline:
    def __init__(self, client):
        self._client = client
        self._commands = []

    def setex(self, key, seconds, value):
        self._commands.append(("setex", key, seconds, value))

    def sadd(self, key, value):
        self._commands.append(("sadd", key, value))

    def expire(self, key, seconds):
        self._commands.append(("expire", key, seconds))

    def execute(self):
        results = []
        for cmd in self._commands:
            op = cmd[0]
            if op == "setex":
                _, key, seconds, value = cmd
                results.append(self._client.setex(key, seconds, value))
            elif op == "sadd":
                _, key, value = cmd
                results.append(self._client.sadd(key, value))
            elif op == "expire":
                _, key, seconds = cmd
                results.append(self._client.expire(key, seconds))
        self._commands.clear()
        return results


def get_redis():
    global _redis
    with _redis_lock:
        if _redis is not None:
            return _redis

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=5)
            client.ping()
            _redis = client
        except Exception as exc:
            logger.warning(
                f"⚠ Redis connection failed ({type(exc).__name__}): {exc}. Using in-memory fallback."
            )
            _redis = InMemoryRedis()

        return _redis


def publish(channel: str, message: str):
    client = get_redis()
    client.publish(channel, message)


def subscribe(channel: str):
    client = get_redis()
    pubsub = client.pubsub()
    pubsub.subscribe(channel)
    return pubsub
