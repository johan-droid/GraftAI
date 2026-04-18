#!/usr/bin/env python3
"""
Security Fixes Test Suite
Run after applying Phase 1 & 2 security fixes
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select
from backend.utils.db import AsyncSessionLocal
from backend.models.tables import UserTable, BookingTable, generate_uuid


async def test_database_columns():
    """Test H-03: Stripe columns exist"""
    print("\n🔍 Testing H-03: Stripe column separation...")
    async with AsyncSessionLocal() as db:
        # Check if columns exist by querying
        stmt = select(UserTable).limit(1)
        await db.execute(stmt)
        # Check columns exist
        assert hasattr(UserTable, 'stripe_customer_id'), "stripe_customer_id column missing"
        assert hasattr(UserTable, 'stripe_subscription_id'), "stripe_subscription_id column missing"
        assert hasattr(UserTable, 'razorpay_customer_id'), "razorpay_customer_id column missing"
        print("   ✅ Stripe and Razorpay columns both exist")


async def test_booking_persistence():
    """Test C-01: Bookings persist to database"""
    print("\n🔍 Testing C-01: Booking persistence...")
    async with AsyncSessionLocal() as db:
        # Create test booking
        booking = BookingTable(
            id=generate_uuid(),
            user_id="test_user_123",
            full_name="Test User",
            email="test@example.com",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            status="confirmed",
            metadata_payload={"title": "Test Booking", "description": "Security test"}
        )
        
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        
        # Verify it exists
        stmt = select(BookingTable).where(BookingTable.id == booking.id)
        result = await db.execute(stmt)
        found = result.scalars().first()
        
        assert found is not None, "Booking not found in database!"
        assert found.id == booking.id, "Booking ID mismatch"
        assert found.metadata_payload.get("title") == "Test Booking"
        print(f"   ✅ Booking persisted with ID: {booking.id[:8]}...")
        
        # Cleanup
        await db.delete(found)
        await db.commit()


async def test_access_control_whitelist():
    """Test H-09: Attribute whitelist"""
    print("\n🔍 Testing H-09: Access control whitelist...")
    from backend.services.access_control import ALLOWED_ATTRIBUTES
    
    # Verify whitelist exists and has expected values
    assert "tier" in ALLOWED_ATTRIBUTES
    assert "subscription_status" in ALLOWED_ATTRIBUTES
    assert "password_hash" not in ALLOWED_ATTRIBUTES, "password_hash should NOT be whitelisted"
    assert "mfa_secret" not in ALLOWED_ATTRIBUTES, "mfa_secret should NOT be whitelisted"
    print("   ✅ Attribute whitelist correctly configured")


def test_nextauth_secret_validation():
    """Test C-03: NextAuth secret validation"""
    print("\n🔍 Testing C-03: NextAuth secret validation...")
    
    # Read the auth.ts file
    auth_ts_path = os.path.join(os.path.dirname(__file__), 'frontend', 'src', 'auth.ts')
    with open(auth_ts_path, 'r') as f:
        content = f.read()
    
    # Verify no hardcoded fallback
    assert 'your-development-fallback-secret-here' not in content, "Hardcoded secret found!"
    assert 'getNextAuthSecret' in content, "getNextAuthSecret function missing"
    assert 'NEXTAUTH_SECRET' in content, "NEXTAUTH_SECRET check missing"
    print("   ✅ NextAuth secret properly validated")


def test_worker_cron_syntax():
    """Test H-07: Worker cron job syntax"""
    print("\n🔍 Testing H-07: Worker cron job syntax...")
    
    worker_path = os.path.join(os.path.dirname(__file__), 'backend', 'worker.py')
    with open(worker_path, 'r') as f:
        content = f.read()
    
    # Verify proper cron() function calls
    assert 'from arq import cron' in content, "arq cron import missing"
    assert 'cron(task_sync_all_users' in content, "cron() function call missing"
    assert '{"coroutine":' not in content, "Dict literal cron syntax found (should use cron() function)"
    print("   ✅ Worker cron jobs use proper syntax")


def test_server_auth_cookies():
    """Test H-10: Single cookie system"""
    print("\n🔍 Testing H-10: Cookie standardization...")
    
    server_auth_path = os.path.join(os.path.dirname(__file__), 'frontend', 'src', 'lib', 'server-auth.ts')
    with open(server_auth_path, 'r') as f:
        content = f.read()
    
    # Verify single cookie system
    assert 'graftai_access_token' in content, "Primary cookie name missing"
    assert 'auth_token", ""' in content, "Legacy cookie cleanup missing"
    # Check that we're not setting both cookies with values
    set_calls = content.count('response.cookies.set("graftai_access_token"')
    assert set_calls >= 1, "Primary cookie not being set"
    print("   ✅ Single cookie system implemented")


async def run_all_tests():
    """Run all security tests"""
    print("=" * 60)
    print("🔒 SECURITY FIXES TEST SUITE")
    print("=" * 60)
    
    try:
        # Database tests
        await test_database_columns()
        await test_booking_persistence()
        await test_access_control_whitelist()
        
        # File-based tests
        test_nextauth_secret_validation()
        test_worker_cron_syntax()
        test_server_auth_cookies()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
