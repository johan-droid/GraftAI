from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(tags=["Plugins"])


class PluginItem(BaseModel):
    id: str
    name: str
    description: str
    version: str
    category: str
    icon: str
    installed: bool
    author: Optional[str] = None


SUPPORTED_PLUGIN_IDS = {"google", "microsoft", "zoom"}


@router.get("/plugins/list")
async def list_plugins() -> dict:
    plugins: List[PluginItem] = [
        PluginItem(
            id="google",
            name="Google Calendar",
            description="Connect your Google Calendar to sync events, meetings, and availability.",
            version="1.0.0",
            category="Calendar",
            icon="calendar",
            installed=False,
            author="Google",
        ),
        PluginItem(
            id="microsoft",
            name="Microsoft Calendar",
            description="Connect Microsoft Calendar for enterprise scheduling and availability sync.",
            version="1.0.0",
            category="Calendar",
            icon="calendar",
            installed=False,
            author="Microsoft",
        ),
        PluginItem(
            id="zoom",
            name="Zoom Meetings",
            description="Connect Zoom to create and manage meeting links from GraftAI.",
            version="1.0.0",
            category="Video",
            icon="video",
            installed=False,
            author="Zoom",
        ),
    ]

    return {"plugins": [plugin.dict() for plugin in plugins]}


@router.post("/plugins/{plugin_id}/enable")
async def enable_plugin(plugin_id: str) -> dict:
    if plugin_id not in SUPPORTED_PLUGIN_IDS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{plugin_id}' not found",
        )

    # Placeholder: actual enable/install logic can go here.
    # For now, we acknowledge the request so the frontend can show install success.
    return {"plugin_id": plugin_id, "enabled": True}
