import pyotp
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.tables import UserTable

async def start_mfa_enrollment(db: AsyncSession, user_id: str) -> dict:
    """ Generates a new TOTP secret for user enrollment. """
    secret = pyotp.random_base32()
    # We return the secret and URI but don't save yet 
    # (waiting for verification)
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=f"user_{user_id}@graftai", issuer_name="GraftAI"
    )
    return {"secret": secret, "otp_uri": otp_uri}

async def enable_mfa(db: AsyncSession, user_id: str, secret: str) -> bool:
    """ Persists the MFA secret and enables MFA for the user. """
    user = await db.get(UserTable, user_id)
    if not user:
        return False
    
    user.mfa_secret = secret
    user.mfa_enabled = True
    await db.commit()
    return True

async def verify_mfa_token(db: AsyncSession, user_id: str, token: str, temp_secret: str = None) -> bool:
    """ Validates a TOTP token against a stored or temporary secret. """
    if temp_secret:
        secret = temp_secret
    else:
        user = await db.get(UserTable, user_id)
        if not user or not user.mfa_secret:
            return False
        secret = user.mfa_secret

    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)

def check_device_fingerprint(user_id: str, fingerprint: str) -> bool:
    return True
