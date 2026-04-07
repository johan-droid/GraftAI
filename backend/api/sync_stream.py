import asyncio
import json
import logging
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import StreamingResponse
from backend.auth.schemes import get_current_user_id
from backend.services.redis_client import subscribe

router = APIRouter(prefix="/calendar", tags=["calendar"])
logger = logging.getLogger(__name__)

async def status_event_generator(request: Request, user_id: str):
    # Unified User Event Channel
    channel = f"sse:user:{user_id}"
    pubsub = await subscribe(channel)
    
    try:
        # Initial ping to confirm connection
        yield f"data: {json.dumps({'event': 'CONNECTED', 'status': 'online'})}\n\n"
        
        while not await request.is_disconnected():
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=2.0)
            if message and message.get('data'):
                data = message['data']
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                
                # Relay the JSON/String data directly as an SSE event
                # This catches 'SYNC_STATUS' objects or generic 'QUOTA_UPDATE' drops natively.
                yield f"data: {data}\n\n"
            
            await asyncio.sleep(0.02) # Yield control
    except Exception as e:
        logger.error(f"SSE stream error for {user_id}: {e}")
        yield f"data: {json.dumps({'event': 'ERROR', 'detail': str(e)})}\n\n"
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()

@router.get("/sync/stream")
async def sync_stream(
    request: Request, 
    user_id: str = Depends(get_current_user_id),
    token: str = Query(None) # Added for EventSource compatibility
):
    """
    Server-Sent Events (SSE) Global Stream Endpoint.
    Acts as a persistent socket to push realtime Quotas, Billing, and Calendar changes.
    """
    return StreamingResponse(
        status_event_generator(request, user_id),
        media_type="text/event-stream"
    )
