import logging
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from backend.utils.db import get_db
from backend.models.tables import UserTable
from backend.auth import logic
from backend.auth.saml_service import (
    prepare_saml_request, 
    get_saml_auth, 
    generate_sp_metadata,
    validate_relay_state
)

router = APIRouter(tags=["auth-saml"])
logger = logging.getLogger(__name__)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

@router.get("/saml/metadata")
async def saml_metadata():
    """Returns the Service Provider (SP) metadata XML for IdP configuration."""
    try:
        xml = generate_sp_metadata()
        return Response(content=xml, media_type="application/xml")
    except Exception as e:
        logger.error(f"SAML Metadata generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate SAML metadata")

@router.get("/saml/login")
async def saml_login(request: Request, redirect_to: str = "/dashboard"):
    """
    Initiates the SAML Auth flow by redirecting the user to the IdP's SSO URL.
    """
    try:
        request_data = await prepare_saml_request(request)
        auth = get_saml_auth(request_data)
        
        # redirect_to is stored in the RelayState parameter
        login_url = auth.login(return_to=redirect_to)
        return RedirectResponse(url=login_url)
    except Exception as e:
        logger.error(f"SAML Login initiation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate SAML login")

@router.post("/saml/acs")
async def saml_acs(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Assertion Consumer Service: Receives the SAML response from the IdP.
    Validates the assertion, creates/updates the user, and issues a session.
    """
    try:
        request_data = await prepare_saml_request(request)
        auth = get_saml_auth(request_data)
        
        auth.process_response()
        errors = auth.get_errors()
        
        if errors:
            reason = auth.get_last_error_reason()
            logger.error(f"SAML ACS Validation errors: {errors}. Reason: {reason}")
            return RedirectResponse(url=f"{FRONTEND_URL}/login?error=saml_failed&reason=validation_error")

        if not auth.is_authenticated():
            logger.error("SAML Authentication failed: Not authenticated.")
            return RedirectResponse(url=f"{FRONTEND_URL}/login?error=saml_failed&reason=not_authenticated")

        # Extract attributes from SAML Assertion
        # Note: mapping depends on the IdP (Okta, Azure, etc.)
        # Default typical mappings:
        attributes = auth.get_attributes()
        # Common attribute names: 'email', 'User.Email', 'EmailAddress', 'NameID'
        email = (
            attributes.get('email', [None])[0] or 
            attributes.get('User.Email', [None])[0] or
            attributes.get('EmailAddress', [None])[0] or
            auth.get_nameid()
        )
        
        if not email:
            logger.error("SAML authentication succeeded but email was not found in assertion.")
            return RedirectResponse(url=f"{FRONTEND_URL}/login?error=email_missing")

        # UPSERT User logic
        stmt = select(UserTable).where(UserTable.email == email)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        first_name = attributes.get('FirstName', [None])[0] or attributes.get('givenname', [None])[0]
        last_name = attributes.get('LastName', [None])[0] or attributes.get('surname', [None])[0]
        display_name = attributes.get('displayName', [None])[0] or f"{first_name or ''} {last_name or ''}".strip() or email.split("@")[0]

        if not user:
            user = UserTable(
                email=email,
                full_name=display_name,
                name=display_name,
                is_active=True,
                email_verified=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                timezone="UTC",
            )
            db.add(user)
            await db.flush() # Get user ID
            logger.info(f"New SAML user created: {email}")
            
            # Welcome email / Onboarding sync
            try:
                from backend.services.bg_tasks import enqueue_welcome_email, enqueue_calendar_sync
                await enqueue_welcome_email(user_email=email, full_name=user.full_name)
                # Enqueue a baseline sync to initialize the engine for the new user
                await enqueue_calendar_sync(user_id=str(user.id))
            except Exception as onboarding_err:
                logger.warning(f"Onboarding background tasks failed for {email}: {onboarding_err}")
        else:
            # Sync profile if needed
            user.full_name = display_name or user.full_name
            user.email_verified = True
            
        await db.commit()

        # Create session tokens
        token_data = await logic.create_jwt_token(str(user.id), email=user.email)
        
        # Handle Handoff via Token Bridge or Cookies
        target_path = request_data['post_data'].get('RelayState', '/dashboard')
        
        # Security: Prevent open-redirect / SSRF via RelayState
        if not validate_relay_state(target_path):
            logger.warning(f"Invalid RelayState blocked: {target_path}")
            target_path = "/dashboard"
        
        bridge_url = logic.get_token_bridge_url(
            token_data["access_token"], 
            token_data["refresh_token"], 
            target_path
        )
        response = RedirectResponse(url=bridge_url)
        logic.set_auth_cookies(response, token_data["access_token"], token_data["refresh_token"], request)
        
        return response

    except Exception as e:
        logger.error(f"SAML ACS Processing error: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=server_error")
