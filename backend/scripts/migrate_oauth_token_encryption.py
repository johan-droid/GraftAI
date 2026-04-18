"""
Encrypt existing plaintext OAuth tokens stored in user_tokens.

This script is safe to run multiple times:
- Plaintext rows are upgraded to encrypted values.
- Already encrypted rows are left unchanged.
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

# Add repo root to import path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.tables import UserTokenTable
from backend.services.token_encryption import (
    decrypt_token_value,
    encrypt_token_value,
    token_encryption_enabled,
)
from backend.utils.db import get_async_session_maker


async def migrate_oauth_token_encryption() -> None:
    if not token_encryption_enabled():
        print(
            "Token encryption is not configured. Set OAUTH_TOKEN_ENCRYPTION_KEY or SECRET_KEY."
        )
        return

    session_maker = get_async_session_maker()

    scanned = 0
    migrated = 0
    unchanged = 0
    unreadable = 0

    async with session_maker() as db:
        result = await db.execute(select(UserTokenTable))
        records = result.scalars().all()

        for record in records:
            scanned += 1
            changed = False

            access_plain, access_needs_upgrade = decrypt_token_value(
                record.access_token
            )
            if record.access_token and access_plain is None:
                unreadable += 1
            elif access_needs_upgrade and access_plain:
                encrypted_access_token = encrypt_token_value(access_plain)
                if encrypted_access_token is None:
                    raise RuntimeError(
                        f"Failed to encrypt access_token for token ID {record.id}"
                    )
                record.access_token = encrypted_access_token
                changed = True

            refresh_plain, refresh_needs_upgrade = decrypt_token_value(
                record.refresh_token
            )
            if record.refresh_token and refresh_plain is None:
                unreadable += 1
            elif refresh_needs_upgrade and refresh_plain:
                encrypted_refresh_token = encrypt_token_value(refresh_plain)
                if encrypted_refresh_token is None:
                    raise RuntimeError(
                        f"Failed to encrypt refresh_token for token ID {record.id}"
                    )
                record.refresh_token = encrypted_refresh_token
                changed = True
                changed = True

            if changed:
                migrated += 1
            else:
                unchanged += 1

        await db.commit()

    print("OAuth token encryption migration complete")
    print(f"Scanned: {scanned}")
    print(f"Migrated: {migrated}")
    print(f"Unchanged: {unchanged}")
    print(f"Unreadable: {unreadable}")


if __name__ == "__main__":
    asyncio.run(migrate_oauth_token_encryption())
