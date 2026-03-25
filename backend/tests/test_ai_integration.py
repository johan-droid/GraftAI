import pytest
from datetime import datetime, timedelta
from backend.services import ai, scheduler
from backend.models.tables import EventTable
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch


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
            AsyncMock(title="Existing Sync", start_time=datetime.now())
        ]

        # Test AI Request
        request = ai.AIRequest(prompt="What does my day look like?", timezone="UTC")

        # Mock Cache
        with patch("backend.services.ai.get_cache", return_value=None), patch(
            "backend.services.ai.set_cache"
        ), patch(
            "backend.services.ai._generate_with_groq", new_callable=AsyncMock
        ) as mock_gen:

            mock_gen.return_value = "You have a sync."
            await ai.ai_chat(request, user_id=user_id, db=db_mock)

            # Verify the system prompt sent to the LLM contains our 'GROUND TRUTH'
            # In new ai_chat, _generate_with_groq args are (system_reasoning, user_input)
            # Access args safely regardless of mock type
            called_args = mock_gen.call_args[0] if mock_gen.call_args else []
            if not called_args and mock_gen.await_args:
                called_args = mock_gen.await_args[0]
            
            if called_args:
                system_prompt = called_args[0]
                assert "Your Real-Time Schedule (GROUND TRUTH):" in system_prompt
            else:
                pytest.fail("mock_gen was not called correctly")


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
    ) as mock_gen:

        mock_gen.return_value = 'Rescheduling. ACTION:UPDATE_MEETING:{"event_id": 1, "new_start_time": "2026-03-25T16:00:00"}'

        with patch(
            "backend.services.scheduler.update_event", new_callable=AsyncMock
        ) as mock_update:
            await ai.ai_chat(request, user_id=user_id, db=db_mock)
            # Ensure the call was made despite any extra text in the AI response
            mock_update.assert_called_once()
