import asyncio
import logging
from typing import Any

from backend.utils.cache import get_redis_client

logger = logging.getLogger(__name__)
QUEUE_KEY_PATTERN = "arq:queue:*"
FAILED_KEY_PATTERN = "arq:failed*"
SCAN_BATCH_SIZE = 100


def _decode_key(key: Any) -> str:
    if isinstance(key, bytes):
        return key.decode("utf-8", errors="replace")
    return str(key)


async def get_queue_depths() -> dict[str, int]:
    redis = await get_redis_client()
    if not redis:
        logger.warning("Queue monitoring disabled: no Redis client available.")
        return {}

    depths: dict[str, int] = {}
    cursor = 0

    while True:
        cursor, keys = await redis.scan(
            cursor=cursor, match=QUEUE_KEY_PATTERN, count=SCAN_BATCH_SIZE
        )
        for key in keys:
            key_name = _decode_key(key)
            try:
                queue_length = await redis.llen(key)
            except Exception as exc:
                logger.error("Unable to read queue length for %s: %s", key_name, exc)
                queue_length = -1
            depths[key_name] = queue_length

        if cursor in (0, "0", b"0"):
            break

    return depths


async def get_failed_job_count() -> int:
    redis = await get_redis_client()
    if not redis:
        return 0

    count = 0
    cursor = 0

    while True:
        cursor, keys = await redis.scan(
            cursor=cursor, match=FAILED_KEY_PATTERN, count=SCAN_BATCH_SIZE
        )
        count += len(keys)
        if cursor in (0, "0", b"0"):
            break

    return count


async def _monitor_loop(
    interval_seconds: int = 60, warning_threshold: int = 250
) -> None:
    while True:
        try:
            depths = await get_queue_depths()
            failed_count = await get_failed_job_count()

            if depths:
                total = sum(max(0, value) for value in depths.values())
                max_depth = max(depths.values())
                logger.info(
                    "Queue health - total backlog=%d, max queue depth=%d, queues=%s",
                    total,
                    max_depth,
                    depths,
                )
                if max_depth >= warning_threshold:
                    logger.warning(
                        "High queue backlog detected (threshold=%d): %s",
                        warning_threshold,
                        depths,
                    )
            else:
                logger.debug("Queue monitoring found no ARQ queue keys.")

            if failed_count:
                logger.warning("Detected %d failed queue job key(s).", failed_count)

        except Exception as exc:
            logger.error("Queue monitoring encountered an error: %s", exc)

        await asyncio.sleep(interval_seconds)


def start_queue_monitoring(
    interval_seconds: int = 60, warning_threshold: int = 250
) -> asyncio.Task[None]:
    task = asyncio.create_task(_monitor_loop(interval_seconds, warning_threshold))
    logger.info(
        "Started queue monitoring task with interval=%s seconds.", interval_seconds
    )
    return task
