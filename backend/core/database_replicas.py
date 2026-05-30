"""
Database Read Replicas and Connection Pooling Implementation

Provides scalable database architecture with:
- Read replicas for query distribution
- Connection pooling for performance
- Automatic failover and load balancing
- Health monitoring and metrics
"""
import asyncio
import logging
import random
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)

class ReplicaRole(Enum):
    """Database replica roles"""
    PRIMARY = "primary"
    REPLICA = "replica"
    STANDBY = "standby"

class ConnectionPoolStatus(Enum):
    """Connection pool status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    name: str
    connection_url: str
    role: ReplicaRole
    max_connections: int = 20
    min_connections: int = 5
    connection_timeout: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    read_only: bool = False
    weight: int = 1
    health_check_interval: int = 30

@dataclass
class PoolMetrics:
    """Connection pool metrics"""
    total_connections: int
    active_connections: int
    idle_connections: int
    overflow_connections: int
    checked_in_connections: int
    checked_out_connections: int
    invalid_connections: int
    creation_time: datetime

class DatabaseReplicaManager:
    """Manages database replicas and connection pooling"""

    def __init__(self):
        self.replicas: dict[str, DatabaseConfig] = {}
        self.engines: dict[str, Any] = {}
        self.session_makers: dict[str, async_sessionmaker] = {}
        self.pool_metrics: dict[str, PoolMetrics] = {}
        self.health_status: dict[str, ConnectionPoolStatus] = {}
        self.last_health_check: dict[str, datetime] = {}
        self.read_replica_weights: dict[str, int] = {}
        self.redis_client: aioredis.Redis | None = None
        self.health_check_task: asyncio.Task | None = None
        self.metrics_task: asyncio.Task | None = None

    async def initialize(self, configs: list[DatabaseConfig], redis_url: str | None=None):
        """Initialize database replicas and connection pools"""
        logger.info("Initializing %s database replicas", len(configs))
        if redis_url:
            try:
                self.redis_client = await aioredis.from_url(redis_url)
                logger.info("Redis connection established for replica coordination")
            except Exception as e:
                logger.exception("Failed to connect to Redis: %s", e)
        for config in configs:
            await self._create_replica_pool(config)
        await self._start_health_monitoring()
        await self._start_metrics_collection()
        logger.info("Database replica manager initialized successfully")

    async def _create_replica_pool(self, config: DatabaseConfig):
        """Create connection pool for database replica"""
        try:
            engine = create_async_engine(config.connection_url, pool_size=config.max_connections, max_overflow=config.max_connections // 2, pool_timeout=config.pool_timeout, pool_recycle=config.pool_recycle, pool_pre_ping=config.pool_pre_ping, echo=False, future=True)
            session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            self.engines[config.name] = engine
            self.session_makers[config.name] = session_maker
            self.replicas[config.name] = config
            self.health_status[config.name] = ConnectionPoolStatus.HEALTHY
            self.last_health_check[config.name] = datetime.now(UTC)
            if config.role == ReplicaRole.REPLICA:
                self.read_replica_weights[config.name] = config.weight
            self.pool_metrics[config.name] = PoolMetrics(total_connections=0, active_connections=0, idle_connections=0, overflow_connections=0, checked_in_connections=0, checked_out_connections=0, invalid_connections=0, creation_time=datetime.now(UTC))
            logger.info("Created connection pool for %s (%s)", config.name, config.role.value)
        except Exception as e:
            logger.exception("Failed to create pool for %s: %s", config.name, e)
            self.health_status[config.name] = ConnectionPoolStatus.UNHEALTHY

    async def get_primary_session(self) -> AsyncSession:
        """Get session for primary database (write operations)"""
        primary_replicas = [name for name, config in self.replicas.items() if config.role == ReplicaRole.PRIMARY]
        if not primary_replicas:
            msg = "No primary database configured"
            raise RuntimeError(msg)
        primary_name = primary_replicas[0]
        if self.health_status[primary_name] != ConnectionPoolStatus.HEALTHY:
            for name in primary_replicas[1:]:
                if self.health_status[name] == ConnectionPoolStatus.HEALTHY:
                    primary_name = name
                    break
            else:
                msg = "No healthy primary database available"
                raise RuntimeError(msg)
        session_maker = self.session_makers[primary_name]
        return session_maker()

    async def get_read_session(self) -> AsyncSession:
        """Get session for read database (read operations)"""
        read_replicas = [name for name, config in self.replicas.items() if config.role in [ReplicaRole.REPLICA, ReplicaRole.PRIMARY] and (not config.read_only)]
        if not read_replicas:
            return await self.get_primary_session()
        healthy_replicas = [name for name in read_replicas if self.health_status[name] == ConnectionPoolStatus.HEALTHY]
        if not healthy_replicas:
            return await self.get_primary_session()
        selected_replica = self._select_weighted_replica(healthy_replicas)
        session_maker = self.session_makers[selected_replica]
        return session_maker()

    def _select_weighted_replica(self, replicas: list[str]) -> str:
        """Select replica based on weights"""
        if not self.read_replica_weights:
            return random.choice(replicas)
        total_weight = sum(self.read_replica_weights.get(name, 1) for name in replicas)
        if total_weight == 0:
            return random.choice(replicas)
        rand = random.uniform(0, total_weight)
        current_weight = 0
        for name in replicas:
            current_weight += self.read_replica_weights.get(name, 1)
            if rand <= current_weight:
                return name
        return replicas[0]

    @asynccontextmanager
    async def get_session(self, read_only: bool=False):
        """Get database session with automatic cleanup"""
        if read_only:
            session = await self.get_read_session()
        else:
            session = await self.get_primary_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def _start_health_monitoring(self):
        """Start health monitoring for all replicas"""
        self.health_check_task = asyncio.create_task(self._health_check_loop())

    async def _health_check_loop(self):
        """Health monitoring loop"""
        while True:
            try:
                await self._check_all_replicas_health()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Health check error: %s", e)
                await asyncio.sleep(60)

    async def _check_all_replicas_health(self):
        """Check health of all replicas"""
        tasks = []
        for name in self.replicas:
            tasks.append(self._check_replica_health(name))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_replica_health(self, replica_name: str):
        """Check health of specific replica"""
        self.replicas[replica_name]
        engine = self.engines[replica_name]
        try:
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()
            old_status = self.health_status[replica_name]
            self.health_status[replica_name] = ConnectionPoolStatus.HEALTHY
            self.last_health_check[replica_name] = datetime.now(UTC)
            if old_status != ConnectionPoolStatus.HEALTHY:
                logger.info("Replica %s recovered to healthy status", replica_name)
                if self.redis_client:
                    await self.redis_client.hset("replica_health", replica_name, "healthy")
        except Exception as e:
            logger.exception("Health check failed for %s: %s", replica_name, e)
            old_status = self.health_status[replica_name]
            self.health_status[replica_name] = ConnectionPoolStatus.UNHEALTHY
            self.last_health_check[replica_name] = datetime.now(UTC)
            if old_status != ConnectionPoolStatus.UNHEALTHY:
                logger.warning("Replica %s marked as unhealthy", replica_name)
                if self.redis_client:
                    await self.redis_client.hset("replica_health", replica_name, "unhealthy")

    async def _start_metrics_collection(self):
        """Start metrics collection"""
        self.metrics_task = asyncio.create_task(self._metrics_loop())

    async def _metrics_loop(self):
        """Metrics collection loop"""
        while True:
            try:
                await self._collect_pool_metrics()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Metrics collection error: %s", e)
                await asyncio.sleep(120)

    async def _collect_pool_metrics(self):
        """Collect connection pool metrics"""
        for name, engine in self.engines.items():
            try:
                pool = engine.pool
                metrics = PoolMetrics(total_connections=pool.size(), active_connections=len(pool._pool.queue), idle_connections=pool.checkedin(), overflow_connections=pool.overflow(), checked_in_connections=pool.checkedin(), checked_out_connections=pool.checkedout(), invalid_connections=pool.invalid(), creation_time=datetime.now(UTC))
                self.pool_metrics[name] = metrics
                if self.redis_client:
                    await self.redis_client.hset("pool_metrics", name, json.dumps(asdict(metrics), default=str))
            except Exception as e:
                logger.exception("Failed to collect metrics for %s: %s", name, e)

    async def get_replica_status(self) -> dict[str, Any]:
        """Get status of all replicas"""
        status = {}
        for name, config in self.replicas.items():
            metrics = self.pool_metrics.get(name)
            health = self.health_status.get(name)
            last_check = self.last_health_check.get(name)
            status[name] = {"role": config.role.value, "connection_url": config.connection_url, "max_connections": config.max_connections, "health_status": health.value if health else "unknown", "last_health_check": last_check.isoformat() if last_check else None, "metrics": asdict(metrics) if metrics else None}
        return status

    async def failover_to_replica(self, failed_primary: str) -> bool:
        """Failover to replica when primary fails"""
        logger.warning("Initiating failover from %s", failed_primary)
        healthy_replicas = [name for name, status in self.health_status.items() if status == ConnectionPoolStatus.HEALTHY and name != failed_primary]
        if not healthy_replicas:
            logger.error("No healthy replicas available for failover")
            return False
        new_primary = healthy_replicas[0]
        old_config = self.replicas[new_primary]
        new_config = DatabaseConfig(name=old_config.name, connection_url=old_config.connection_url, role=ReplicaRole.PRIMARY, max_connections=old_config.max_connections, min_connections=old_config.min_connections, connection_timeout=old_config.connection_timeout, pool_timeout=old_config.pool_timeout, pool_recycle=old_config.pool_recycle, pool_pre_ping=old_config.pool_pre_ping, read_only=False, weight=old_config.weight)
        self.replicas[new_primary] = new_config
        logger.info("Promoted %s to primary role", new_primary)
        if self.redis_client:
            await self.redis_client.hset("replica_roles", new_primary, "primary")
            await self.redis_client.hset("replica_roles", failed_primary, "failed")
        return True

    async def add_replica(self, config: DatabaseConfig):
        """Add new replica dynamically"""
        await self._create_replica_pool(config)
        logger.info("Added new replica: %s", config.name)

    async def remove_replica(self, replica_name: str):
        """Remove replica"""
        if replica_name in self.engines:
            await self.engines[replica_name].dispose()
            del self.engines[replica_name]
            del self.session_makers[replica_name]
            del self.replicas[replica_name]
            del self.health_status[replica_name]
            del self.last_health_check[replica_name]
            del self.pool_metrics[replica_name]
            if replica_name in self.read_replica_weights:
                del self.read_replica_weights[replica_name]
            logger.info("Removed replica: %s", replica_name)

    async def close_all_connections(self):
        """Close all database connections"""
        logger.info("Closing all database connections")
        if self.health_check_task:
            self.health_check_task.cancel()
        if self.metrics_task:
            self.metrics_task.cancel()
        for engine in self.engines.values():
            await engine.dispose()
        if self.redis_client:
            await self.redis_client.close()
        self.engines.clear()
        self.session_makers.clear()
        self.replicas.clear()
        self.health_status.clear()
        self.last_health_check.clear()
        self.pool_metrics.clear()
        self.read_replica_weights.clear()
        logger.info("All database connections closed")
replica_manager = DatabaseReplicaManager()

def get_replica_manager() -> DatabaseReplicaManager:
    """Get global replica manager instance"""
    return replica_manager

async def get_db_session(read_only: bool=False) -> AsyncSession:
    """Get database session with replica routing"""
    manager = get_replica_manager()
    if read_only:
        return await manager.get_read_session()
    return await manager.get_primary_session()

async def get_read_db_session() -> AsyncSession:
    """Get read-only database session"""
    return await get_db_session(read_only=True)

async def get_write_db_session() -> AsyncSession:
    """Get write database session"""
    return await get_db_session(read_only=False)

@asynccontextmanager
async def database_session(read_only: bool=False):
    """Context manager for database operations"""
    manager = get_replica_manager()
    async with manager.get_session(read_only=read_only) as session:
        yield session

async def initialize_database_replicas(configs: list[DatabaseConfig], redis_url: str | None=None):
    """Initialize database replicas with configurations"""
    manager = get_replica_manager()
    await manager.initialize(configs, redis_url)
