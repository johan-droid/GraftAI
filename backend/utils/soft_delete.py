"""
Soft delete mixin for SQLAlchemy models.
Provides soft delete functionality with query filtering.
"""
from datetime import datetime, timezone
from typing import Optional, TypeVar, List, Type

from sqlalchemy import Column, DateTime, Boolean, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declared_attr


class SoftDeleteMixin:
    """
    Mixin to add soft delete functionality to SQLAlchemy models.
    
    Usage:
        class MyModel(Base, SoftDeleteMixin):
            __tablename__ = "my_table"
            # other columns...
    
    Then use the provided methods:
        await obj.soft_delete(db)  # Soft delete
        await obj.restore(db)  # Restore soft-deleted record
        
    Querying:
        # Get only non-deleted records
        await MyModel.get_active(db)
        
        # Get only deleted records
        await MyModel.get_deleted(db)
        
        # Get all records (including deleted)
        await MyModel.get_all(db)
    """
    
    deleted_at: Optional[datetime] = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True
    )
    
    is_deleted: bool = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    async def soft_delete(self, db: AsyncSession, deleted_by: Optional[str] = None) -> None:
        """
        Soft delete this record.
        
        Args:
            db: Database session
            deleted_by: Optional user ID who performed the deletion
        """
        self.deleted_at = datetime.now(timezone.utc)
        self.is_deleted = True
        
        # Optionally track who deleted
        if deleted_by and hasattr(self, 'deleted_by'):
            self.deleted_by = deleted_by
        
        db.add(self)
        await db.commit()
    
    async def restore(self, db: AsyncSession) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.is_deleted = False
        
        if hasattr(self, 'deleted_by'):
            self.deleted_by = None
        
        db.add(self)
        await db.commit()
    
    async def hard_delete(self, db: AsyncSession) -> None:
        """Permanently delete the record from database."""
        await db.delete(self)
        await db.commit()
    
    @classmethod
    async def get_active(
        cls: Type["SoftDeleteMixin"],
        db: AsyncSession,
        **filters
    ) -> List:
        """
        Get all non-deleted (active) records.
        
        Args:
            db: Database session
            **filters: Additional filter conditions
        
        Returns:
            List of active records
        """
        query = select(cls).where(cls.is_deleted == False)
        
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.where(getattr(cls, key) == value)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def get_deleted(
        cls: Type["SoftDeleteMixin"],
        db: AsyncSession,
        **filters
    ) -> List:
        """
        Get all soft-deleted records.
        
        Args:
            db: Database session
            **filters: Additional filter conditions
        
        Returns:
            List of deleted records
        """
        query = select(cls).where(cls.is_deleted == True)
        
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.where(getattr(cls, key) == value)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def get_all(
        cls: Type["SoftDeleteMixin"],
        db: AsyncSession,
        include_deleted: bool = False,
        **filters
    ) -> List:
        """
        Get all records, optionally including soft-deleted ones.
        
        Args:
            db: Database session
            include_deleted: If True, include soft-deleted records
            **filters: Additional filter conditions
        
        Returns:
            List of records
        """
        if include_deleted:
            query = select(cls)
        else:
            query = select(cls).where(cls.is_deleted == False)
        
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.where(getattr(cls, key) == value)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def find_by_id(
        cls: Type["SoftDeleteMixin"],
        db: AsyncSession,
        record_id: str,
        include_deleted: bool = False
    ) -> Optional:
        """
        Find a record by ID.
        
        Args:
            db: Database session
            record_id: Record ID to find
            include_deleted: If True, can return soft-deleted records
        
        Returns:
            Record if found, None otherwise
        """
        # Get primary key column name
        pk_column = cls.__mapper__.primary_key[0].name
        
        query = select(cls).where(getattr(cls, pk_column) == record_id)
        
        if not include_deleted:
            query = query.where(cls.is_deleted == False)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def bulk_soft_delete(
        cls: Type["SoftDeleteMixin"],
        db: AsyncSession,
        ids: List[str],
        deleted_by: Optional[str] = None
    ) -> int:
        """
        Soft delete multiple records by ID.
        
        Args:
            db: Database session
            ids: List of record IDs to delete
            deleted_by: Optional user ID who performed the deletion
        
        Returns:
            Number of records deleted
        """
        pk_column = cls.__mapper__.primary_key[0].name
        
        # Find records
        query = select(cls).where(
            getattr(cls, pk_column).in_(ids),
            cls.is_deleted == False
        )
        result = await db.execute(query)
        records = result.scalars().all()
        
        # Soft delete each record
        deleted_at = datetime.now(timezone.utc)
        for record in records:
            record.deleted_at = deleted_at
            record.is_deleted = True
            if deleted_by and hasattr(record, 'deleted_by'):
                record.deleted_by = deleted_by
            db.add(record)
        
        await db.commit()
        return len(records)
    
    @classmethod
    async def bulk_restore(
        cls: Type["SoftDeleteMixin"],
        db: AsyncSession,
        ids: List[str]
    ) -> int:
        """
        Restore multiple soft-deleted records.
        
        Args:
            db: Database session
            ids: List of record IDs to restore
        
        Returns:
            Number of records restored
        """
        pk_column = cls.__mapper__.primary_key[0].name
        
        # Find deleted records
        query = select(cls).where(
            getattr(cls, pk_column).in_(ids),
            cls.is_deleted == True
        )
        result = await db.execute(query)
        records = result.scalars().all()
        
        # Restore each record
        for record in records:
            record.deleted_at = None
            record.is_deleted = False
            if hasattr(record, 'deleted_by'):
                record.deleted_by = None
            db.add(record)
        
        await db.commit()
        return len(records)
    
    @classmethod
    async def cleanup_deleted(
        cls: Type["SoftDeleteMixin"],
        db: AsyncSession,
        days: int = 30
    ) -> int:
        """
        Permanently delete records that have been soft-deleted for specified days.
        
        Args:
            db: Database session
            days: Number of days after which to permanently delete
        
        Returns:
            Number of records permanently deleted
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = select(cls).where(
            cls.is_deleted == True,
            cls.deleted_at <= cutoff_date
        )
        result = await db.execute(query)
        records = result.scalars().all()
        
        # Hard delete each record
        count = 0
        for record in records:
            await db.delete(record)
            count += 1
        
        await db.commit()
        return count
