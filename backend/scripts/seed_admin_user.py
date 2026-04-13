import argparse
import asyncio
import getpass
import os
import sys
from typing import Optional

from sqlalchemy import select

from backend.models.tables import UserTable
from backend.utils.db import get_async_session_maker


def parse_args():
    parser = argparse.ArgumentParser(description="Seed an admin user into the database.")
    parser.add_argument("--email", required=False, help="Admin user email")
    parser.add_argument("--password", required=False, help="Admin user password")
    parser.add_argument("--username", required=False, help="Admin username")
    return parser.parse_args()


async def seed_admin(email: str, username: Optional[str] = None) -> None:
    SessionLocal = get_async_session_maker()
    async with SessionLocal() as session:
        existing = await session.execute(
            select(UserTable.id).where(UserTable.email == email)
        )
        if existing.scalars().first():
            print(f"User with email {email} already exists. No changes made.")
            return

        user = UserTable(
            email=email,
            username=username,
            full_name=username or email.split("@")[0],
            hashed_password=None,
            email_verified=True,
            tier="elite",
            subscription_status="active",
            trial_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"✅ Admin user seeded: {email} (elite tier)")


if __name__ == "__main__":
    args = parse_args()

    email = args.email or os.getenv("ADMIN_EMAIL")
    username = args.username or os.getenv("ADMIN_USERNAME")

    if not email:
        email = input("Admin email to seed: ").strip()

    if not email:
        print("ERROR: email is required.")
        sys.exit(1)

    try:
        asyncio.run(seed_admin(email, username))
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
