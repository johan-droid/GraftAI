from typing import List, Optional

from fastapi import APIRouter
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
