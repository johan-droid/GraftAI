from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from typing import Optional
import os
import httpx

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM = "HS256"

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")
AUTH0_ISSUER = os.getenv("AUTH0_ISSUER", f"https://{AUTH0_DOMAIN}/") if AUTH0_DOMAIN else ""

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def _get_auth0_jwk(token: str) -> dict:
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise JWTError("Missing kid in token header")

    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    try:
        response = httpx.get(jwks_url, timeout=5.0)
        response.raise_for_status()
        jwks = response.json()
    except Exception as exc:
        raise JWTError(f"Unable to fetch JWKS from Auth0: {exc}")

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise JWTError("Appropriate key not found in Auth0 JWKS")


def decode_token(token: str) -> Optional[dict]:
    # If Auth0 variables are configured, use RS256 and JWKS-based validation.
    if AUTH0_DOMAIN and AUTH0_AUDIENCE:
        try:
            jwk = _get_auth0_jwk(token)
            payload = jwt.decode(
                token,
                jwk,
                algorithms=["RS256"],
                audience=AUTH0_AUDIENCE,
                issuer=AUTH0_ISSUER,
            )
            return payload
        except JWTError:
            return None

    # Fallback to local symmetric JWT strategy.
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
