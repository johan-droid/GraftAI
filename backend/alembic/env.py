import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine

from alembic import context

# Ensure backend is in path
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import the SQLAlchemy models and existing engine logic
from backend.models.tables import Base
from backend.utils.db import DATABASE_URL

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Re-use the engine creation logic from utils.db to handle asyncpg SSL/params
    from backend.utils.db import engine as existing_engine
    
    if existing_engine:
        connectable = existing_engine
    else:
        # Fallback if engine wasn't initialized
        from sqlalchemy.ext.asyncio import create_async_engine
        connectable = create_async_engine(DATABASE_URL)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
