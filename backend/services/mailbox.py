import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from anyio import to_thread

from backend.models.tables import UserTokenTable
from backend.services.integrations.google_calendar import get_google_credentials
from backend.services.integrations.ms_graph import get_ms_graph_token
from backend.services.token_encryption import decrypt_token_value

logger = logging.getLogger(__name__)


async def get_recent_emails(db: AsyncSession, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    emails = []

    stmt = select(UserTokenTable).where(
        and_(
            UserTokenTable.user_id == user_id,
            UserTokenTable.is_active == True,
        )
    )
    result = await db.execute(stmt)
    tokens = result.scalars().all()

    for token in tokens:
        try:
            if token.provider == "google":
                google_emails = await _fetch_gmail_recent(token, limit)
                emails.extend(google_emails)
            elif token.provider == "microsoft":
                ms_emails = await _fetch_outlook_recent(token, limit)
                emails.extend(ms_emails)
        except Exception as e:
            logger.error(f"Failed to fetch emails from {token.provider} for {user_id}: {e}")

    return emails


async def _fetch_gmail_recent(token: UserTokenTable, limit: int) -> List[Dict[str, Any]]:
    from googleapiclient.discovery import build

    access_token, _ = decrypt_token_value(token.access_token)
    refresh_token, _ = decrypt_token_value(token.refresh_token)

    if access_token is None or refresh_token is None:
        logger.error(f"Cannot sync Gmail. Token decryption failed for token ID {token.id}")
        return []

    token_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "scopes": getattr(token, "scopes", None),
    }
    creds = get_google_credentials(token_data)

    def sync_fetch() -> List[Dict[str, Any]]:
        service = build("gmail", "v1", credentials=creds)

        results = service.users().messages().list(userId="me", maxResults=limit).execute()
        messages = results.get("messages", [])

        fetched_emails: List[Dict[str, Any]] = []
        for msg in messages:
            m = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            headers = m.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
            snippet = m.get("snippet", "")

            fetched_emails.append({
                "source": "gmail",
                "subject": subject,
                "from": sender,
                "snippet": snippet,
                "id": msg["id"],
            })
        return fetched_emails

    return await to_thread.run_sync(sync_fetch)


async def _fetch_outlook_recent(token: UserTokenTable, limit: int) -> List[Dict[str, Any]]:
    access_token, _ = decrypt_token_value(token.access_token)
    refresh_token, _ = decrypt_token_value(token.refresh_token)

    if access_token is None or refresh_token is None:
        logger.error(f"Cannot sync Outlook. Token decryption failed for token ID {token.id}")
        return []

    token_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "scopes": getattr(token, "scopes", None),
    }
    access_token = get_ms_graph_token(token_data)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    from backend.utils.http_client import get_client

    client = await get_client()

    resp = await client.get(
        f"https://graph.microsoft.com/v1.0/me/messages?$top={limit}&$select=subject,from,bodyPreview",
        headers=headers,
    )

    if resp.status_code != 200:
        logger.error(f"Outlook fetch error: {resp.status_code}")
        return []

    data = resp.json()
    messages = data.get("value", [])

    fetched_emails = []
    for msg in messages:
        fetched_emails.append({
            "source": "outlook",
            "subject": msg.get("subject"),
            "from": msg.get("from", {}).get("emailAddress", {}).get("address"),
            "snippet": msg.get("bodyPreview"),
            "id": msg.get("id"),
        })

    return fetched_emails
