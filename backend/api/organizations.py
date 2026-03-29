from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from backend.api.deps import get_db
from backend.auth.schemes import get_current_user, get_current_user_id
from backend.models.tables import OrganizationTable, UserOrganizationTable, WorkspaceTable
from backend.utils.tenant import get_current_org_id

router = APIRouter(prefix="/organizations", tags=["organizations"])

# --- Models ---

class WorkspaceBase(BaseModel):
    name: str
    slug: str

class WorkspaceRead(WorkspaceBase):
    id: int
    org_id: int

class OrganizationBase(BaseModel):
    name: str
    slug: str

class OrganizationRead(OrganizationBase):
    id: int
    role: str # User's role in this org

# --- Endpoints ---

@router.get("/", response_model=List[OrganizationRead])
async def list_my_organizations(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """List all organizations the user belongs to."""
    stmt = (
        select(OrganizationTable, UserOrganizationTable.role)
        .join(UserOrganizationTable, OrganizationTable.id == UserOrganizationTable.org_id)
        .where(UserOrganizationTable.user_id == user_id)
    )
    result = await db.execute(stmt)
    orgs = []
    for org, role in result.all():
        orgs.append({
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "role": role
        })
    return orgs

@router.post("/", response_model=OrganizationRead)
async def create_organization(
    org_data: OrganizationBase,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Create a new organization and assign current user as admin."""
    # Check slug uniqueness
    stmt = select(OrganizationTable).where(OrganizationTable.slug == org_data.slug)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already in use")

    new_org = OrganizationTable(**org_data.dict())
    db.add(new_org)
    await db.flush()

    mapping = UserOrganizationTable(
        user_id=user_id,
        org_id=new_org.id,
        role="admin"
    )
    db.add(mapping)
    await db.commit()
    await db.refresh(new_org)

    return {
        "id": new_org.id,
        "name": new_org.name,
        "slug": new_org.slug,
        "role": "admin"
    }

@router.get("/{org_id}/workspaces", response_model=List[WorkspaceRead])
async def list_workspaces(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    # Ensure current user belongs to the org
    verified_org_id: int = Depends(get_current_org_id) 
):
    """List all workspaces in an organization."""
    if org_id != verified_org_id:
        raise HTTPException(status_code=403, detail="Forbidden: Organization mismatch")

    stmt = select(WorkspaceTable).where(WorkspaceTable.org_id == org_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{org_id}/workspaces", response_model=WorkspaceRead)
async def create_workspace(
    org_id: int,
    workspace_data: WorkspaceBase,
    db: AsyncSession = Depends(get_db),
    verified_org_id: int = Depends(get_current_org_id)
):
    """Create a new workspace within an organization."""
    if org_id != verified_org_id:
        raise HTTPException(status_code=403, detail="Forbidden: Organization mismatch")

    new_workspace = WorkspaceTable(
        **workspace_data.dict(),
        org_id=org_id
    )
    db.add(new_workspace)
    await db.commit()
    await db.refresh(new_workspace)
    return new_workspace
