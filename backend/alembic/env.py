import asyncio
import os
import logging
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from urllib.parse import urlparse, urlunparse

# Import your models here
from backend.models import *
from backend.utils.db import DATABASE_URL

logger = logging.getLogger("alembic.env")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url():
    url = DATABASE_URL
    if not url:
        return url

    # Preserve SQLite file URLs exactly (avoid urlunparse removing a slash)
    if url.startswith("sqlite"):
        return url

    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # asyncpg is picky about query params. Strip them from the URL and return
    # a cleaned URL without query parameters for engine creation.
    parsed = urlparse(url)
    return urlunparse(parsed._replace(query=""))


config.set_main_option("sqlalchemy.url", get_url())

target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=target_metadata, render_as_batch=True
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # Handle SSL for Render/Production if needed
    is_render = os.getenv("RENDER") == "true" or "render.com" in (DATABASE_URL or "")
    connect_args = {}
    if is_render:
        connect_args["ssl"] = "require"

    # Add any other required asyncpg params here. For sqlite, use the
    # DB driver's supported timeout option instead of asyncpg's
    # `command_timeout` which is invalid for sqlite connections.
    is_sqlite = (DATABASE_URL or "").startswith("sqlite")
    if is_sqlite:
        # `timeout` is accepted by sqlite3.connect
        connect_args["timeout"] = int(os.getenv("DB_CONNECT_TIMEOUT", "30"))
    else:
        connect_args["command_timeout"] = 60

    async_config = config.get_section(config.config_ini_section, {})

    connectable = async_engine_from_config(
        async_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
