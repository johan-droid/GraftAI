import pytest
from datetime import datetime, timedelta, timezone
from backend.services import ai, scheduler
from backend.models.tables import EventTable
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch, MagicMock


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
            AsyncMock(title="Existing Sync", start_time=datetime.now(timezone.utc))
        ]

        # Test AI Request
        request = ai.AIRequest(prompt="What does my day look like?", timezone="UTC")

        # Mock Cache and dependencies
        with patch("backend.services.ai.scheduler.get_optimized_context", new_callable=AsyncMock) as mock_opt, patch(
            "backend.services.ai.prefetcher.get_cached_context", new_callable=AsyncMock
        ) as mock_prefetcher, patch(
            "backend.services.ai.get_llm"
        ) as mock_get_llm:
            
            mock_prefetcher.return_value = "Your Real-Time Schedule (GROUND TRUTH): Existing Sync"

            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm
            mock_llm_with_tools = MagicMock()
            mock_llm.bind_tools.return_value = mock_llm_with_tools

            async def dummy_astream(messages, *args, **kwargs):
                # Capture the messages for assertion
                dummy_astream.captured_messages = messages
                from types import SimpleNamespace
                yield SimpleNamespace(content="You have a sync.")
            
            mock_llm_with_tools.astream = dummy_astream

            response = await ai.ai_chat(request, user_id=str(user_id), db=db_mock, org_id=1, workspace_id=1)
            
            # Consume the StreamingResponse
            async for _ in response.body_iterator:
                pass

            # Verify the system prompt sent to the LLM contains our 'GROUND TRUTH'
            captured = getattr(dummy_astream, "captured_messages", [])
            if captured:
                system_prompt_msg = captured[0]
                assert "Your Real-Time Schedule (GROUND TRUTH):" in system_prompt_msg.content
            else:
                pytest.fail("astream was not called with messages")


@pytest.mark.asyncio
async def test_multi_action_parsing():
    user_id = "999"
    db_mock = AsyncMock(spec=AsyncSession)

    # Test UPDATE parsing
    request = ai.AIRequest(prompt="Move my 2pm meeting to 4pm", timezone="UTC")
    with patch("backend.services.ai.scheduler.get_optimized_context", new_callable=AsyncMock), patch(
        "backend.services.ai.prefetcher.get_cached_context", new_callable=AsyncMock
    ), patch(
        "backend.services.ai.get_llm"
    ) as mock_get_llm:

        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        mock_llm_with_tools = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm_with_tools

        async def dummy_astream(*args, **kwargs):
            from types import SimpleNamespace
            # Yielding a tool call structure
            yield SimpleNamespace(
                content="", 
                tool_call_chunks=[{
                    "index": 0, 
                    "name": "UpdateMeeting", 
                    "args": '{"event_id": 1, "new_start_time": "2026-03-25T16:00:00"}'
                }]
            )
        
        mock_llm_with_tools.astream = dummy_astream

        with patch(
            "backend.services.scheduler.update_event", new_callable=AsyncMock
        ) as mock_update:
            response = await ai.ai_chat(request, user_id=user_id, db=db_mock, org_id=1, workspace_id=1)
            async for _ in response.body_iterator:
                pass
            
            # Ensure the call was made
            mock_update.assert_called_once()
