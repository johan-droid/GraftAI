# Plugin/Marketplace API Service
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db
from backend.auth.schemes import get_current_user_id
from backend.models.user_token import UserTokenTable

router = APIRouter(prefix="/plugins", tags=["plugins"])


class PluginInfo(BaseModel):
    id: str
    name: str
    description: str
    version: str
    category: str
    icon: str
    installed: bool
    author: Optional[str] = None


class PluginListResponse(BaseModel):
    plugins: List[PluginInfo]


PLUGIN_CATALOG = [
    {
        "id": "google",
        "name": "Google Workspace",
        "description": "Two-way sync with Google Calendar and Google Meet link generation.",
        "version": "1.0.0",
        "category": "Calendar",
        "icon": "calendar",
        "author": "GraftAI",
    },
    {
        "id": "microsoft",
        "name": "Microsoft 365",
        "description": "Sync Outlook Calendar and create Microsoft Teams meeting links.",
        "version": "1.0.0",
        "category": "Calendar",
        "icon": "calendar",
        "author": "GraftAI",
    },
]


@router.get("/list", response_model=PluginListResponse)
async def list_plugins(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserTokenTable.provider).where(
        and_(
            UserTokenTable.user_id == str(user_id),
            UserTokenTable.is_active == True,
            UserTokenTable.provider.in_(["google", "microsoft"]),
        )
    )
    result = await db.execute(stmt)
    active_providers = {provider for provider in result.scalars().all() if provider}

    plugins: List[PluginInfo] = []
    for plugin in PLUGIN_CATALOG:
        plugins.append(
            PluginInfo(
                id=plugin["id"],
                name=plugin["name"],
                description=plugin["description"],
                version=plugin["version"],
                category=plugin["category"],
                icon=plugin["icon"],
                installed=plugin["id"] in active_providers,
                author=plugin.get("author"),
            )
        )

    return PluginListResponse(plugins=plugins)
