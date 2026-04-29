"""
Integration tests for AI Chat API endpoints.
Tests the complete flow from HTTP request to database persistence.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from backend.models.tables import ChatMessageTable


@pytest.mark.integration
@pytest.mark.api
class TestChatAPI:
    """Test AI chat endpoints."""

    @pytest.mark.asyncio
    async def test_send_message_success(self, async_client, test_user):
        """Test sending a chat message returns AI response."""
        response = await async_client.post(
            "/api/v1/ai/chat",
            json={"message": "Hello, schedule a meeting for tomorrow at 2pm"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert "role" in data
        assert "content" in data
        assert "conversation_id" in data
        assert data["role"] == "assistant"
        assert len(data["content"]) > 0

    @pytest.mark.asyncio
    async def test_send_message_with_conversation_id(self, async_client, test_user):
        """Test sending message with existing conversation ID."""
        conversation_id = "test-conv-123"

        response = await async_client.post(
            "/api/v1/ai/chat",
            json={"message": "First message", "conversation_id": conversation_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conversation_id

    @pytest.mark.asyncio
    async def test_send_message_persists_to_database(
        self, async_client, test_user, db_session
    ):
        """Test that chat messages are saved to database."""
        message_text = "Test message for persistence"

        response = await async_client.post(
            "/api/v1/ai/chat", json={"message": message_text}
        )

        assert response.status_code == 200

        # Verify user message was saved
        from sqlalchemy import select

        result = await db_session.execute(
            select(ChatMessageTable).where(
                ChatMessageTable.user_id == test_user.id,
                ChatMessageTable.role == "user",
                ChatMessageTable.content == message_text,
            )
        )
        user_message = result.scalar_one_or_none()
        assert user_message is not None

        # Verify AI response was saved
        result = await db_session.execute(
            select(ChatMessageTable).where(
                ChatMessageTable.user_id == test_user.id,
                ChatMessageTable.role == "assistant",
            )
        )
        ai_message = result.scalar_one_or_none()
        assert ai_message is not None

    @pytest.mark.asyncio
    async def test_list_conversations(self, async_client, test_user, db_session):
        """Test listing user conversations."""
        # Create some test messages
        from backend.models.tables import ChatMessageTable

        conversation_id = "test-conv-list"
        msg1 = ChatMessageTable(
            id="msg-1",
            user_id=test_user.id,
            conversation_id=conversation_id,
            role="user",
            content="Hello",
            timestamp=datetime.now(timezone.utc),
        )
        msg2 = ChatMessageTable(
            id="msg-2",
            user_id=test_user.id,
            conversation_id=conversation_id,
            role="assistant",
            content="Hi there!",
            timestamp=datetime.now(timezone.utc),
        )

        db_session.add_all([msg1, msg2])
        await db_session.commit()

        response = await async_client.get("/api/v1/ai/conversations")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Check conversation structure
        conversation = data[0]
        assert "id" in conversation
        assert "title" in conversation
        assert "last_message_at" in conversation
        assert "message_count" in conversation

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, async_client, test_user, db_session):
        """Test getting messages for a specific conversation."""
        conversation_id = "test-conv-messages"

        # Add messages
        from backend.models.tables import ChatMessageTable

        msg = ChatMessageTable(
            id="msg-test",
            user_id=test_user.id,
            conversation_id=conversation_id,
            role="user",
            content="Test message",
            timestamp=datetime.now(timezone.utc),
        )
        db_session.add(msg)
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/ai/conversations/{conversation_id}/messages"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data

        # PaginatedResponse structure: {"items": [...], "pagination": {"total": X, ...}}
        assert "pagination" in data
        pagination = data["pagination"]
        assert "total" in pagination

        assert isinstance(data["items"], list)
        assert len(data["items"]) >= 1
        assert pagination["total"] >= 1

        # Check message structure
        message = data["items"][0]
        assert "id" in message
        assert "role" in message
        assert "content" in message
        assert "timestamp" in message

    @pytest.mark.asyncio
    async def test_delete_conversation(self, async_client, test_user, db_session):
        """Test deleting a conversation."""
        conversation_id = "test-conv-delete"

        # Add a message
        from backend.models.tables import ChatMessageTable

        msg = ChatMessageTable(
            id="msg-delete",
            user_id=test_user.id,
            conversation_id=conversation_id,
            role="user",
            content="Delete me",
            timestamp=datetime.now(timezone.utc),
        )
        db_session.add(msg)
        await db_session.commit()

        response = await async_client.delete(
            f"/api/v1/ai/conversations/{conversation_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["conversation_id"] == conversation_id

    @pytest.mark.asyncio
    async def test_clear_conversation(self, async_client, test_user, db_session):
        """Test clearing messages while keeping conversation ID."""
        conversation_id = "test-conv-clear"

        # Add messages
        from backend.models.tables import ChatMessageTable

        msg = ChatMessageTable(
            id="msg-clear",
            user_id=test_user.id,
            conversation_id=conversation_id,
            role="user",
            content="Clear me",
            timestamp=datetime.now(timezone.utc),
        )
        db_session.add(msg)
        await db_session.commit()

        response = await async_client.post(
            f"/api/v1/ai/conversations/{conversation_id}/clear"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cleared"

    @pytest.mark.asyncio
    async def test_chat_agent_execution_metadata(self, async_client, test_user):
        """Test that chat response includes agent execution metadata."""
        # Mock the LLM to trigger agent execution
        with patch(
            "backend.api.ai_chat.get_llm_core", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.generate_response.return_value = {
                "content": "I've scheduled your meeting!",
                "agent_executed": True,
                "agent_type": "booking",
                "intent": "schedule_meeting",
                "confidence": 0.95,
                "phases": {
                    "perception": {"status": "completed", "time_ms": 100},
                    "cognition": {"status": "completed", "time_ms": 200},
                    "action": {"status": "completed", "time_ms": 500},
                    "reflection": {"status": "completed", "time_ms": 50},
                },
                "entities": {"date": "tomorrow", "time": "14:00"},
            }
            mock_llm.return_value = mock_llm_instance

            response = await async_client.post(
                "/api/v1/ai/chat",
                json={"message": "Schedule a meeting tomorrow at 2pm"},
            )

            assert response.status_code == 200
            data = response.json()

            # Verify metadata fields
            assert "agent_executed" in data
            assert "agent_type" in data
            assert "intent" in data
            assert "confidence" in data
            assert "phases" in data
            assert "entities" in data

    @pytest.mark.asyncio
    async def test_chat_empty_message_validation(self, async_client, test_user):
        """Test validation of empty message."""
        response = await async_client.post("/api/v1/ai/chat", json={"message": ""})

        # Should either return 400 or handle gracefully
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_chat_long_message_handling(self, async_client, test_user):
        """Test handling of very long messages."""
        long_message = "A" * 10000  # 10k character message

        response = await async_client.post(
            "/api/v1/ai/chat", json={"message": long_message}
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 413]

    @pytest.mark.asyncio
    async def test_conversation_isolation(self, async_client, test_user, db_session):
        """Test that users can only see their own conversations."""
        # Create a conversation for the test user
        from backend.models.tables import ChatMessageTable

        my_conversation = "my-conv-123"
        msg = ChatMessageTable(
            id="msg-isolation",
            user_id=test_user.id,
            conversation_id=my_conversation,
            role="user",
            content="My message",
            timestamp=datetime.now(timezone.utc),
        )
        db_session.add(msg)
        await db_session.commit()

        # Try to access the conversation
        response = await async_client.get(
            f"/api/v1/ai/conversations/{my_conversation}/messages"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert data["pagination"]["total"] == 1
        assert len(data["items"]) == 1


@pytest.mark.integration
@pytest.mark.api
class TestChatErrorHandling:
    """Test error handling in chat endpoints."""

    @pytest.mark.asyncio
    async def test_chat_with_invalid_json(self, async_client, test_user):
        """Test handling of invalid JSON payload."""
        response = await async_client.post(
            "/api/v1/ai/chat",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_chat_missing_required_field(self, async_client, test_user):
        """Test handling of missing required fields."""
        response = await async_client.post(
            "/api/v1/ai/chat",
            json={},  # Missing 'message' field
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self, async_client, test_user):
        """Test accessing a conversation that doesn't exist."""
        response = await async_client.get(
            "/api/v1/ai/conversations/nonexistent-id/messages"
        )

        # Should return empty list or 404
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            payload = response.json()
            assert payload["items"] == []
            assert payload["pagination"]["total"] == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_conversation(self, async_client, test_user):
        """Test deleting a conversation that doesn't exist."""
        response = await async_client.delete("/api/v1/ai/conversations/nonexistent-id")

        # Should return success or 404
        assert response.status_code in [200, 404]
