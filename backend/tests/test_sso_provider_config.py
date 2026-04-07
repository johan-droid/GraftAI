from fastapi import HTTPException
import pytest

from backend.services import sso


@pytest.mark.asyncio
async def test_start_oauth2_flow_unconfigured_provider_returns_503(monkeypatch):
    original_config = sso.PROVIDERS["microsoft"].copy()
    monkeypatch.setitem(sso.PROVIDERS["microsoft"], "client_id", None)
    monkeypatch.setitem(sso.PROVIDERS["microsoft"], "client_secret", None)

    try:
        await sso.start_oauth2_flow("microsoft", "/dashboard")
        assert False, "Expected HTTPException for unavailable provider"
    except HTTPException as exc:
        assert exc.status_code == 503
        assert "currently unavailable" in str(exc.detail)
    finally:
        sso.PROVIDERS["microsoft"] = original_config