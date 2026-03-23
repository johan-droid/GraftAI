from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from jose import jwt
from datetime import datetime, timedelta
import os

from backend.services import sso, passwordless, mfa, access_control, fido2_did

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
AUTH_METHODS = [m.strip() for m in os.getenv("AUTH_METHODS", "sso,passwordless,mfa").split(",") if m.strip()]

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Pydantic Request Models ──

class FIDO2AssertionRequest(BaseModel):
    user_id: int
    assertion: dict = {}

class FIDO2AttestationRequest(BaseModel):
    user_id: int
    attestation: dict = {}

class DIDVerifyRequest(BaseModel):
    user_id: int
    did: str


def _create_jwt_token(sub: str):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode({
        "sub": sub,
        "exp": datetime.utcnow() + access_token_expires
    }, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # A safe default fallback user for quick startup.
    if form_data.username != "admin" or form_data.password != "password":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    return _create_jwt_token(form_data.username)


@router.get("/sso/start")
def sso_start(provider: str = "github", redirect_to: str = "/dashboard"):
    try:
        return sso.start_oauth2_flow(provider=provider, redirect_to=redirect_to)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.get("/sso/callback")
def sso_callback(code: str, state: str):
    try:
        payload = sso.complete_oauth2_flow(code=code, state=state)
        own_token = _create_jwt_token(str(payload["profile"].get("id", "unknown")))
        return {"auth": payload, "token": own_token, "redirect_to": payload.get("redirect_to", "/dashboard")}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/passwordless/request")
def _passwordless_request(email: str):
    return passwordless.request_magic_link(email)


@router.post("/passwordless/verify")
def _passwordless_verify(email: str, code: str):
    if not passwordless.verify_magic_link_code(email, code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")
    return _create_jwt_token(email)


@router.post("/mfa/setup")
def _mfa_setup(user_id: int):
    return mfa.start_mfa_enrollment(user_id)


@router.post("/mfa/verify")
def _mfa_verify(user_id: int, token: str):
    if not mfa.verify_mfa_token(user_id, token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP token")
    return {"status": "success"}


@router.get("/fido2/register")
def _fido2_start(user_id: int):
    return fido2_did.start_fido2_registration(user_id)


@router.post("/fido2/register")
def _fido2_complete(request: FIDO2AttestationRequest):
    if not fido2_did.complete_fido2_registration(request.user_id, request.attestation):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="FIDO2 registration failed")
    return {"status": "registered"}


@router.post("/fido2/verify")
def _fido2_verify(request: FIDO2AssertionRequest):
    if not fido2_did.verify_fido2_assertion(request.user_id, request.assertion):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="FIDO2 assertion failed")
    return {"status": "verified"}


@router.post("/did/issue")
def _did_issue(user_id: int):
    return {"did": fido2_did.issue_decentralized_id(user_id)}


@router.post("/did/verify")
def _did_verify(request: DIDVerifyRequest):
    valid = fido2_did.verify_decentralized_id(request.user_id, request.did)
    if not valid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DID not found")
    return {"status": "valid"}


@router.post("/authenticate")
def authenticate(request: Request):
    # Fallback chain execution across multiple auth methods.
    errors = {}

    for method in AUTH_METHODS:
        try:
            if method == "sso":
                code = request.query_params.get("code")
                state = request.query_params.get("state")
                if code and state:
                    return sso_callback(code=code, state=state)
                raise RuntimeError("SSO requires code/state query params")
            if method == "passwordless":
                email = request.query_params.get("email")
                code = request.query_params.get("code")
                if email and code and passwordless.verify_magic_link_code(email, code):
                    return _create_jwt_token(email)
                raise RuntimeError("Passwordless failed")
            if method == "mfa":
                user_id = request.query_params.get("user_id")
                token = request.query_params.get("token")
                if user_id and token and mfa.verify_mfa_token(int(user_id), token):
                    return {"status": "mfa_success"}
                raise RuntimeError("MFA failed")
        except Exception as e:
            errors[method] = str(e)
            continue

    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"fallback_errors": errors})


@router.get("/access-control/check-role")
def check_role(user_id: int, role: str):
    return {"allowed": access_control.check_user_role(user_id, role)}


@router.get("/access-control/check-attribute")
def check_attribute(user_id: int, attribute: str, value: str):
    return {"allowed": access_control.check_user_attribute(user_id, attribute, value)}


from backend.auth.schemes import get_current_user


@router.get("/check")
def check_auth(current_user=Depends(get_current_user)):
    # returns user payload if authenticated
    return {"authenticated": True, "user": current_user}
