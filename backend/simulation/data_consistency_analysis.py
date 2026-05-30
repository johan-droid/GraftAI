"""
Data Consistency Analysis for Traffic Spikes

Analyzes data consistency issues under high load:
- Race condition detection
- Transaction isolation analysis
- Cache consistency issues
- Distributed system consistency
"""
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class ConsistencyIssueType(Enum):
    """Types of data consistency issues"""
    DUPLICATE_RECORDS = "duplicate_records"
    ORPHANED_RECORDS = "orphaned_records"
    STALE_DATA = "stale_data"
    RACE_CONDITIONS = "race_conditions"
    TRANSACTION_CONFLICTS = "transaction_conflicts"
    CACHE_INVALIDATION = "cache_invalidation"
    EVENTUAL_CONSISTENCY = "eventual_consistency"
    PARTITION_TOLERANCE = "partition_tolerance"

class IsolationLevel(Enum):
    """Database transaction isolation levels"""
    READ_UNCOMMITTED = "read_uncommitted"
    READ_COMMITTED = "read_committed"
    REPEATABLE_READ = "repeatable_read"
    SERIALIZABLE = "serializable"

@dataclass
class ConsistencyIssue:
    """Data consistency issue analysis"""
    issue_type: ConsistencyIssueType
    entity_type: str
    affected_records: int
    detection_time: datetime
    root_cause: str
    severity: str
    auto_recovery_possible: bool
    recovery_strategy: str
    prevention_strategy: str
    sample_records: list[dict[str, Any]]

@dataclass
class RaceCondition:
    """Race condition analysis"""
    resource: str
    concurrent_operations: int
    conflict_probability: float
    detected_conflicts: int
    affected_entities: list[str]
    mitigation_strategy: str

@dataclass
class TransactionConflict:
    """Transaction conflict analysis"""
    transaction_type: str
    isolation_level: IsolationLevel
    conflict_rate: float
    deadlock_count: int
    rollback_count: int
    affected_tables: list[str]
    recommended_isolation: IsolationLevel

class DataConsistencyAnalyzer:
    """Analyzes data consistency issues during traffic spikes"""

    def __init__(self):
        self.consistency_issues: list[ConsistencyIssue] = []
        self.race_conditions: list[RaceCondition] = []
        self.transaction_conflicts: list[TransactionConflict] = []
        self.cache_consistency_issues: list[dict[str, Any]] = []

    async def analyze_consistency_issues(self, db: AsyncSession, simulation_report: dict[str, Any]) -> dict[str, Any]:
        """Analyze data consistency issues from traffic spike simulation"""
        logger.info("Analyzing data consistency issues from traffic spike")
        duplicate_issues = await self._analyze_duplicate_records(db)
        orphaned_issues = await self._analyze_orphaned_records(db)
        race_conditions = await self._analyze_race_conditions(db, simulation_report)
        transaction_conflicts = await self._analyze_transaction_conflicts(db, simulation_report)
        cache_issues = await self._analyze_cache_consistency(simulation_report)
        stale_data_issues = await self._analyze_stale_data(db)
        return {"consistency_analysis": {"duplicate_records": [asdict(issue) for issue in duplicate_issues], "orphaned_records": [asdict(issue) for issue in orphaned_issues], "race_conditions": [asdict(rc) for rc in race_conditions], "transaction_conflicts": [asdict(tc) for tc in transaction_conflicts], "cache_consistency": cache_issues, "stale_data": [asdict(issue) for issue in stale_data_issues]}, "critical_issues": self._identify_critical_consistency_issues(), "recovery_strategies": self._generate_recovery_strategies(), "prevention_recommendations": self._generate_prevention_recommendations(), "monitoring_requirements": self._generate_monitoring_requirements()}

    async def _analyze_duplicate_records(self, db: AsyncSession) -> list[ConsistencyIssue]:
        """Analyze duplicate record issues"""
        duplicate_issues = []
        duplicate_bookings = await self._find_duplicate_bookings(db)
        if duplicate_bookings:
            issue = ConsistencyIssue(issue_type=ConsistencyIssueType.DUPLICATE_RECORDS, entity_type="booking", affected_records=len(duplicate_bookings), detection_time=datetime.now(UTC), root_cause="Concurrent booking creation without proper locking", severity="high", auto_recovery_possible=True, recovery_strategy="Merge duplicates and notify users", prevention_strategy="Implement unique constraints and distributed locking")
            duplicate_issues.append(issue)
        duplicate_users = await self._find_duplicate_users(db)
        if duplicate_users:
            issue = ConsistencyIssue(issue_type=ConsistencyIssueType.DUPLICATE_RECORDS, entity_type="user", affected_records=len(duplicate_users), detection_time=datetime.now(UTC), root_cause="Concurrent user registration without email uniqueness check", severity="critical", auto_recovery_possible=False, recovery_strategy="Manual review and merge of duplicate accounts", prevention_strategy="Implement unique email constraint at database level")
            duplicate_issues.append(issue)
        return duplicate_issues

    async def _analyze_orphaned_records(self, db: AsyncSession) -> list[ConsistencyIssue]:
        """Analyze orphaned record issues"""
        orphaned_issues = []
        orphaned_bookings = await self._find_orphaned_bookings(db)
        if orphaned_bookings:
            issue = ConsistencyIssue(issue_type=ConsistencyIssueType.ORPHANED_RECORDS, entity_type="booking", affected_records=len(orphaned_bookings), detection_time=datetime.now(UTC), root_cause="User deletion without cascade delete of bookings", severity="medium", auto_recovery_possible=True, recovery_strategy="Archive orphaned bookings or assign to system user", prevention_strategy="Implement proper foreign key constraints and cascade deletes")
            orphaned_issues.append(issue)
        orphaned_integrations = await self._find_orphaned_calendar_integrations(db)
        if orphaned_integrations:
            issue = ConsistencyIssue(issue_type=ConsistencyIssueType.ORPHANED_RECORDS, entity_type="calendar_integration", affected_records=len(orphaned_integrations), detection_time=datetime.now(UTC), root_cause="User deletion without cleanup of calendar integrations", severity="low", auto_recovery_possible=True, recovery_strategy="Delete orphaned integrations", prevention_strategy="Implement cascade delete for user-related data")
            orphaned_issues.append(issue)
        return orphaned_issues

    async def _analyze_race_conditions(self, db: AsyncSession, simulation_report: dict[str, Any]) -> list[RaceCondition]:
        """Analyze race condition issues"""
        race_conditions = []
        booking_race = await self._analyze_booking_race_conditions(db, simulation_report)
        if booking_race:
            race_conditions.append(booking_race)
        quota_race = await self._analyze_quota_race_conditions(db, simulation_report)
        if quota_race:
            race_conditions.append(quota_race)
        sync_race = await self._analyze_calendar_sync_race_conditions(db, simulation_report)
        if sync_race:
            race_conditions.append(sync_race)
        return race_conditions

    async def _analyze_transaction_conflicts(self, db: AsyncSession, simulation_report: dict[str, Any]) -> list[TransactionConflict]:
        """Analyze transaction conflict issues"""
        transaction_conflicts = []
        booking_conflicts = await self._analyze_booking_transaction_conflicts(db, simulation_report)
        if booking_conflicts:
            transaction_conflicts.append(booking_conflicts)
        user_conflicts = await self._analyze_user_transaction_conflicts(db, simulation_report)
        if user_conflicts:
            transaction_conflicts.append(user_conflicts)
        return transaction_conflicts

    async def _analyze_cache_consistency(self, simulation_report: dict[str, Any]) -> list[dict[str, Any]]:
        """Analyze cache consistency issues"""
        cache_issues = []
        bottlenecks = simulation_report.get("bottlenecks", [])
        cache_bottlenecks = [b for b in bottlenecks if "cache" in b.get("bottleneck_type", "").lower()]
        if cache_bottlenecks:
            cache_issues.append({"issue_type": "cache_invalidation", "description": "Cache invalidation failures during high load", "impact": "Stale data served to users", "affected_endpoints": ["/api/v1/bookings", "/api/v1/users/me"], "severity": "medium"})
        resource_usage = simulation_report.get("resource_usage", {})
        if resource_usage.get("cache", {}).get("max", 0) > 90:
            cache_issues.append({"issue_type": "cache_stampede", "description": "Cache stampede due to high concurrent requests", "impact": "Increased database load and response times", "affected_endpoints": ["/api/v1/bookings", "/api/v1/calendar"], "severity": "high"})
        return cache_issues

    async def _analyze_stale_data(self, db: AsyncSession) -> list[ConsistencyIssue]:
        """Analyze stale data issues"""
        stale_issues = []
        stale_quotas = await self._find_stale_quota_data(db)
        if stale_quotas:
            issue = ConsistencyIssue(issue_type=ConsistencyIssueType.STALE_DATA, entity_type="user_quota", affected_records=len(stale_quotas), detection_time=datetime.now(UTC), root_cause="Cache invalidation failures during high load", severity="medium", auto_recovery_possible=True, recovery_strategy="Force cache refresh and recalculate quotas", prevention_strategy="Implement cache warming and proper invalidation")
            stale_issues.append(issue)
        stale_sync = await self._find_stale_calendar_sync_data(db)
        if stale_sync:
            issue = ConsistencyIssue(issue_type=ConsistencyIssueType.STALE_DATA, entity_type="calendar_sync", affected_records=len(stale_sync), detection_time=datetime.now(UTC), root_cause="Calendar sync failures during high load", severity="low", auto_recovery_possible=True, recovery_strategy="Trigger manual calendar sync", prevention_strategy="Implement sync retry logic and exponential backoff")
            stale_issues.append(issue)
        return stale_issues

    async def _find_duplicate_bookings(self, db: AsyncSession) -> list[dict[str, Any]]:
        """Find duplicate booking records"""
        try:
            query = text("\n                SELECT user_id, start_time, title, COUNT(*) as duplicate_count\n                FROM bookings\n                WHERE start_time > NOW() - INTERVAL '1 hour'\n                GROUP BY user_id, start_time, title\n                HAVING COUNT(*) > 1\n            ")
            result = await db.execute(query)
            duplicates = result.fetchall()
            return [dict(row._mapping) for row in duplicates]
        except Exception as e:
            logger.exception("Error finding duplicate bookings: %s", e)
            return []

    async def _find_duplicate_users(self, db: AsyncSession) -> list[dict[str, Any]]:
        """Find duplicate user records"""
        try:
            query = text("\n                SELECT email, COUNT(*) as duplicate_count\n                FROM users\n                GROUP BY email\n                HAVING COUNT(*) > 1\n            ")
            result = await db.execute(query)
            duplicates = result.fetchall()
            return [dict(row._mapping) for row in duplicates]
        except Exception as e:
            logger.exception("Error finding duplicate users: %s", e)
            return []

    async def _find_orphaned_bookings(self, db: AsyncSession) -> list[dict[str, Any]]:
        """Find orphaned booking records"""
        try:
            query = text("\n                SELECT b.id, b.user_id, b.title\n                FROM bookings b\n                LEFT JOIN users u ON b.user_id = u.id\n                WHERE u.id IS NULL\n                LIMIT 100\n            ")
            result = await db.execute(query)
            orphaned = result.fetchall()
            return [dict(row._mapping) for row in orphaned]
        except Exception as e:
            logger.exception("Error finding orphaned bookings: %s", e)
            return []

    async def _find_orphaned_calendar_integrations(self, db: AsyncSession) -> list[dict[str, Any]]:
        """Find orphaned calendar integration records"""
        try:
            query = text("\n                SELECT ci.id, ci.user_id, ci.provider\n                FROM calendar_integrations ci\n                LEFT JOIN users u ON ci.user_id = u.id\n                WHERE u.id IS NULL\n                LIMIT 100\n            ")
            result = await db.execute(query)
            orphaned = result.fetchall()
            return [dict(row._mapping) for row in orphaned]
        except Exception as e:
            logger.exception("Error finding orphaned calendar integrations: %s", e)
            return []

    async def _analyze_booking_race_conditions(self, db: AsyncSession, simulation_report: dict[str, Any]) -> RaceCondition | None:
        """Analyze booking creation race conditions"""
        try:
            query = text("\n                SELECT user_id, COUNT(*) as concurrent_bookings\n                FROM bookings\n                WHERE created_at > NOW() - INTERVAL '1 minute'\n                GROUP BY user_id\n                HAVING COUNT(*) > 1\n            ")
            result = await db.execute(query)
            concurrent_bookings = result.fetchall()
            if concurrent_bookings:
                total_concurrent = sum(row.concurrent_bookings for row in concurrent_bookings)
                conflict_probability = min(0.95, total_concurrent / 100)
                return RaceCondition(resource="booking_creation", concurrent_operations=total_concurrent, conflict_probability=conflict_probability, detected_conflicts=len(concurrent_bookings), affected_entities=["booking"], mitigation_strategy="Implement distributed locking and idempotency keys")
            return None
        except Exception as e:
            logger.exception("Error analyzing booking race conditions: %s", e)
            return None

    async def _analyze_quota_race_conditions(self, db: AsyncSession, simulation_report: dict[str, Any]) -> RaceCondition | None:
        """Analyze quota update race conditions"""
        try:
            query = text("\n                SELECT user_id, COUNT(*) as rapid_updates\n                FROM users\n                WHERE updated_at > NOW() - INTERVAL '1 minute'\n                GROUP BY user_id\n                HAVING COUNT(*) > 5\n            ")
            result = await db.execute(query)
            rapid_updates = result.fetchall()
            if rapid_updates:
                total_rapid = sum(row.rapid_updates for row in rapid_updates)
                conflict_probability = min(0.8, total_rapid / 50)
                return RaceCondition(resource="quota_updates", concurrent_operations=total_rapid, conflict_probability=conflict_probability, detected_conflicts=len(rapid_updates), affected_entities=["user_quota"], mitigation_strategy="Implement atomic quota operations with proper locking")
            return None
        except Exception as e:
            logger.exception("Error analyzing quota race conditions: %s", e)
            return None

    async def _analyze_calendar_sync_race_conditions(self, db: AsyncSession, simulation_report: dict[str, Any]) -> RaceCondition | None:
        """Analyze calendar sync race conditions"""
        try:
            query = text("\n                SELECT user_id, COUNT(*) as concurrent_syncs\n                FROM calendar_integrations\n                WHERE last_sync_at > NOW() - INTERVAL '1 minute'\n                GROUP BY user_id\n                HAVING COUNT(*) > 1\n            ")
            result = await db.execute(query)
            concurrent_syncs = result.fetchall()
            if concurrent_syncs:
                total_concurrent = sum(row.concurrent_syncs for row in concurrent_syncs)
                conflict_probability = min(0.7, total_concurrent / 20)
                return RaceCondition(resource="calendar_sync", concurrent_operations=total_concurrent, conflict_probability=conflict_probability, detected_conflicts=len(concurrent_syncs), affected_entities=["calendar_integration"], mitigation_strategy="Implement sync queuing and deduplication")
            return None
        except Exception as e:
            logger.exception("Error analyzing calendar sync race conditions: %s", e)
            return None

    async def _analyze_booking_transaction_conflicts(self, db: AsyncSession, simulation_report: dict[str, Any]) -> TransactionConflict | None:
        """Analyze booking transaction conflicts"""
        try:
            total_requests = simulation_report.get("simulation_summary", {}).get("total_requests", 0)
            estimated_conflict_rate = min(0.1, total_requests / 10000)
            return TransactionConflict(transaction_type="booking_creation", isolation_level=IsolationLevel.READ_COMMITTED, conflict_rate=estimated_conflict_rate, deadlock_count=int(total_requests * 0.001), rollback_count=int(total_requests * 0.005), affected_tables=["bookings", "users"], recommended_isolation=IsolationLevel.SERIALIZABLE)
        except Exception as e:
            logger.exception("Error analyzing booking transaction conflicts: %s", e)
            return None

    async def _analyze_user_transaction_conflicts(self, db: AsyncSession, simulation_report: dict[str, Any]) -> TransactionConflict | None:
        """Analyze user update transaction conflicts"""
        try:
            total_requests = simulation_report.get("simulation_summary", {}).get("total_requests", 0)
            estimated_conflict_rate = min(0.05, total_requests / 20000)
            return TransactionConflict(transaction_type="user_update", isolation_level=IsolationLevel.READ_COMMITTED, conflict_rate=estimated_conflict_rate, deadlock_count=int(total_requests * 0.0005), rollback_count=int(total_requests * 0.002), affected_tables=["users"], recommended_isolation=IsolationLevel.REPEATABLE_READ)
        except Exception as e:
            logger.exception("Error analyzing user transaction conflicts: %s", e)
            return None

    async def _find_stale_quota_data(self, db: AsyncSession) -> list[dict[str, Any]]:
        """Find stale quota data"""
        try:
            query = text("\n                SELECT id, email, quota_reset_at\n                FROM users\n                WHERE quota_reset_at < NOW() - INTERVAL '1 day'\n                LIMIT 100\n            ")
            result = await db.execute(query)
            stale_quotas = result.fetchall()
            return [dict(row._mapping) for row in stale_quotas]
        except Exception as e:
            logger.exception("Error finding stale quota data: %s", e)
            return []

    async def _find_stale_calendar_sync_data(self, db: AsyncSession) -> list[dict[str, Any]]:
        """Find stale calendar sync data"""
        try:
            query = text("\n                SELECT id, user_id, provider, last_sync_at\n                FROM calendar_integrations\n                WHERE last_sync_at < NOW() - INTERVAL '1 hour'\n                AND sync_status = 'active'\n                LIMIT 100\n            ")
            result = await db.execute(query)
            stale_sync = result.fetchall()
            return [dict(row._mapping) for row in stale_sync]
        except Exception as e:
            logger.exception("Error finding stale calendar sync data: %s", e)
            return []

    def _identify_critical_consistency_issues(self) -> list[str]:
        """Identify critical consistency issues that need immediate attention"""
        critical_issues = []
        for issue in self.consistency_issues:
            if issue.severity in ["critical", "high"] and (not issue.auto_recovery_possible):
                critical_issues.append(f"{issue.entity_type}: {issue.issue_type.value}")
        for race_condition in self.race_conditions:
            if race_condition.conflict_probability > 0.5:
                critical_issues.append(f"Race condition: {race_condition.resource}")
        return critical_issues

    def _generate_recovery_strategies(self) -> dict[str, list[str]]:
        """Generate recovery strategies for different consistency issues"""
        return {"duplicate_records": ["Implement unique constraints at database level", "Add idempotency keys for API operations", "Implement data deduplication jobs", "Manual review and merge of duplicates"], "orphaned_records": ["Implement proper foreign key constraints", "Add cascade delete rules", "Run periodic cleanup jobs", "Archive orphaned records"], "race_conditions": ["Implement distributed locking mechanisms", "Add idempotency to all write operations", "Use optimistic locking with version numbers", "Implement request deduplication"], "cache_consistency": ["Implement cache invalidation strategies", "Add cache warming mechanisms", "Use cache stampede protection", "Implement cache consistency checks"], "transaction_conflicts": ["Use appropriate isolation levels", "Implement retry logic for conflicts", "Add deadlock detection and handling", "Use optimistic concurrency control"]}

    def _generate_prevention_recommendations(self) -> list[str]:
        """Generate prevention recommendations"""
        return ["Implement database constraints and foreign keys", "Use distributed transactions for critical operations", "Implement proper cache invalidation strategies", "Add idempotency to all API endpoints", "Use optimistic locking with version numbers", "Implement circuit breakers for external services", "Add comprehensive data validation", "Implement audit logging for data changes", "Use message queues for async operations", "Implement proper error handling and retry logic", "Add data consistency checks and validation", "Implement proper session management", "Use database connection pooling with proper limits", "Implement proper timeout handling", "Add monitoring and alerting for consistency issues"]

    def _generate_monitoring_requirements(self) -> list[str]:
        """Generate monitoring requirements for data consistency"""
        return ["Monitor duplicate record creation", "Track orphaned record counts", "Monitor race condition indicators", "Track transaction conflict rates", "Monitor cache hit/miss ratios", "Track stale data detection", "Monitor database lock contention", "Track API response times under load", "Monitor error rates by endpoint", "Track concurrent operation counts", "Monitor database connection pool usage", "Track cache invalidation latency", "Monitor message queue depth", "Track background job failure rates", "Monitor data integrity checks"]
consistency_analyzer = DataConsistencyAnalyzer()

async def analyze_data_consistency(db: AsyncSession, simulation_report: dict[str, Any]) -> dict[str, Any]:
    """Analyze data consistency issues from traffic spike simulation"""
    return await consistency_analyzer.analyze_consistency_issues(db, simulation_report)
