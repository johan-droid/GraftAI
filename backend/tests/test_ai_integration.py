import pytest
from datetime import datetime, timezone
from backend.services import ai
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace


@pytest.mark.asyncio
async def test_proactive_context_injection():
    # Setup: Mock DB and Cache
    user_id = 999
    db_mock = AsyncMock(spec=AsyncSession)

    # Mock scheduler.get_events_for_range
    with patch(
        "backend.services.scheduler.get_events_for_range", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = [
            SimpleNamespace(id=1, title="Existing Sync", start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc))
        ]

        # Test AI Request
        request = ai.AIRequest(prompt="Give me a strategic summary for the next 48 hours.", timezone="UTC")

        # Mock Cache
        with patch("backend.services.ai.get_cache", return_value=None), patch(
            "backend.services.ai.set_cache"
        ), patch(
            "backend.services.ai._generate_with_groq_response", new_callable=AsyncMock
        ) as mock_gen:

            mock_gen.return_value = ("You have a sync.", "llama-3.3-70b-versatile")
            await ai.ai_chat(request, user_id=user_id, db=db_mock)

            # Verify the system prompt sent to the LLM contains our 'GROUND TRUTH'
            # In ai_chat, _generate_with_groq_response args are (system_reasoning, user_input)
            # Access args safely regardless of mock type
            called_args = mock_gen.call_args[0] if mock_gen.call_args else []
            if not called_args and mock_gen.await_args:
                called_args = mock_gen.await_args[0]
            
            if called_args:
                system_prompt = called_args[0]
                assert "AUTHORITATIVE CONTEXT" in system_prompt
            else:
                pytest.fail("mock_gen was not called correctly")


@pytest.mark.asyncio
async def test_ai_chat_returns_response_when_usage_increment_fails():
    user_id = 999
    db_mock = AsyncMock(spec=AsyncSession)
    request = ai.AIRequest(prompt="Summarize my next 3 meetings.", timezone="UTC")

    with patch("backend.services.ai.get_cache", return_value=None), patch(
        "backend.services.ai.set_cache"
    ), patch("backend.services.ai._generate_with_groq_response", new_callable=AsyncMock) as mock_gen, patch(
        "backend.services.ai.increment_usage", new_callable=AsyncMock
    ) as mock_usage, patch(
        "backend.services.scheduler.get_events_for_range", new_callable=AsyncMock
    ) as mock_events, patch(
        "backend.services.ai.get_recent_emails", new_callable=AsyncMock
    ) as mock_emails:
        mock_gen.return_value = ("Here are your upcoming meetings.", "llama-3.3-70b-versatile")
        mock_usage.side_effect = RuntimeError("usage db unavailable")
        mock_events.return_value = []
        mock_emails.return_value = []

        response = await ai.ai_chat(request, user_id=user_id, db=db_mock)

        assert response.result == "Here are your upcoming meetings."
        assert response.model_used.startswith("graftai-assistant-online")
        mock_usage.assert_awaited_once()


@pytest.mark.asyncio
async def test_multi_action_parsing():
    user_id = 999
    db_mock = AsyncMock(spec=AsyncSession)

    # Test UPDATE parsing
    request = ai.AIRequest(prompt="Move my 2pm meeting to 4pm", timezone="UTC")
    with patch("backend.services.ai.get_cache", return_value=None), patch(
        "backend.services.ai.set_cache"
    ), patch(
        "backend.services.ai._generate_with_groq", new_callable=AsyncMock
    ) as mock_gen, patch(
        "backend.services.ai._resolve_event_id", new_callable=AsyncMock
    ) as mock_resolve:
        mock_resolve.return_value = None

        mock_gen.return_value = 'Rescheduling. ACTION:UPDATE_MEETING:{"event_id": 1, "new_start_time": "2026-03-25T16:00:00"}'

        with patch(
            "backend.services.scheduler.update_event", new_callable=AsyncMock
        ) as mock_update:
            await ai.ai_chat(request, user_id=user_id, db=db_mock)
            # Ensure the call was made despite any extra text in the AI response
            mock_update.assert_called_once()


def test_extract_json_payload_from_prefixed_text():
    raw = 'Rescheduling now. ACTION:UPDATE_MEETING:{"event_id": 42, "new_start_time": "2026-03-25T16:00:00"}'
    payload = ai._extract_json_payload(raw)
    assert isinstance(payload, dict)
    assert payload.get("event_id") == 42


@pytest.mark.asyncio
async def test_offline_update_still_works_when_groq_unavailable():
    db_mock = AsyncMock(spec=AsyncSession)
    prompt = "Update event 15 to tomorrow at 4pm"

    updated_event = SimpleNamespace(
        id=15,
        start_time=datetime(2026, 4, 8, 16, 0, tzinfo=timezone.utc),
    )

    with patch("backend.services.ai._generate_with_groq", new_callable=AsyncMock) as mock_groq, patch(
        "backend.services.scheduler.update_event", new_callable=AsyncMock
    ) as mock_update:
        mock_groq.side_effect = RuntimeError("provider unavailable")
        mock_update.return_value = updated_event

        result_text, action = await ai._offline_assistant_response(
            prompt=prompt,
            user_timezone="UTC",
            db=db_mock,
            user_id="u_1",
        )

        assert "Updated event #15" in result_text
        assert action.get("type") == "update"
        mock_update.assert_called_once()
