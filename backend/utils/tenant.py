from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from backend.utils.db import get_db
from backend.models.tables import UserOrganizationTable, OrganizationTable, WorkspaceTable
from backend.auth.schemes import get_current_user_id

logger = logging.getLogger(__name__)

async def get_current_org_id(
    x_org_id: Optional[int] = Header(None, alias="X-Org-Id"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> int:
    """Resolve the active Organization ID for the current request.
    
    Self-healing: If the user has no organization (e.g. provisioning failed
    during an earlier login due to a schema issue), auto-provision one now.
    """
    if x_org_id:
        # Verify user belongs to this org
        stmt = select(UserOrganizationTable).where(
            UserOrganizationTable.user_id == user_id,
            UserOrganizationTable.org_id == x_org_id
        )
        result = await db.execute(stmt)
        mapping = result.scalar_one_or_none()
        if not mapping:
            raise HTTPException(status_code=403, detail="Not a member of this organization")
        return x_org_id

    # Fallback: Get the user's first (default) organization
    stmt = select(UserOrganizationTable).where(
        UserOrganizationTable.user_id == user_id
    ).limit(1)
    result = await db.execute(stmt)
    mapping = result.scalar_one_or_none()
    
    if not mapping:
        # Self-healing: auto-provision a default organization on-demand
        logger.warning(f"No org found for user {user_id}, auto-provisioning now...")
        try:
            from backend.services.provisioning import provision_default_organization
            await provision_default_organization(db, str(user_id))
            
            # Re-query after provisioning
            result = await db.execute(
                select(UserOrganizationTable).where(
                    UserOrganizationTable.user_id == user_id
                ).limit(1)
            )
            mapping = result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Auto-provisioning failed for user {user_id}: {e}")
        
        if not mapping:
            raise HTTPException(
                status_code=404, 
                detail="No organization context found. Please create or join an organization."
            )
    
    return mapping.org_id

async def get_current_workspace_id(
    x_workspace_id: Optional[int] = Header(None, alias="X-Workspace-Id"),
    org_id: int = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
) -> Optional[int]:
    """Resolve the active Workspace ID for the current request."""
    if not x_workspace_id:
        return None  # Personal workspace / un-scoped

    # Verify workspace belongs to the current org
    stmt = select(WorkspaceTable).where(
        WorkspaceTable.id == x_workspace_id,
        WorkspaceTable.org_id == org_id
    )
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization context")
    
    return x_workspace_id
