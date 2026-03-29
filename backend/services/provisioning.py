from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from backend.models.tables import (
    UserTable, 
    OrganizationTable, 
    UserOrganizationTable, 
    WorkspaceTable,
    EventTable, 
    TodoTable
)
import logging

logger = logging.getLogger(__name__)

async def provision_default_organization(db: AsyncSession, user_id: str):
    """
    Ensure the user has at least one organization. 
    If not, create a Personal Organization and attempt to migrate orphan data.
    
    CRITICAL: Org/Workspace/Mapping creation is committed FIRST,
    then optional data migration is attempted separately so a failure
    in migrating legacy data never rolls back the org creation.
    """
    try:
        # 1. Check if user already belongs to any organization
        stmt = select(UserOrganizationTable).where(UserOrganizationTable.user_id == user_id).limit(1)
        result = await db.execute(stmt)
        existing_mapping = result.scalar_one_or_none()
        
        if existing_mapping:
            return  # User already provisioned

        # 2. Fetch user to get name for the organization
        stmt = select(UserTable).where(UserTable.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            logger.error(f"Cannot provision org: User {user_id} not found")
            return

        user_name = user.name or user.full_name or "Personal"
        org_name = f"{user_name}'s Personal Organization"
        org_slug = f"personal-{user_id[:8]}"

        # 3. Create Organization + Workspace + User Mapping (CRITICAL)
        new_org = OrganizationTable(
            name=org_name,
            slug=org_slug
        )
        db.add(new_org)
        await db.flush()  # Get the ID

        general_workspace = WorkspaceTable(
            org_id=new_org.id,
            name="General",
            slug="general"
        )
        db.add(general_workspace)
        await db.flush()

        mapping = UserOrganizationTable(
            user_id=user_id,
            org_id=new_org.id,
            role="admin"
        )
        db.add(mapping)
        
        # Commit the critical org infrastructure first
        await db.commit()
        logger.info(f"Successfully provisioned Personal Organization (id={new_org.id}) for user {user_id}")

        # 4. Optional: Migrate orphan data (events/todos without org_id)
        # This is best-effort — failure here should NOT affect the org itself
        try:
            stmt_events = update(EventTable).where(
                EventTable.user_id == user_id,
                EventTable.org_id == None
            ).values(
                org_id=new_org.id,
                workspace_id=general_workspace.id
            )
            await db.execute(stmt_events)

            stmt_todos = update(TodoTable).where(
                TodoTable.user_id == user_id,
                TodoTable.org_id == None
            ).values(
                org_id=new_org.id,
                workspace_id=general_workspace.id
            )
            await db.execute(stmt_todos)
            
            await db.commit()
            logger.info(f"Migrated orphan data for user {user_id}")
        except Exception as migrate_err:
            await db.rollback()
            logger.warning(f"Non-critical: Failed to migrate orphan data for user {user_id}: {migrate_err}")

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to provision default organization for user {user_id}: {e}")

