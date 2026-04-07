import os
import logging
from typing import Dict, Any
from fastapi import Request
from urllib.parse import urlparse
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings

logger = logging.getLogger(__name__)

def get_saml_settings() -> Dict[str, Any]:
    """
    Constructs the SAML settings from environment variables.
    In a SaaS-grade system, these might eventually be fetched from a database per tenant.
    """
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    # SP Settings
    sp_entity_id = os.getenv("SAML_SP_ENTITY_ID", f"{base_url}/api/v1/auth/saml/metadata")
    acs_url = f"{base_url}/api/v1/auth/saml/acs"
    
    # IdP Settings
    idp_entity_id = os.getenv("SAML_IDP_ENTITY_ID")
    idp_sso_url = os.getenv("SAML_IDP_SSO_URL")
    idp_x509_cert = os.getenv("SAML_IDP_X509_CERT")

    settings = {
        "strict": True,
        "debug": os.getenv("DEBUG", "False").lower() == "true",
        "sp": {
            "entityId": sp_entity_id,
            "assertionConsumerService": {
                "url": acs_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            },
            "singleLogoutService": {
                "url": f"{base_url}/api/v1/auth/saml/sls",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "x509cert": os.getenv("SAML_SP_X509_CERT", ""),
            "privateKey": os.getenv("SAML_SP_PRIVATE_KEY", ""),
        },
        "idp": {
            "entityId": idp_entity_id,
            "singleSignOnService": {
                "url": idp_sso_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "x509cert": idp_x509_cert,
        },
        "security": {
            "nameIdEncrypted": False,
            "authnRequestsSigned": False,
            "logoutRequestSigned": False,
            "logoutResponseSigned": False,
            "signMetadata": False,
            "wantMessagesSigned": False,
            "wantAssertionsSigned": True,
            "wantNameId": True,
            "wantNameIdEncrypted": False,
            "wantAssertionsEncrypted": False,
            "signatureAlgorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
            "digestAlgorithm": "http://www.w3.org/2001/04/xmlenc#sha256"
        }
    }
    return settings

def validate_relay_state(relay_state: str) -> bool:
    """
    Validates the RelayState to prevent open redirect vulnerabilities.
    Only allows redirects to paths within the app or known frontend domains.
    """
    if not relay_state:
        return True
    
    # Allow relative paths
    if relay_state.startswith("/") and not relay_state.startswith("//"):
        return True
        
    # Allow explicit frontend/backend domains
    allowed = {
        urlparse(os.getenv("FRONTEND_URL", "")).netloc,
        urlparse(os.getenv("BACKEND_URL", "")).netloc,
        "localhost",
        "127.0.0.1"
    }
    
    try:
        parsed = urlparse(relay_state)
        return parsed.netloc in allowed
    except Exception:
        return False

async def prepare_saml_request(request: Request) -> Dict[str, Any]:
    """
    Transforms a FastAPI/Starlette Request into the format expected by python3-saml.
    Handles proxy headers (X-Forwarded-Proto, X-Forwarded-Host) for production compatibility.
    """
    is_https = request.url.scheme == 'https' or request.headers.get('x-forwarded-proto') == 'https'
    
    # Use headers for host and port if behind a proxy
    host = request.headers.get('x-forwarded-host') or request.url.hostname
    port = request.headers.get('x-forwarded-port') or request.url.port
    
    if not port:
        port = 443 if is_https else 80

    # For ACS (POST), we need form data
    post_data = {}
    if request.method == "POST":
        post_data = await request.form()
        post_data = dict(post_data)

    return {
        'https': 'on' if is_https else 'off',
        'http_host': host,
        'server_port': str(port),
        'script_name': request.url.path,
        'get_data': dict(request.query_params),
        'post_data': post_data,
        'query_string': request.url.query
    }

def get_saml_auth(request_data: Dict[str, Any]) -> OneLogin_Saml2_Auth:
    """Returns an instance of OneLogin_Saml2_Auth with the SP/IdP settings."""
    settings = get_saml_settings()
    return OneLogin_Saml2_Auth(request_data, settings)

def generate_sp_metadata() -> str:
    """Returns the SP metadata XML for distribution to IdP admins."""
    settings_dict = get_saml_settings()
    settings = OneLogin_Saml2_Settings(settings_dict)
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)
    
    if errors:
        logger.error(f"SAML Metadata validation errors: {errors}")
        raise ValueError(f"Invalid SAML Metadata: {', '.join(errors)}")
        
    return metadata
