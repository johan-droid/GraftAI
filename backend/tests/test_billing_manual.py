import os
import pytest
import uuid
from sqlalchemy import select

from backend.models.tables import ManualActivationRequestTable, UserTable
import backend.services.storage as storage_module


@pytest.mark.asyncio
async def test_create_manual_request_sends_admin_email(async_client, db_session, test_user, monkeypatch):
    sent = []

    async def fake_send_email(to_email, subject, html_body, text_body=None):
        sent.append((to_email, subject))

    monkeypatch.setattr("backend.api.billing.send_email", fake_send_email)

    payload = {
        "requested_tier": "pro",
        "proof_key": "proofs/manual-proof.png",
        "notes": "Student needs manual approval",
    }

    resp = await async_client.post("/api/v1/billing/manual/request", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "success"
    request_id = data.get("request_id")
    assert request_id

    # Verify DB entry exists
    stmt = select(ManualActivationRequestTable).where(ManualActivationRequestTable.id == request_id)
    result = await db_session.execute(stmt)
    req = result.scalars().first()
    assert req is not None
    assert req.status == "pending"

    # Verify admin email was invoked
    admin_email = os.getenv("ADMIN_EMAIL", "admin@graftai.com")
    assert sent and sent[0][0] == admin_email


@pytest.mark.asyncio
async def test_presign_manual_upload_endpoint_returns_payload(async_client, db_session, test_user):
    # Attempt to generate a presigned upload payload
    payload = {"filename": "proof.png", "content_type": "image/png"}
    resp = await async_client.post("/api/v1/billing/manual/presign", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # Either a backend upload instruction or a presigned put URL is acceptable
    assert "method" in data
    assert data["method"] in {"put", "backend"}
    # If 'put', must include an upload_url
    if data["method"] == "put":
        assert data.get("upload_url")
        assert data.get("key")
    else:
        assert data.get("upload_endpoint") == "/api/v1/uploads"
        assert data.get("key")


@pytest.mark.asyncio
async def test_presign_manual_upload_missing_filename_returns_422(async_client, db_session, test_user):
    resp = await async_client.post("/api/v1/billing/manual/presign", json={})
    assert resp.status_code == 422
    data = resp.json()
    assert any(
        detail.get("loc") and "filename" in detail.get("loc")
        for detail in data.get("detail", [])
    )


@pytest.mark.asyncio
async def test_presign_manual_upload_invalid_content_type_returns_422(async_client, db_session, test_user):
    payload = {"filename": "proof.png", "content_type": 123}
    resp = await async_client.post("/api/v1/billing/manual/presign", json=payload)
    assert resp.status_code == 422
    data = resp.json()
    assert any(
        detail.get("loc") and "content_type" in detail.get("loc")
        for detail in data.get("detail", [])
    )


@pytest.mark.asyncio
async def test_presign_manual_upload_returns_500_when_storage_fails(async_client, db_session, test_user, monkeypatch):
    monkeypatch.setattr(storage_module.storage, "get_presigned_upload_url", lambda *_args, **_kwargs: None)

    payload = {"filename": "proof.png", "content_type": "image/png"}
    resp = await async_client.post("/api/v1/billing/manual/presign", json=payload)
    assert resp.status_code == 500
    data = resp.json()
    assert data.get("detail") == "Could not generate presigned upload URL"
