"""
AI Copilot Chat API Routes
Handles AI chat conversations using the 4-phase Agent Loop architecture.
Agent = LLM + Memory + Tools + Loop
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.auth.dependencies import get_current_user
from backend.models.tables import UserTable, ChatMessageTable
from backend.ai.llm_core import get_llm_core
from backend.ai.orchestrator import get_agent_controller, AgentType, AgentRequest
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


class ChatMessageSchema(BaseModel):
    """Schema for a chat message."""
    id: Optional[str] = None
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Request schema for sending a message."""
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response schema for AI chat."""
    id: str
    role: str
    content: str
    timestamp: datetime
    conversation_id: str
    agent_executed: bool = False
    agent_type: Optional[str] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None
    phases: Optional[Dict[str, Any]] = None
    entities: Optional[Dict[str, Any]] = None


class ConversationListSchema(BaseModel):
    """Schema for listing conversations."""
    id: str
    title: str
    last_message_at: datetime
    message_count: int


async def analyze_intent(user_message: str) -> Dict[str, Any]:
    """
    Analyze user message to determine intent and required agent.
    
    Returns:
        Dict with intent, confidence, and suggested agent type
    """
    lower = user_message.lower()
    
    # Booking/Scheduling intents
    if any(word in lower for word in ["schedule", "book", "meeting", "appointment", "reserve"]):
        return {
            "intent": "schedule_meeting",
            "agent_type": AgentType.BOOKING,
            "confidence": 0.9,
            "extract_entities": ["date", "time", "attendees", "duration", "title"]
        }
    
    # Optimization intents
    if any(word in lower for word in ["optimize", "best time", "when should", "suggest", "recommend"]):
        return {
            "intent": "optimize_schedule",
            "agent_type": AgentType.OPTIMIZATION,
            "confidence": 0.85,
            "extract_entities": ["preferences", "constraints", "goals"]
        }
    
    # Execution intents
    if any(word in lower for word in ["send", "create", "update", "delete", "execute"]):
        return {
            "intent": "execute_action",
            "agent_type": AgentType.EXECUTION,
            "confidence": 0.8,
            "extract_entities": ["action", "target", "parameters"]
        }
    
    # Monitoring/Analytics intents
    if any(word in lower for word in ["analytics", "report", "how many", "stats", "summary"]):
        return {
            "intent": "get_analytics",
            "agent_type": AgentType.MONITORING,
            "confidence": 0.8,
            "extract_entities": ["metric", "timeframe"]
        }
    
    # General conversation (use LLM directly)
    return {
        "intent": "general_chat",
        "agent_type": None,
        "confidence": 0.7,
        "extract_entities": []
    }


async def extract_entities(user_message: str, intent: str) -> Dict[str, Any]:
    """
    Extract relevant entities from user message based on intent.
    """
    import re
    from datetime import datetime, timedelta
    
    entities = {}
    lower = user_message.lower()
    
    # Extract date
    date_patterns = [
        r'(today|tomorrow|next\s+\w+|this\s+\w+|\d{1,2}/\d{1,2}/\d{2,4})',
        r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, lower)
        if match:
            entities["date"] = match.group(1)
            break
    
    # Extract time
    time_pattern = r'(\d{1,2}):?(\d{2})?\s*(am|pm)?'
    match = re.search(time_pattern, lower)
    if match:
        entities["time"] = match.group(0)
    
    # Extract duration
    duration_pattern = r'(\d{1,3})\s*(minute|hour|min|hr)'
    match = re.search(duration_pattern, lower)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        if 'hour' in unit or 'hr' in unit:
            entities["duration"] = value * 60
        else:
            entities["duration"] = value
    
    # Extract attendees (email addresses or names)
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    emails = re.findall(email_pattern, user_message)
    if emails:
        entities["attendees"] = emails
    
    # Extract meeting title (text after "about", "for", "titled")
    title_patterns = [
        r'(?:about|for|titled|called)\s+["\']?([^"\']{3,50})["\']?',
        r'(?:schedule|book)\s+a\s+(\w+)\s+meeting',
    ]
    for pattern in title_patterns:
        match = re.search(pattern, lower)
        if match:
            entities["title"] = match.group(1).strip().title()
            break
    
    return entities


async def generate_ai_response(
    user_message: str, 
    user_id: str, 
    db: AsyncSession,
    conversation_history: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Generate AI response using the 4-phase agent loop architecture.
    
    Args:
        user_message: The user's input message
        user_id: Current user ID
        db: Database session
        conversation_history: Previous messages for context
        
    Returns:
        Dict containing response text and optional agent execution results
    """
    try:
        # Step 1: Analyze intent (Perception phase entry point)
        intent_analysis = await analyze_intent(user_message)
        intent = intent_analysis["intent"]
        agent_type = intent_analysis["agent_type"]
        
        logger.info(f"Intent detected: {intent} (confidence: {intent_analysis['confidence']})")
        
        # Step 2: Extract entities
        entities = await extract_entities(user_message, intent)
        
        # Step 3: Route to appropriate handler
        if agent_type:
            # Use the 4-phase agent loop
            controller = await get_agent_controller()
            
            # Create agent request
            request = AgentRequest(
                id=f"chat_{datetime.utcnow().timestamp()}",
                type=agent_type,
                user_id=user_id,
                context={
                    "user_message": user_message,
                    "intent": intent,
                    "entities": entities,
                    "conversation_history": conversation_history or [],
                    "extracted_date": entities.get("date"),
                    "extracted_time": entities.get("time"),
                    "extracted_duration": entities.get("duration"),
                    "extracted_attendees": entities.get("attendees"),
                    "extracted_title": entities.get("title")
                },
                priority=5
            )
            
            # Execute the agent (runs all 4 phases)
            agent_result = await controller.dispatch(
                agent_type=agent_type,
                user_id=user_id,
                context=request.context
            )
            
            # Generate response based on agent result
            if agent_result.success:
                response_text = await _format_agent_response(agent_result, intent)
            else:
                response_text = await _format_agent_error(agent_result)
            
            return {
                "content": response_text,
                "agent_executed": True,
                "agent_type": agent_type.value,
                "intent": intent,
                "phases": agent_result.result.get("phases", {}) if hasattr(agent_result, 'result') else {},
                "entities": entities
            }
        
        else:
            # Use LLM directly for general conversation
            llm = await get_llm_core()
            
            # Build context from user data
            context = await _build_user_context(user_id, db)
            
            # Generate response
            response = await llm.generate_response(
                user_message=user_message,
                user_id=user_id,
                context=context
            )
            
            return {
                "content": response.content,
                "agent_executed": False,
                "intent": intent,
                "confidence": response.confidence,
                "entities": entities
            }
    
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return {
            "content": "I apologize, but I encountered an error processing your request. Could you please try again or rephrase your message?",
            "agent_executed": False,
            "intent": "error",
            "error": str(e)
        }


async def _format_agent_response(agent_result: Any, intent: str) -> str:
    """Format agent execution result into user-friendly response"""
    
    if intent == "schedule_meeting":
        result_data = agent_result.result.get("final_output", {}) if hasattr(agent_result, 'result') else {}
        booking_id = result_data.get("booking_id")
        metadata = result_data.get("metadata", {})
        
        title = metadata.get("title", "Meeting")
        date = metadata.get("start_time", "TBD")
        
        return f"✅ **Meeting Scheduled Successfully!**\n\n📅 **{title}**\n🕒 {date}\n\nI've scheduled your meeting and sent invitations. You can view it in your calendar. Is there anything else you'd like me to adjust?"
    
    elif intent == "optimize_schedule":
        return "📊 I've analyzed your schedule and found some optimization opportunities. Check the suggestions panel for personalized recommendations!"
    
    elif intent == "execute_action":
        return "✅ Action completed successfully!"
    
    elif intent == "get_analytics":
        return "📈 Here are your analytics! Check the reports section for detailed insights."
    
    return "I've processed your request. Is there anything else I can help you with?"


async def _format_agent_error(agent_result: Any) -> str:
    """Format agent error into user-friendly message"""
    error = agent_result.error if hasattr(agent_result, 'error') else "Unknown error"
    failed_phase = agent_result.result.get("failed_phase", "unknown") if hasattr(agent_result, 'result') else "unknown"
    
    # User-friendly error messages
    if "validation" in error.lower():
        return "⚠️ I couldn't complete that request because some information is missing. Could you please provide the meeting title, date, and time?"
    
    elif "availability" in error.lower():
        return "⚠️ That time slot isn't available. Would you like me to suggest alternative times?"
    
    elif "conflict" in error.lower():
        return "⚠️ There's a scheduling conflict with one of the attendees. Let me find a time that works for everyone."
    
    elif "timeout" in error.lower():
        return "⏱️ The request timed out. Please try again in a moment."
    
    else:
        return f"⚠️ I encountered an issue while processing your request. Error: {error}. Would you like to try again?"


async def _build_user_context(user_id: str, db: AsyncSession) -> Dict[str, Any]:
    """Build context about the user for the LLM"""
    context = {}
    
    try:
        # Get user data
        result = await db.execute(
            select(UserTable).where(UserTable.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            context["user_name"] = user.name
            context["user_email"] = user.email
            context["user_timezone"] = getattr(user, 'timezone', 'UTC')
        
        # Get recent meetings count
        from backend.models.tables import EventTable
        meetings_result = await db.execute(
            select(EventTable).where(
                and_(
                    EventTable.user_id == user_id,
                    EventTable.start_time >= datetime.utcnow()
                )
            ).limit(5)
        )
        upcoming_meetings = meetings_result.scalars().all()
        
        context["upcoming_meetings_count"] = len(upcoming_meetings)
        context["calendar_summary"] = f"{len(upcoming_meetings)} upcoming meetings"
        
        # Get user preferences (placeholder)
        context["user_preferences"] = {
            "preferred_meeting_duration": 30,
            "buffer_time": 15,
            "focus_time": "morning"
        }
    
    except Exception as e:
        logger.error(f"Error building user context: {e}")
    
    return context


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to the AI Copilot and get a response.
    Persists both user message and AI response to conversation history.
    """
    import uuid
    
    # Generate conversation ID if not provided
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # Create user message
    user_message = ChatMessageTable(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        conversation_id=conversation_id,
        role="user",
        content=request.message,
        timestamp=datetime.utcnow()
    )
    db.add(user_message)
    
    # Generate AI response (returns dict with content + metadata)
    ai_result = await generate_ai_response(
        request.message, 
        str(current_user.id), 
        db
    )
    
    # Extract content and metadata
    ai_content = ai_result.get("content", "I'm sorry, I couldn't process your request.")
    agent_executed = ai_result.get("agent_executed", False)
    agent_type = ai_result.get("agent_type")
    intent = ai_result.get("intent")
    confidence = ai_result.get("confidence")
    phases = ai_result.get("phases")
    entities = ai_result.get("entities")
    
    # Create AI response message (store just the text content)
    ai_message = ChatMessageTable(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        conversation_id=conversation_id,
        role="assistant",
        content=ai_content,
        timestamp=datetime.utcnow()
    )
    db.add(ai_message)
    
    await db.commit()
    
    return ChatResponse(
        id=ai_message.id,
        role="assistant",
        content=ai_content,
        timestamp=ai_message.timestamp,
        conversation_id=conversation_id,
        agent_executed=agent_executed,
        agent_type=agent_type,
        intent=intent,
        confidence=confidence,
        phases=phases,
        entities=entities
    )


@router.get("/conversations", response_model=List[ConversationListSchema])
async def list_conversations(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all chat conversations for the current user.
    """
    from sqlalchemy import func
    
    # Get all unique conversation IDs with their latest message
    stmt = select(
        ChatMessageTable.conversation_id,
        func.max(ChatMessageTable.timestamp).label("last_message_at"),
        func.count(ChatMessageTable.id).label("message_count")
    ).where(
        ChatMessageTable.user_id == current_user.id
    ).group_by(
        ChatMessageTable.conversation_id
    ).order_by(
        func.max(ChatMessageTable.timestamp).desc()
    )
    
    result = await db.execute(stmt)
    conversations = result.all()
    
    # Get first message of each conversation for title
    response = []
    for conv in conversations:
        # Get first user message for title
        title_stmt = select(ChatMessageTable).where(
            and_(
                ChatMessageTable.conversation_id == conv.conversation_id,
                ChatMessageTable.role == "user"
            )
        ).order_by(ChatMessageTable.timestamp.asc()).limit(1)
        
        first_msg = (await db.execute(title_stmt)).scalar_one_or_none()
        title = first_msg.content[:50] + "..." if first_msg and len(first_msg.content) > 50 else (first_msg.content if first_msg else "New Conversation")
        
        response.append(ConversationListSchema(
            id=conv.conversation_id,
            title=title,
            last_message_at=conv.last_message_at,
            message_count=conv.message_count
        ))
    
    return response


@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessageSchema])
async def get_conversation_messages(
    conversation_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all messages for a specific conversation.
    """
    stmt = select(ChatMessageTable).where(
        and_(
            ChatMessageTable.conversation_id == conversation_id,
            ChatMessageTable.user_id == current_user.id
        )
    ).order_by(ChatMessageTable.timestamp.asc())
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    return [
        ChatMessageSchema(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            timestamp=msg.timestamp
        ) for msg in messages
    ]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a conversation and all its messages.
    """
    # Delete all messages in the conversation
    stmt = ChatMessageTable.__table__.delete().where(
        and_(
            ChatMessageTable.conversation_id == conversation_id,
            ChatMessageTable.user_id == current_user.id
        )
    )
    
    await db.execute(stmt)
    await db.commit()
    
    return {"status": "deleted", "conversation_id": conversation_id}


@router.post("/conversations/{conversation_id}/clear")
async def clear_conversation(
    conversation_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clear all messages in a conversation but keep the conversation ID.
    """
    stmt = ChatMessageTable.__table__.delete().where(
        and_(
            ChatMessageTable.conversation_id == conversation_id,
            ChatMessageTable.user_id == current_user.id
        )
    )
    
    await db.execute(stmt)
    await db.commit()
    
    return {"status": "cleared", "conversation_id": conversation_id}
