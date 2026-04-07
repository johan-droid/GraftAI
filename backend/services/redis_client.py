import asyncio
import logging
import time
from typing import Optional

from backend.utils.redis_singleton import get_redis as get_redis_singleton

logger = logging.getLogger(__name__)

class InMemoryRedis:
    def __init__(self):
        self._data = {}
        self._expires = {}
        self._sets = {}
        self._hashes = {}

    def _purge_expired(self):
        now = time.time()
        for key in list(self._expires.keys()):
            if self._expires.get(key) is not None and self._expires[key] <= now:
                self._data.pop(key, None)
                self._sets.pop(key, None)
                self._hashes.pop(key, None)
                self._expires.pop(key, None)

    async def get(self, key):
        self._purge_expired()
        return self._data.get(key)

    async def set(self, key, value, ex=None):
        self._purge_expired()
        self._data[key] = str(value)
        if ex is not None:
            self._expires[key] = time.time() + int(ex)

    async def setex(self, key, seconds, value):
        await self.set(key, value, ex=seconds)

    async def exists(self, key):
        self._purge_expired()
        return 1 if key in self._data or key in self._sets or key in self._hashes else 0

    async def sadd(self, key, member):
        self._purge_expired()
        if key not in self._sets:
            self._sets[key] = set()
        self._sets[key].add(member)

    async def srem(self, key, member):
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

    async def smembers(self, key):
        self._purge_expired()
        return set(self._sets.get(key, set()))

    async def hset(self, key, mapping=None, **kwargs):
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

    async def delete(self, *keys):
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

    async def incr(self, key):
        self._purge_expired()
        value = int(self._data.get(key, "0"))
        value += 1
        self._data[key] = str(value)
        return value

    async def expire(self, key, seconds):
        self._purge_expired()
        if key in self._data or key in self._sets:
            self._expires[key] = time.time() + int(seconds)
            return True
        return False

    async def ping(self):
        return True

    def pubsub(self):
        return InMemoryPubSub(self)

    async def publish(self, channel, message):
        # In-memory publish is a no-op for now unless we implement a dispatcher
        pass

class InMemoryPubSub:
    def __init__(self, client):
        self.client = client
        self.channels = set()

    async def subscribe(self, *channels):
        for c in channels:
            self.channels.add(c)

    async def unsubscribe(self, *channels):
        for c in channels:
            self.channels.discard(c)

    async def get_message(self, ignore_subscribe_messages=False, timeout=0):
        if timeout > 0:
            await asyncio.sleep(timeout)
        return None

    async def close(self):
        pass

async def get_redis():
    try:
        client = await get_redis_singleton()
        return client
    except Exception:
        logger.warning(
            "⚠ Redis singleton unavailable — using in-memory fallback."
        )
        return InMemoryRedis()

async def publish(channel: str, message: str):
    client = await get_redis()
    await client.publish(channel, message)

async def subscribe(channel: str):
    client = await get_redis()
    pubsub = client.pubsub()
    await pubsub.subscribe(channel)
    return pubsub
