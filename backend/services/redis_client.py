import os
import logging
import threading
import time
from typing import Optional

import redis
from backend.utils.redis_singleton import get_redis as get_redis_singleton

logger = logging.getLogger(__name__)
_redis = None
_redis_lock = threading.Lock()


class InMemoryRedis:
    def __init__(self):
        self._data = {}
        self._expires = {}
        self._sets = {}
        self._hashes = {}
        self._subscribers = {}
        self._pubsub_lock = threading.Lock()

    def _purge_expired(self):
        now = time.time()
        for key in list(self._expires.keys()):
            if self._expires.get(key) is not None and self._expires[key] <= now:
                self._data.pop(key, None)
                self._sets.pop(key, None)
                self._hashes.pop(key, None)
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
        return 1 if key in self._data or key in self._sets or key in self._hashes else 0

    def sadd(self, key, member):
        self._purge_expired()
        if key not in self._sets:
            self._sets[key] = set()
        self._sets[key].add(member)

    def srem(self, key, member):
        self._purge_expired()
        members = self._sets.get(key)
        if not members:
            return 0
        if member in members:
            members.remove(member)
            if not members:
                self._sets.pop(key, None)
            return 1
        return 0

    def smembers(self, key):
        self._purge_expired()
        return set(self._sets.get(key, set()))

    def hset(self, key, mapping=None, **kwargs):
        self._purge_expired()
        values = {}
        if mapping:
            values.update(mapping)
        if kwargs:
            values.update(kwargs)
        if key not in self._hashes:
            self._hashes[key] = {}
        for field, value in values.items():
            self._hashes[key][str(field)] = str(value)
        return len(values)

    def delete(self, *keys):
        self._purge_expired()
        deleted = 0
        for key in keys:
            removed = False
            if key in self._data:
                self._data.pop(key, None)
                removed = True
            if key in self._sets:
                self._sets.pop(key, None)
                removed = True
            if key in self._hashes:
                self._hashes.pop(key, None)
                removed = True
            self._expires.pop(key, None)
            if removed:
                deleted += 1
        return deleted

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
        keys = set(self._data.keys()) | set(self._sets.keys()) | set(self._hashes.keys())
        return len(keys)

    def publish(self, channel, message):
        with self._pubsub_lock:
            subscribers = list(self._subscribers.get(channel, []))

        for subscriber in subscribers:
            subscriber._enqueue(channel, message)

        return len(subscribers)

    def pubsub(self):
        return InMemoryPubSub(self)

    def _register_subscriber(self, channel, subscriber):
        with self._pubsub_lock:
            listeners = self._subscribers.setdefault(channel, [])
            if subscriber not in listeners:
                listeners.append(subscriber)

    def _unregister_subscriber(self, channel, subscriber):
        with self._pubsub_lock:
            listeners = self._subscribers.get(channel)
            if not listeners:
                return
            if subscriber in listeners:
                listeners.remove(subscriber)
            if not listeners:
                self._subscribers.pop(channel, None)


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

    def hset(self, key, mapping=None, **kwargs):
        self._commands.append(("hset", key, mapping, kwargs))

    def srem(self, key, value):
        self._commands.append(("srem", key, value))

    def delete(self, key):
        self._commands.append(("delete", key))

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
            elif op == "hset":
                _, key, mapping, kwargs = cmd
                results.append(self._client.hset(key, mapping=mapping, **kwargs))
            elif op == "srem":
                _, key, value = cmd
                results.append(self._client.srem(key, value))
            elif op == "delete":
                _, key = cmd
                results.append(self._client.delete(key))
        self._commands.clear()
        return results


class InMemoryPubSub:
    def __init__(self, client):
        self._client = client
        self._channels = set()
        self._messages = []
        self._messages_lock = threading.Lock()

    def subscribe(self, *channels):
        for channel in channels:
            self._channels.add(channel)
            self._client._register_subscriber(channel, self)

    def unsubscribe(self, *channels):
        target_channels = channels or tuple(self._channels)
        for channel in target_channels:
            if channel in self._channels:
                self._channels.remove(channel)
                self._client._unregister_subscriber(channel, self)

    def _enqueue(self, channel, message):
        with self._messages_lock:
            self._messages.append({"type": "message", "channel": channel, "data": message})

    def get_message(self, ignore_subscribe_messages=True, timeout: float = 0.0):
        end_time: Optional[float] = None
        if timeout and timeout > 0:
            end_time = time.time() + timeout

        while True:
            with self._messages_lock:
                if self._messages:
                    return self._messages.pop(0)

            if end_time is None:
                return None

            if time.time() >= end_time:
                return None

            time.sleep(0.01)

    def close(self):
        self.unsubscribe()


def get_redis():
    global _redis
    with _redis_lock:
        if _redis is not None:
            return _redis

        try:
            client = get_redis_singleton()
            _redis = client
            return _redis
        except Exception:
            logger.warning(
                "⚠ Redis singleton unavailable — using in-memory fallback."
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
