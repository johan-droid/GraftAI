# Plugin/Marketplace API Service
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/plugins", tags=["plugins"])


class PluginInfo(BaseModel):
    name: str
    description: str
    version: str
    author: Optional[str] = None


class PluginListResponse(BaseModel):
    plugins: List[PluginInfo]


@router.get("/list", response_model=PluginListResponse)
async def list_plugins():
    # TODO: List available plugins from registry
    return PluginListResponse(plugins=[])
