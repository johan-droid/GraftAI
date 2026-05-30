"""
Data Portability Framework for GraftAI

Implements standardized data formats and migration tools:
- Standardized data schemas
- Export/import capabilities
- Data transformation pipelines
- Migration orchestration
"""
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class DataFormat(Enum):
    """Supported data formats"""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    PARQUET = "parquet"
    SQLITE = "sqlite"

class MigrationStatus(Enum):
    """Migration status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class DataSchema:
    """Standardized data schema definition"""
    entity_name: str
    version: str
    fields: dict[str, dict[str, Any]]
    indexes: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    constraints: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert schema to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataSchema":
        """Create schema from dictionary"""
        return cls(**data)

@dataclass
class MigrationJob:
    """Migration job definition"""
    job_id: str
    source_provider: str
    target_provider: str
    entity_type: str
    status: MigrationStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    records_processed: int = 0
    total_records: int = 0
    error_message: str | None = None
    rollback_data: str | None = None

class DataExporter(ABC):
    """Abstract data exporter interface"""

    @abstractmethod
    async def export_data(self, entity_type: str, filters: dict | None=None) -> dict[str, Any]:
        """Export data in standardized format"""

    @abstractmethod
    async def export_schema(self, entity_type: str) -> DataSchema:
        """Export data schema"""

    @abstractmethod
    async def validate_export(self, data: dict[str, Any]) -> bool:
        """Validate exported data"""

class DataImporter(ABC):
    """Abstract data importer interface"""

    @abstractmethod
    async def import_data(self, entity_type: str, data: dict[str, Any], schema: DataSchema) -> bool:
        """Import data from standardized format"""

    @abstractmethod
    async def validate_import(self, data: dict[str, Any], schema: DataSchema) -> bool:
        """Validate data before import"""

    @abstractmethod
    async def rollback_import(self, job_id: str) -> bool:
        """Rollback failed import"""

class DataTransformer(ABC):
    """Abstract data transformer interface"""

    @abstractmethod
    async def transform(self, data: dict[str, Any], source_schema: DataSchema, target_schema: DataSchema) -> dict[str, Any]:
        """Transform data between schemas"""

    @abstractmethod
    async def validate_transformation(self, data: dict[str, Any], schema: DataSchema) -> bool:
        """Validate transformed data"""

class StandardizedSchemas:
    """Standardized data schemas for GraftAI entities"""
    USER_SCHEMA = DataSchema(entity_name="user", version="1.0", fields={"id": {"type": "string", "required": True, "primary_key": True}, "email": {"type": "string", "required": True, "unique": True}, "username": {"type": "string", "required": False}, "full_name": {"type": "string", "required": False}, "timezone": {"type": "string", "required": False, "default": "UTC"}, "email_verified": {"type": "boolean", "required": False, "default": False}, "tier": {"type": "string", "required": False, "default": "free"}, "subscription_status": {"type": "string", "required": False, "default": "inactive"}, "created_at": {"type": "datetime", "required": True}, "updated_at": {"type": "datetime", "required": True}, "preferences": {"type": "json", "required": False}, "metadata": {"type": "json", "required": False}}, indexes=[{"fields": ["email"], "unique": True}, {"fields": ["username"], "unique": True}, {"fields": ["tier"]}, {"fields": ["created_at"]}], relationships=[{"type": "one_to_many", "field": "bookings", "target": "booking", "foreign_key": "user_id"}, {"type": "one_to_many", "field": "calendar_integrations", "target": "calendar_integration", "foreign_key": "user_id"}], constraints=[{"type": "check", "condition": "tier IN ('free', 'pro', 'elite', 'enterprise')"}, {"type": "check", "condition": "subscription_status IN ('active', 'inactive', 'cancelled', 'trial')"}])
    BOOKING_SCHEMA = DataSchema(entity_name="booking", version="1.0", fields={"id": {"type": "string", "required": True, "primary_key": True}, "user_id": {"type": "string", "required": True, "foreign_key": "user.id"}, "title": {"type": "string", "required": True}, "description": {"type": "text", "required": False}, "start_time": {"type": "datetime", "required": True}, "end_time": {"type": "datetime", "required": True}, "timezone": {"type": "string", "required": True}, "status": {"type": "string", "required": True, "default": "scheduled"}, "attendees": {"type": "json", "required": False}, "location": {"type": "json", "required": False}, "recurrence": {"type": "json", "required": False}, "external_calendar_id": {"type": "string", "required": False}, "created_at": {"type": "datetime", "required": True}, "updated_at": {"type": "datetime", "required": True}, "metadata": {"type": "json", "required": False}}, indexes=[{"fields": ["user_id"]}, {"fields": ["start_time"]}, {"fields": ["status"]}, {"fields": ["external_calendar_id"]}], relationships=[{"type": "many_to_one", "field": "user", "target": "user", "foreign_key": "user_id"}], constraints=[{"type": "check", "condition": "start_time < end_time"}, {"type": "check", "condition": "status IN ('scheduled', 'confirmed', 'cancelled', 'completed')"}])
    CALENDAR_INTEGRATION_SCHEMA = DataSchema(entity_name="calendar_integration", version="1.0", fields={"id": {"type": "string", "required": True, "primary_key": True}, "user_id": {"type": "string", "required": True, "foreign_key": "user.id"}, "provider": {"type": "string", "required": True}, "provider_user_id": {"type": "string", "required": True}, "calendar_id": {"type": "string", "required": True}, "access_token": {"type": "encrypted_string", "required": True}, "refresh_token": {"type": "encrypted_string", "required": False}, "token_expires_at": {"type": "datetime", "required": False}, "sync_status": {"type": "string", "required": True, "default": "active"}, "last_sync_at": {"type": "datetime", "required": False}, "sync_settings": {"type": "json", "required": False}, "created_at": {"type": "datetime", "required": True}, "updated_at": {"type": "datetime", "required": True}}, indexes=[{"fields": ["user_id"]}, {"fields": ["provider"]}, {"fields": ["sync_status"]}], relationships=[{"type": "many_to_one", "field": "user", "target": "user", "foreign_key": "user_id"}], constraints=[{"type": "check", "condition": "provider IN ('google', 'microsoft', 'caldav')"}, {"type": "check", "condition": "sync_status IN ('active', 'inactive', 'error', 'syncing')"}])

    @classmethod
    def get_schema(cls, entity_name: str) -> DataSchema | None:
        """Get schema by entity name"""
        schemas = {"user": cls.USER_SCHEMA, "booking": cls.BOOKING_SCHEMA, "calendar_integration": cls.CALENDAR_INTEGRATION_SCHEMA}
        return schemas.get(entity_name)

class DatabaseExporter(DataExporter):
    """Database data exporter"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_data(self, entity_type: str, filters: dict | None=None) -> dict[str, Any]:
        """Export data from database"""
        try:
            schema = StandardizedSchemas.get_schema(entity_type)
            if not schema:
                msg = f"Unknown entity type: {entity_type}"
                raise ValueError(msg)
            query = f"SELECT * FROM {entity_type}s"
            params = {}
            if filters:
                where_clauses = []
                for field, value in filters.items():
                    where_clauses.append(f"{field} = :{field}")
                    params[field] = value
                if where_clauses:
                    query += f" WHERE {' AND '.join(where_clauses)}"
            result = await self.db.execute(text(query), params)
            rows = result.fetchall()
            return {"schema": schema.to_dict(), "data": [dict(row._mapping) for row in rows], "exported_at": datetime.now(UTC).isoformat(), "record_count": len(rows)}
        except Exception as e:
            logger.exception("Error exporting %s: %s", entity_type, e)
            raise

    async def export_schema(self, entity_type: str) -> DataSchema:
        """Export data schema"""
        schema = StandardizedSchemas.get_schema(entity_type)
        if not schema:
            msg = f"Unknown entity type: {entity_type}"
            raise ValueError(msg)
        return schema

    async def validate_export(self, data: dict[str, Any]) -> bool:
        """Validate exported data"""
        try:
            schema = DataSchema.from_dict(data["schema"])
            records = data["data"]
            return all(self._validate_record(record, schema) for record in records)
        except Exception as e:
            logger.exception("Error validating export: %s", e)
            return False

    def _validate_record(self, record: dict, schema: DataSchema) -> bool:
        """Validate record against schema"""
        for field_name, field_def in schema.fields.items():
            if field_def.get("required", False) and field_name not in record:
                return False
            if field_name in record:
                field_type = field_def["type"]
                value = record[field_name]
                if (field_type == "string" and (not isinstance(value, str))) or (field_type == "datetime" and (not isinstance(value, (str, datetime)))):
                    return False
                if (field_type == "boolean" and (not isinstance(value, bool))) or (field_type == "json" and (not isinstance(value, (dict, str)))):
                    return False
        return True

class DatabaseImporter(DataImporter):
    """Database data importer"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rollback_data: dict[str, list[dict]] = {}

    async def import_data(self, entity_type: str, data: dict[str, Any], schema: DataSchema) -> bool:
        """Import data to database"""
        try:
            records = data["data"]
            await self._create_rollback_snapshot(entity_type)
            batch_size = 100
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                await self._import_batch(entity_type, batch, schema)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            logger.exception("Error importing %s: %s", entity_type, e)
            return False

    async def validate_import(self, data: dict[str, Any], schema: DataSchema) -> bool:
        """Validate data before import"""
        try:
            records = data["data"]
            return all(self._validate_record(record, schema) for record in records)
        except Exception as e:
            logger.exception("Error validating import: %s", e)
            return False

    async def rollback_import(self, job_id: str) -> bool:
        """Rollback failed import"""
        try:
            for entity_type, records in self.rollback_data.items():
                await self.db.execute(text(f"DELETE FROM {entity_type}s"))
                if records:
                    pass
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            logger.exception("Error rolling back import: %s", e)
            return False

    async def _create_rollback_snapshot(self, entity_type: str):
        """Create rollback snapshot"""
        try:
            result = await self.db.execute(text(f"SELECT * FROM {entity_type}s"))
            self.rollback_data[entity_type] = [dict(row._mapping) for row in result]
        except Exception as e:
            logger.exception("Error creating rollback snapshot: %s", e)

    async def _import_batch(self, entity_type: str, batch: list[dict], schema: DataSchema):
        """Import batch of records"""
        fields = list(schema.fields.keys())
        placeholders = [f":{field}" for field in fields]
        insert_sql = f"\n        INSERT INTO {entity_type}s ({', '.join(fields)})\n        VALUES ({', '.join(placeholders)})\n        ON CONFLICT (id) DO UPDATE SET\n        {', '.join([f'{field} = EXCLUDED.{field}' for field in fields if field != 'id'])}\n        "
        for record in batch:
            await self.db.execute(text(insert_sql), record)

    def _validate_record(self, record: dict, schema: DataSchema) -> bool:
        """Validate record against schema"""
        for field_name, field_def in schema.fields.items():
            if field_def.get("required", False) and field_name not in record:
                return False
            if field_name in record:
                field_type = field_def["type"]
                value = record[field_name]
                if (field_type == "string" and (not isinstance(value, str))) or (field_type == "datetime" and (not isinstance(value, (str, datetime)))):
                    return False
                if (field_type == "boolean" and (not isinstance(value, bool))) or (field_type == "json" and (not isinstance(value, (dict, str)))):
                    return False
        return True

class DataTransformer:
    """Data transformer between different formats"""

    async def transform(self, data: dict[str, Any], source_schema: DataSchema, target_schema: DataSchema) -> dict[str, Any]:
        """Transform data between schemas"""
        try:
            records = data["data"]
            transformed_records = []
            for record in records:
                transformed_record = await self._transform_record(record, source_schema, target_schema)
                transformed_records.append(transformed_record)
            return {"schema": target_schema.to_dict(), "data": transformed_records, "transformed_at": datetime.now(UTC).isoformat(), "record_count": len(transformed_records)}
        except Exception as e:
            logger.exception("Error transforming data: %s", e)
            raise

    async def validate_transformation(self, data: dict[str, Any], schema: DataSchema) -> bool:
        """Validate transformed data"""
        try:
            records = data["data"]
            return all(self._validate_record(record, schema) for record in records)
        except Exception as e:
            logger.exception("Error validating transformation: %s", e)
            return False

    async def _transform_record(self, record: dict, source_schema: DataSchema, target_schema: DataSchema) -> dict:
        """Transform individual record"""
        transformed = {}
        for field_name, _field_def in target_schema.fields.items():
            if field_name in record:
                transformed[field_name] = record[field_name]
            else:
                alternatives = self._find_alternative_fields(field_name, source_schema)
                for alt in alternatives:
                    if alt in record:
                        transformed[field_name] = record[alt]
                        break
        return transformed

    def _find_alternative_fields(self, field_name: str, schema: DataSchema) -> list[str]:
        """Find alternative field names"""
        alternatives = {"user_id": ["owner_id", "account_id"], "created_at": ["timestamp", "date_created"], "updated_at": ["modified_at", "date_updated"]}
        return alternatives.get(field_name, [])

    def _validate_record(self, record: dict, schema: DataSchema) -> bool:
        """Validate record against schema"""
        for field_name, field_def in schema.fields.items():
            if field_def.get("required", False) and field_name not in record:
                return False
            if field_name in record:
                field_type = field_def["type"]
                value = record[field_name]
                if (field_type == "string" and (not isinstance(value, str))) or (field_type == "datetime" and (not isinstance(value, (str, datetime)))):
                    return False
                if (field_type == "boolean" and (not isinstance(value, bool))) or (field_type == "json" and (not isinstance(value, (dict, str)))):
                    return False
        return True

class DataPortabilityManager:
    """Manages data portability operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.exporter = DatabaseExporter(db)
        self.importer = DatabaseImporter(db)
        self.transformer = DataTransformer()
        self.migration_jobs: dict[str, MigrationJob] = {}

    async def export_user_data(self, user_id: str, format: DataFormat=DataFormat.JSON) -> str | bytes:
        """Export all user data in specified format"""
        try:
            entities = ["user", "booking", "calendar_integration"]
            export_data = {}
            for entity in entities:
                filters = {"user_id": user_id} if entity != "user" else {"id": user_id}
                data = await self.exporter.export_data(entity, filters)
                export_data[entity] = data
            if format == DataFormat.JSON:
                return json.dumps(export_data, indent=2, default=str)
            if format == DataFormat.CSV:
                return await self._convert_to_csv(export_data)
            if format == DataFormat.PARQUET:
                return await self._convert_to_parquet(export_data)
            msg = f"Unsupported format: {format}"
            raise ValueError(msg)
        except Exception as e:
            logger.exception("Error exporting user data: %s", e)
            raise

    async def import_user_data(self, user_id: str, data: str | bytes, format: DataFormat=DataFormat.JSON) -> bool:
        """Import user data from specified format"""
        try:
            if format == DataFormat.JSON:
                parsed_data = json.loads(data)
            else:
                msg = f"Unsupported format: {format}"
                raise ValueError(msg)
            for entity_name, entity_data in parsed_data.items():
                schema = StandardizedSchemas.get_schema(entity_name)
                if schema:
                    if await self.importer.validate_import(entity_data, schema):
                        await self.importer.import_data(entity_name, entity_data, schema)
            return True
        except Exception as e:
            logger.exception("Error importing user data: %s", e)
            return False

    async def migrate_data(self, source_provider: str, target_provider: str, entity_type: str) -> str:
        """Migrate data between providers"""
        job_id = f"migration_{entity_type}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        job = MigrationJob(job_id=job_id, source_provider=source_provider, target_provider=target_provider, entity_type=entity_type, status=MigrationStatus.PENDING, created_at=datetime.now(UTC))
        self.migration_jobs[job_id] = job
        try:
            job.status = MigrationStatus.IN_PROGRESS
            job.started_at = datetime.now(UTC)
            export_data = await self.exporter.export_data(entity_type)
            job.total_records = export_data["record_count"]
            source_schema = StandardizedSchemas.get_schema(entity_type)
            target_schema = StandardizedSchemas.get_schema(entity_type)
            if source_schema.version != target_schema.version:
                export_data = await self.transformer.transform(export_data, source_schema, target_schema)
            success = await self.importer.import_data(entity_type, export_data, target_schema)
            if success:
                job.status = MigrationStatus.COMPLETED
                job.completed_at = datetime.now(UTC)
                job.records_processed = job.total_records
            else:
                job.status = MigrationStatus.FAILED
                job.error_message = "Import failed"
        except Exception as e:
            job.status = MigrationStatus.FAILED
            job.error_message = str(e)
            logger.exception("Migration failed: %s", e)
        return job_id

    async def get_migration_status(self, job_id: str) -> MigrationJob | None:
        """Get migration job status"""
        return self.migration_jobs.get(job_id)

    async def _convert_to_csv(self, data: dict[str, Any]) -> str:
        """Convert data to CSV format"""
        csv_data = {}
        for entity_name, entity_data in data.items():
            records = entity_data["data"]
            if records:
                df = pd.DataFrame(records)
                csv_data[entity_name] = df.to_csv(index=False)
        return json.dumps(csv_data)

    async def _convert_to_parquet(self, data: dict[str, Any]) -> bytes:
        """Convert data to Parquet format"""
        return json.dumps(data).encode()
data_portability_manager: DataPortabilityManager | None = None

def get_data_portability_manager(db: AsyncSession) -> DataPortabilityManager:
    """Get data portability manager instance"""
    global data_portability_manager
    if data_portability_manager is None:
        data_portability_manager = DataPortabilityManager(db)
    return data_portability_manager
