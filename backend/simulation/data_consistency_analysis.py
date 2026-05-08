"""
Data Consistency Analysis for Traffic Spikes

Analyzes data consistency issues under high load:
- Race condition detection
- Transaction isolation analysis
- Cache consistency issues
- Distributed system consistency
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

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
    sample_records: List[Dict[str, Any]]


@dataclass
class RaceCondition:
    """Race condition analysis"""
    resource: str
    concurrent_operations: int
    conflict_probability: float
    detected_conflicts: int
    affected_entities: List[str]
    mitigation_strategy: str


@dataclass
class TransactionConflict:
    """Transaction conflict analysis"""
    transaction_type: str
    isolation_level: IsolationLevel
    conflict_rate: float
    deadlock_count: int
    rollback_count: int
    affected_tables: List[str]
    recommended_isolation: IsolationLevel


class DataConsistencyAnalyzer:
    """Analyzes data consistency issues during traffic spikes"""
    
    def __init__(self):
        self.consistency_issues: List[ConsistencyIssue] = []
        self.race_conditions: List[RaceCondition] = []
        self.transaction_conflicts: List[TransactionConflict] = []
        self.cache_consistency_issues: List[Dict[str, Any]] = []
        
    async def analyze_consistency_issues(self, db: AsyncSession, simulation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data consistency issues from traffic spike simulation"""
        
        logger.info("Analyzing data consistency issues from traffic spike")
        
        # Analyze duplicate records
        duplicate_issues = await self._analyze_duplicate_records(db)
        
        # Analyze orphaned records
        orphaned_issues = await self._analyze_orphaned_records(db)
        
        # Analyze race conditions
        race_conditions = await self._analyze_race_conditions(db, simulation_report)
        
        # Analyze transaction conflicts
        transaction_conflicts = await self._analyze_transaction_conflicts(db, simulation_report)
        
        # Analyze cache consistency
        cache_issues = await self._analyze_cache_consistency(simulation_report)
        
        # Analyze stale data issues
        stale_data_issues = await self._analyze_stale_data(db)
        
        # Generate consistency report
        report = {
            "consistency_analysis": {
                "duplicate_records": [asdict(issue) for issue in duplicate_issues],
                "orphaned_records": [asdict(issue) for issue in orphaned_issues],
                "race_conditions": [asdict(rc) for rc in race_conditions],
                "transaction_conflicts": [asdict(tc) for tc in transaction_conflicts],
                "cache_consistency": cache_issues,
                "stale_data": [asdict(issue) for issue in stale_data_issues]
            },
            "critical_issues": self._identify_critical_consistency_issues(),
            "recovery_strategies": self._generate_recovery_strategies(),
            "prevention_recommendations": self._generate_prevention_recommendations(),
            "monitoring_requirements": self._generate_monitoring_requirements()
        }
        
        return report
    
    async def _analyze_duplicate_records(self, db: AsyncSession) -> List[ConsistencyIssue]:
        """Analyze duplicate record issues"""
        duplicate_issues = []
        
        # Check for duplicate bookings
        duplicate_bookings = await self._find_duplicate_bookings(db)
        if duplicate_bookings:
            issue = ConsistencyIssue(
                issue_type=ConsistencyIssueType.DUPLICATE_RECORDS,
                entity_type="booking",
                affected_records=len(duplicate_bookings),
                detection_time=datetime.now(timezone.utc),
                root_cause="Concurrent booking creation without proper locking",
                severity="high",
                auto_recovery_possible=True,
                recovery_strategy="Merge duplicates and notify users",
                prevention_strategy="Implement unique constraints and distributed locking"
            )
            duplicate_issues.append(issue)
        
        # Check for duplicate users
        duplicate_users = await self._find_duplicate_users(db)
        if duplicate_users:
            issue = ConsistencyIssue(
                issue_type=ConsistencyIssueType.DUPLICATE_RECORDS,
                entity_type="user",
                affected_records=len(duplicate_users),
                detection_time=datetime.now(timezone.utc),
                root_cause="Concurrent user registration without email uniqueness check",
                severity="critical",
                auto_recovery_possible=False,
                recovery_strategy="Manual review and merge of duplicate accounts",
                prevention_strategy="Implement unique email constraint at database level"
            )
            duplicate_issues.append(issue)
        
        return duplicate_issues
    
    async def _analyze_orphaned_records(self, db: AsyncSession) -> List[ConsistencyIssue]:
        """Analyze orphaned record issues"""
        orphaned_issues = []
        
        # Check for orphaned bookings (bookings without valid users)
        orphaned_bookings = await self._find_orphaned_bookings(db)
        if orphaned_bookings:
            issue = ConsistencyIssue(
                issue_type=ConsistencyIssueType.ORPHANED_RECORDS,
                entity_type="booking",
                affected_records=len(orphaned_bookings),
                detection_time=datetime.now(timezone.utc),
                root_cause="User deletion without cascade delete of bookings",
                severity="medium",
                auto_recovery_possible=True,
                recovery_strategy="Archive orphaned bookings or assign to system user",
                prevention_strategy="Implement proper foreign key constraints and cascade deletes"
            )
            orphaned_issues.append(issue)
        
        # Check for orphaned calendar integrations
        orphaned_integrations = await self._find_orphaned_calendar_integrations(db)
        if orphaned_integrations:
            issue = ConsistencyIssue(
                issue_type=ConsistencyIssueType.ORPHANED_RECORDS,
                entity_type="calendar_integration",
                affected_records=len(orphaned_integrations),
                detection_time=datetime.now(timezone.utc),
                root_cause="User deletion without cleanup of calendar integrations",
                severity="low",
                auto_recovery_possible=True,
                recovery_strategy="Delete orphaned integrations",
                prevention_strategy="Implement cascade delete for user-related data"
            )
            orphaned_issues.append(issue)
        
        return orphaned_issues
    
    async def _analyze_race_conditions(self, db: AsyncSession, simulation_report: Dict[str, Any]) -> List[RaceCondition]:
        """Analyze race condition issues"""
        race_conditions = []
        
        # Analyze booking creation race conditions
        booking_race = await self._analyze_booking_race_conditions(db, simulation_report)
        if booking_race:
            race_conditions.append(booking_race)
        
        # Analyze quota update race conditions
        quota_race = await self._analyze_quota_race_conditions(db, simulation_report)
        if quota_race:
            race_conditions.append(quota_race)
        
        # Analyze calendar sync race conditions
        sync_race = await self._analyze_calendar_sync_race_conditions(db, simulation_report)
        if sync_race:
            race_conditions.append(sync_race)
        
        return race_conditions
    
    async def _analyze_transaction_conflicts(self, db: AsyncSession, simulation_report: Dict[str, Any]) -> List[TransactionConflict]:
        """Analyze transaction conflict issues"""
        transaction_conflicts = []
        
        # Analyze booking transaction conflicts
        booking_conflicts = await self._analyze_booking_transaction_conflicts(db, simulation_report)
        if booking_conflicts:
            transaction_conflicts.append(booking_conflicts)
        
        # Analyze user update conflicts
        user_conflicts = await self._analyze_user_transaction_conflicts(db, simulation_report)
        if user_conflicts:
            transaction_conflicts.append(user_conflicts)
        
        return transaction_conflicts
    
    async def _analyze_cache_consistency(self, simulation_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze cache consistency issues"""
        cache_issues = []
        
        # Check for cache invalidation issues
        bottlenecks = simulation_report.get("bottlenecks", [])
        cache_bottlenecks = [b for b in bottlenecks if "cache" in b.get("bottleneck_type", "").lower()]
        
        if cache_bottlenecks:
            cache_issues.append({
                "issue_type": "cache_invalidation",
                "description": "Cache invalidation failures during high load",
                "impact": "Stale data served to users",
                "affected_endpoints": ["/api/v1/bookings", "/api/v1/users/me"],
                "severity": "medium"
            })
        
        # Check for cache stampede issues
        resource_usage = simulation_report.get("resource_usage", {})
        if resource_usage.get("cache", {}).get("max", 0) > 90:
            cache_issues.append({
                "issue_type": "cache_stampede",
                "description": "Cache stampede due to high concurrent requests",
                "impact": "Increased database load and response times",
                "affected_endpoints": ["/api/v1/bookings", "/api/v1/calendar"],
                "severity": "high"
            })
        
        return cache_issues
    
    async def _analyze_stale_data(self, db: AsyncSession) -> List[ConsistencyIssue]:
        """Analyze stale data issues"""
        stale_issues = []
        
        # Check for stale user quota data
        stale_quotas = await self._find_stale_quota_data(db)
        if stale_quotas:
            issue = ConsistencyIssue(
                issue_type=ConsistencyIssueType.STALE_DATA,
                entity_type="user_quota",
                affected_records=len(stale_quotas),
                detection_time=datetime.now(timezone.utc),
                root_cause="Cache invalidation failures during high load",
                severity="medium",
                auto_recovery_possible=True,
                recovery_strategy="Force cache refresh and recalculate quotas",
                prevention_strategy="Implement cache warming and proper invalidation"
            )
            stale_issues.append(issue)
        
        # Check for stale calendar sync data
        stale_sync = await self._find_stale_calendar_sync_data(db)
        if stale_sync:
            issue = ConsistencyIssue(
                issue_type=ConsistencyIssueType.STALE_DATA,
                entity_type="calendar_sync",
                affected_records=len(stale_sync),
                detection_time=datetime.now(timezone.utc),
                root_cause="Calendar sync failures during high load",
                severity="low",
                auto_recovery_possible=True,
                recovery_strategy="Trigger manual calendar sync",
                prevention_strategy="Implement sync retry logic and exponential backoff"
            )
            stale_issues.append(issue)
        
        return stale_issues
    
    async def _find_duplicate_bookings(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Find duplicate booking records"""
        try:
            # Find bookings with same user, time, and title
            query = text("""
                SELECT user_id, start_time, title, COUNT(*) as duplicate_count
                FROM bookings
                WHERE start_time > NOW() - INTERVAL '1 hour'
                GROUP BY user_id, start_time, title
                HAVING COUNT(*) > 1
            """)
            
            result = await db.execute(query)
            duplicates = result.fetchall()
            
            return [dict(row._mapping) for row in duplicates]
            
        except Exception as e:
            logger.error(f"Error finding duplicate bookings: {e}")
            return []
    
    async def _find_duplicate_users(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Find duplicate user records"""
        try:
            # Find users with duplicate emails
            query = text("""
                SELECT email, COUNT(*) as duplicate_count
                FROM users
                GROUP BY email
                HAVING COUNT(*) > 1
            """)
            
            result = await db.execute(query)
            duplicates = result.fetchall()
            
            return [dict(row._mapping) for row in duplicates]
            
        except Exception as e:
            logger.error(f"Error finding duplicate users: {e}")
            return []
    
    async def _find_orphaned_bookings(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Find orphaned booking records"""
        try:
            # Find bookings without valid users
            query = text("""
                SELECT b.id, b.user_id, b.title
                FROM bookings b
                LEFT JOIN users u ON b.user_id = u.id
                WHERE u.id IS NULL
                LIMIT 100
            """)
            
            result = await db.execute(query)
            orphaned = result.fetchall()
            
            return [dict(row._mapping) for row in orphaned]
            
        except Exception as e:
            logger.error(f"Error finding orphaned bookings: {e}")
            return []
    
    async def _find_orphaned_calendar_integrations(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Find orphaned calendar integration records"""
        try:
            # Find calendar integrations without valid users
            query = text("""
                SELECT ci.id, ci.user_id, ci.provider
                FROM calendar_integrations ci
                LEFT JOIN users u ON ci.user_id = u.id
                WHERE u.id IS NULL
                LIMIT 100
            """)
            
            result = await db.execute(query)
            orphaned = result.fetchall()
            
            return [dict(row._mapping) for row in orphaned]
            
        except Exception as e:
            logger.error(f"Error finding orphaned calendar integrations: {e}")
            return []
    
    async def _analyze_booking_race_conditions(self, db: AsyncSession, simulation_report: Dict[str, Any]) -> Optional[RaceCondition]:
        """Analyze booking creation race conditions"""
        try:
            # Check for bookings created in same time window
            query = text("""
                SELECT user_id, COUNT(*) as concurrent_bookings
                FROM bookings
                WHERE created_at > NOW() - INTERVAL '1 minute'
                GROUP BY user_id
                HAVING COUNT(*) > 1
            """)
            
            result = await db.execute(query)
            concurrent_bookings = result.fetchall()
            
            if concurrent_bookings:
                total_concurrent = sum(row.concurrent_bookings for row in concurrent_bookings)
                conflict_probability = min(0.95, total_concurrent / 100)  # Estimate
                
                return RaceCondition(
                    resource="booking_creation",
                    concurrent_operations=total_concurrent,
                    conflict_probability=conflict_probability,
                    detected_conflicts=len(concurrent_bookings),
                    affected_entities=["booking"],
                    mitigation_strategy="Implement distributed locking and idempotency keys"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing booking race conditions: {e}")
            return None
    
    async def _analyze_quota_race_conditions(self, db: AsyncSession, simulation_report: Dict[str, Any]) -> Optional[RaceCondition]:
        """Analyze quota update race conditions"""
        try:
            # Check for rapid quota updates
            query = text("""
                SELECT user_id, COUNT(*) as rapid_updates
                FROM users
                WHERE updated_at > NOW() - INTERVAL '1 minute'
                GROUP BY user_id
                HAVING COUNT(*) > 5
            """)
            
            result = await db.execute(query)
            rapid_updates = result.fetchall()
            
            if rapid_updates:
                total_rapid = sum(row.rapid_updates for row in rapid_updates)
                conflict_probability = min(0.8, total_rapid / 50)  # Estimate
                
                return RaceCondition(
                    resource="quota_updates",
                    concurrent_operations=total_rapid,
                    conflict_probability=conflict_probability,
                    detected_conflicts=len(rapid_updates),
                    affected_entities=["user_quota"],
                    mitigation_strategy="Implement atomic quota operations with proper locking"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing quota race conditions: {e}")
            return None
    
    async def _analyze_calendar_sync_race_conditions(self, db: AsyncSession, simulation_report: Dict[str, Any]) -> Optional[RaceCondition]:
        """Analyze calendar sync race conditions"""
        try:
            # Check for concurrent calendar sync operations
            query = text("""
                SELECT user_id, COUNT(*) as concurrent_syncs
                FROM calendar_integrations
                WHERE last_sync_at > NOW() - INTERVAL '1 minute'
                GROUP BY user_id
                HAVING COUNT(*) > 1
            """)
            
            result = await db.execute(query)
            concurrent_syncs = result.fetchall()
            
            if concurrent_syncs:
                total_concurrent = sum(row.concurrent_syncs for row in concurrent_syncs)
                conflict_probability = min(0.7, total_concurrent / 20)  # Estimate
                
                return RaceCondition(
                    resource="calendar_sync",
                    concurrent_operations=total_concurrent,
                    conflict_probability=conflict_probability,
                    detected_conflicts=len(concurrent_syncs),
                    affected_entities=["calendar_integration"],
                    mitigation_strategy="Implement sync queuing and deduplication"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing calendar sync race conditions: {e}")
            return None
    
    async def _analyze_booking_transaction_conflicts(self, db: AsyncSession, simulation_report: Dict[str, Any]) -> Optional[TransactionConflict]:
        """Analyze booking transaction conflicts"""
        try:
            # This would require transaction logging to be implemented
            # For now, return estimated conflicts based on load
            
            total_requests = simulation_report.get("simulation_summary", {}).get("total_requests", 0)
            estimated_conflict_rate = min(0.1, total_requests / 10000)  # Estimate
            
            return TransactionConflict(
                transaction_type="booking_creation",
                isolation_level=IsolationLevel.READ_COMMITTED,
                conflict_rate=estimated_conflict_rate,
                deadlock_count=int(total_requests * 0.001),  # Estimate
                rollback_count=int(total_requests * 0.005),  # Estimate
                affected_tables=["bookings", "users"],
                recommended_isolation=IsolationLevel.SERIALIZABLE
            )
            
        except Exception as e:
            logger.error(f"Error analyzing booking transaction conflicts: {e}")
            return None
    
    async def _analyze_user_transaction_conflicts(self, db: AsyncSession, simulation_report: Dict[str, Any]) -> Optional[TransactionConflict]:
        """Analyze user update transaction conflicts"""
        try:
            # Estimate conflicts based on user update patterns
            total_requests = simulation_report.get("simulation_summary", {}).get("total_requests", 0)
            estimated_conflict_rate = min(0.05, total_requests / 20000)  # Estimate
            
            return TransactionConflict(
                transaction_type="user_update",
                isolation_level=IsolationLevel.READ_COMMITTED,
                conflict_rate=estimated_conflict_rate,
                deadlock_count=int(total_requests * 0.0005),  # Estimate
                rollback_count=int(total_requests * 0.002),  # Estimate
                affected_tables=["users"],
                recommended_isolation=IsolationLevel.REPEATABLE_READ
            )
            
        except Exception as e:
            logger.error(f"Error analyzing user transaction conflicts: {e}")
            return None
    
    async def _find_stale_quota_data(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Find stale quota data"""
        try:
            # Find users with quota reset time in the past
            query = text("""
                SELECT id, email, quota_reset_at
                FROM users
                WHERE quota_reset_at < NOW() - INTERVAL '1 day'
                LIMIT 100
            """)
            
            result = await db.execute(query)
            stale_quotas = result.fetchall()
            
            return [dict(row._mapping) for row in stale_quotas]
            
        except Exception as e:
            logger.error(f"Error finding stale quota data: {e}")
            return []
    
    async def _find_stale_calendar_sync_data(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Find stale calendar sync data"""
        try:
            # Find calendar integrations not synced recently
            query = text("""
                SELECT id, user_id, provider, last_sync_at
                FROM calendar_integrations
                WHERE last_sync_at < NOW() - INTERVAL '1 hour'
                AND sync_status = 'active'
                LIMIT 100
            """)
            
            result = await db.execute(query)
            stale_sync = result.fetchall()
            
            return [dict(row._mapping) for row in stale_sync]
            
        except Exception as e:
            logger.error(f"Error finding stale calendar sync data: {e}")
            return []
    
    def _identify_critical_consistency_issues(self) -> List[str]:
        """Identify critical consistency issues that need immediate attention"""
        critical_issues = []
        
        for issue in self.consistency_issues:
            if issue.severity in ["critical", "high"] and not issue.auto_recovery_possible:
                critical_issues.append(f"{issue.entity_type}: {issue.issue_type.value}")
        
        # Add race conditions with high probability
        for race_condition in self.race_conditions:
            if race_condition.conflict_probability > 0.5:
                critical_issues.append(f"Race condition: {race_condition.resource}")
        
        return critical_issues
    
    def _generate_recovery_strategies(self) -> Dict[str, List[str]]:
        """Generate recovery strategies for different consistency issues"""
        strategies = {
            "duplicate_records": [
                "Implement unique constraints at database level",
                "Add idempotency keys for API operations",
                "Implement data deduplication jobs",
                "Manual review and merge of duplicates"
            ],
            "orphaned_records": [
                "Implement proper foreign key constraints",
                "Add cascade delete rules",
                "Run periodic cleanup jobs",
                "Archive orphaned records"
            ],
            "race_conditions": [
                "Implement distributed locking mechanisms",
                "Add idempotency to all write operations",
                "Use optimistic locking with version numbers",
                "Implement request deduplication"
            ],
            "cache_consistency": [
                "Implement cache invalidation strategies",
                "Add cache warming mechanisms",
                "Use cache stampede protection",
                "Implement cache consistency checks"
            ],
            "transaction_conflicts": [
                "Use appropriate isolation levels",
                "Implement retry logic for conflicts",
                "Add deadlock detection and handling",
                "Use optimistic concurrency control"
            ]
        }
        
        return strategies
    
    def _generate_prevention_recommendations(self) -> List[str]:
        """Generate prevention recommendations"""
        recommendations = [
            "Implement database constraints and foreign keys",
            "Use distributed transactions for critical operations",
            "Implement proper cache invalidation strategies",
            "Add idempotency to all API endpoints",
            "Use optimistic locking with version numbers",
            "Implement circuit breakers for external services",
            "Add comprehensive data validation",
            "Implement audit logging for data changes",
            "Use message queues for async operations",
            "Implement proper error handling and retry logic",
            "Add data consistency checks and validation",
            "Implement proper session management",
            "Use database connection pooling with proper limits",
            "Implement proper timeout handling",
            "Add monitoring and alerting for consistency issues"
        ]
        
        return recommendations
    
    def _generate_monitoring_requirements(self) -> List[str]:
        """Generate monitoring requirements for data consistency"""
        requirements = [
            "Monitor duplicate record creation",
            "Track orphaned record counts",
            "Monitor race condition indicators",
            "Track transaction conflict rates",
            "Monitor cache hit/miss ratios",
            "Track stale data detection",
            "Monitor database lock contention",
            "Track API response times under load",
            "Monitor error rates by endpoint",
            "Track concurrent operation counts",
            "Monitor database connection pool usage",
            "Track cache invalidation latency",
            "Monitor message queue depth",
            "Track background job failure rates",
            "Monitor data integrity checks"
        ]
        
        return requirements


# Global consistency analyzer
consistency_analyzer = DataConsistencyAnalyzer()


async def analyze_data_consistency(db: AsyncSession, simulation_report: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze data consistency issues from traffic spike simulation"""
    return await consistency_analyzer.analyze_consistency_issues(db, simulation_report)
