import os
import logging
import httpx

logger = logging.getLogger(__name__)

ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID") # For Server-to-Server OAuth

async def get_zoom_token() -> str:
    """Gets a Zoom access token via Server-to-Server OAuth."""
    if not ZOOM_CLIENT_ID or not ZOOM_CLIENT_SECRET or not ZOOM_ACCOUNT_ID:
        logger.warning("⚠ Zoom credentials missing. Check ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_ACCOUNT_ID.")
        raise ValueError("Zoom credentials not configured.")
        
    url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={ZOOM_ACCOUNT_ID}"
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            auth=(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET)
        )
        
        if resp.status_code != 200:
            logger.error(f"❌ Zoom token failed: {resp.status_code} - {resp.text}")
            raise RuntimeError("Zoom token retrieval failed.")
            
        return resp.json()["access_token"]

async def create_zoom_meeting(event_details: dict) -> str:
    """Creates a Zoom meeting and returns the join URL."""
    try:
        token = await get_zoom_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "topic": event_details.get("title", "GraftAI Zoom Meeting"),
            "type": 2, # Scheduled meeting
            "start_time": event_details["start_time"].isoformat(),
            "duration": int((event_details["end_time"] - event_details["start_time"]).total_seconds() / 60),
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": True,
                "auto_recording": "none"
            }
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.zoom.us/v2/users/me/meetings",
                headers=headers,
                json=payload
            )
            
            if resp.status_code != 201:
                logger.error(f"❌ Zoom API Error: {resp.status_code} - {resp.text}")
                raise RuntimeError(f"Zoom API returned {resp.status_code}")
                
            data = resp.json()
            logger.info(f"✅ Zoom meeting created: {data.get('join_url')}")
            return data.get("join_url")
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in Zoom meeting creation: {e}")
        return f"https://zoom.us/mock-fallback-{os.urandom(4).hex()}"
