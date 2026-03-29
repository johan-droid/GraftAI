from datetime import datetime, timedelta, timezone
import os
import json
import logging
import hashlib
import re
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.db import get_db
from backend.auth.schemes import get_current_user_id
from backend.services import scheduler
from backend.services.cache import get_cache, set_cache
from backend.services.langchain_client import get_llm, get_vector_store
from backend.services.ai_tools import ScheduleEvent, UpdateMeeting, DeleteMeeting, SearchSchedule, GetTimeAnalytics, FetchProjectNotes
from backend.services.ai_memory import get_session_history
from fastapi.responses import StreamingResponse
from backend.auth.routes import get_rate_limiter
import asyncio
from backend.services.prefetcher import prefetcher
from backend.utils.tenant import get_current_org_id, get_current_workspace_id

# Conditional imports for optional dependencies
try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

try:
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    SystemMessage = None
    HumanMessage = None

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

class AIRequest(BaseModel):
    prompt: str
    timezone: str = "UTC"

class AIResponse(BaseModel):
    result: str
    model_used: Optional[str] = None

async def _generate_with_groq(system_prompt: str, user_input: str) -> str:
    """Helper for direct Groq API access if configured."""
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    chat_completion = await client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def _get_schedule_context(events):
    header = "Your Real-Time Schedule (GROUND TRUTH):\n"
    if not events:
        return header + "Currently empty."
    context = header
    for event in events:
        context += f"- {event.title} at {event.start_time.strftime('%H:%M')} (ID: {event.id})\n"
    return context

@router.post("/chat")
async def ai_chat(
    request: AIRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    workspace_id: Optional[int] = Depends(get_current_workspace_id),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=20, window_seconds=60)),
):
    """
    Sovereign AI Copilot with RAG, Chain-of-Thought Reasoning, and Proactive Tooling.
    """
    current_time = datetime.now(timezone.utc)
    user_name = "User"
    user_email = ""
    
    try:
        from backend.models.tables import UserTable
        user = await db.get(UserTable, user_id)
        if user:
            user_name = user.full_name or "User"
            user_email = user.email

        # 1. RETRIEVAL (RAG): Fetch related context from Vector Store (Isolated by Org)
        vector_store = get_vector_store()
        # Namespace transition: from user_{user_id} to org_{org_id}
        namespace = f"org_{org_id}"
        related_docs = vector_store.similarity_search(request.prompt, k=3, namespace=namespace)
        rag_context = "\n".join([f"[Memory]: {d.page_content}" for d in related_docs])

        # 2. SHORT-TERM CONTEXT: Today's schedule (LIGHTNING FAST)
        # Scoped by Org and Workspace
        schedule_context = await prefetcher.get_cached_context(user_id) # Cache still user-based for speed
        if not schedule_context:
            schedule_context = await scheduler.get_optimized_context(db, user_id, current_time, org_id=org_id, workspace_id=workspace_id)
            
    except Exception as e:
        logger.warning(f"Context retrieval failed: {e}")
        rag_context = "[Notice]: Past memory currently unreachable."
        schedule_context = "[Notice]: Schedule currently unreachable."

    system_prompt = f"""
    IDENTITY: 
    You are GraftAI, the world's most advanced AI Scheduling & Productivity Orchestrator.
    
    REASONING FRAMEWORK (Sovereign Thinking):
    Before taking any action, you MUST perform a 'Cognitive Check':
    1. CONTEXT: Does the request conflict with existing meetings or focus blocks?
    2. PREFERENCE: Does this align with the user's priority (e.g., preference for morning meetings)?
    3. HYGIENE: Does the meeting need an agenda? Is there enough transition time (10m)?
    
    INTELLIGENT CATEGORIZATION:
    You must choose the correct 'category' for every entry:
    - 'meeting': Professional syncs, calls, or demos. (Usually requires a link).
    - 'task': To-dos, reminders, or low-density actions (e.g. "Buy milk").
    - 'birthday': Celebratory events and anniversaries.
    - 'deep_work': Protected time for focused coding, writing, or design.
    - 'personal': Lifestyle events, chores, or private time.
    - 'out_of_office': Vacations or unavailability markers.
    
    GUIDELINES:
    - Be proactive. If you see a conflict, offer an alternative immediately.
    - If a request is vague, search the schedule or project notes first.
    
    ENVIRONMENT:
    Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
    User: {user_name} ({user_email})
    Organization ID: {org_id}
    Workspace ID: {workspace_id or 'General'}
    Timezone: {request.timezone}
    
    {schedule_context}
    
    {rag_context}
    """

    # 1. Setup Tools
    tools = [ScheduleEvent, UpdateMeeting, DeleteMeeting, SearchSchedule, GetTimeAnalytics, FetchProjectNotes]
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    # 2. Setup Memory
    memory = get_session_history(user_id)
    chat_history = memory.messages

    # 3. Construct message list
    messages = [SystemMessage(content=system_prompt)] + chat_history + [HumanMessage(content=request.prompt)]

    async def generate_response():
        from backend.utils.db import AsyncSessionLocal
        # Use a fresh session for the generator to ensure it stays alive throughout the stream
        async with AsyncSessionLocal() as generator_db:
            full_response_text = ""
            aggregated_tool_calls = {}

            try:
                # ── Step 1: LLM Stream ──
                async for chunk in llm_with_tools.astream(messages):
                    # Process Content
                    if hasattr(chunk, 'content') and chunk.content:
                        full_response_text += chunk.content
                        yield f"data: {json.dumps({'text': chunk.content})}\n\n"
                    
                    # Aggregate Tool Calls
                    if hasattr(chunk, 'tool_call_chunks'):
                        for tc_chunk in chunk.tool_call_chunks:
                            idx = tc_chunk.get("index")
                            if idx not in aggregated_tool_calls:
                                aggregated_tool_calls[idx] = tc_chunk
                            else:
                                for k, v in tc_chunk.items():
                                    if k == "args" and v:
                                        aggregated_tool_calls[idx]["args"] += v
                                    elif k != "index" and v:
                                        aggregated_tool_calls[idx][k] = v

                # ── Step 2: Tool Execution ──
                for idx, tc in aggregated_tool_calls.items():
                    name = tc.get("name")
                    args_str = tc.get("args", "{}")
                    try:
                        args = json.loads(args_str)
                        yield f"data: {json.dumps({'status': f'Executing {name}...'})}\n\n"
                        
                        if name == "ScheduleEvent":
                            try:
                                start_str = args["start_time"].replace("Z", "+00:00")
                                start_dt = datetime.fromisoformat(start_str)
                                if start_dt.tzinfo is None: 
                                    start_dt = start_dt.replace(tzinfo=timezone.utc)
                                
                                duration = args.get("duration_minutes", 30)
                                category = args.get("category", "meeting")
                                is_meeting = args.get("is_meeting", True)
                                if category in ["birthday", "personal", "deep_work", "task"]:
                                    is_meeting = False
                                    
                                event_data = {
                                    "user_id": user_id, 
                                    "org_id": org_id,
                                    "workspace_id": workspace_id,
                                    "title": args.get("title", "GraftAI Event"),
                                    "category": category,
                                    "start_time": start_dt, 
                                    "end_time": start_dt + timedelta(minutes=duration),
                                    "status": "confirmed", 
                                    "is_meeting": is_meeting, 
                                    "meeting_platform": args.get("platform") if is_meeting else None,
                                    "agenda": args.get("agenda"), 
                                    "attendees": [{"email": e} for e in args.get("attendees", [])]
                                }
                                await scheduler.create_event(generator_db, event_data)
                                yield f"data: {json.dumps({'action_result': f'Successfully scheduled: {event_data['title']}', 'success': True})}\n\n"
                            except Exception as e:
                                logger.error(f"ScheduleEvent tool failed: {e}")
                                yield f"data: {json.dumps({'error': 'I tried to book that, but the calendar engine had a conflict. Can we try another time?'})}\n\n"

                        elif name == "GetTimeAnalytics":
                            try:
                                from backend.services.analytics import analytics_summary
                                days = args.get('days', 7)
                                res = await analytics_summary(
                                    range=f"{days}d", 
                                    user_id=user_id, 
                                    db=generator_db, 
                                    org_id=org_id, 
                                    workspace_id=workspace_id
                                )
                                summary_text = getattr(res, 'summary', 'No summary data available for this period.')
                                yield f"data: {json.dumps({'text': f'\n\n**Productivity Insight:** {summary_text}'})}\n\n"
                            except Exception as e:
                                logger.error(f"Analytics tool failed: {e}")
                                yield f"data: {json.dumps({'text': '\n\n**Note:** I couldn\'t fetch your full productivity analytics right now, but I can still see your upcoming meetings.'})}\n\n"

                        elif name == "FetchProjectNotes":
                            vector_store = get_vector_store()
                            notes = vector_store.similarity_search(args["project_keyword"], k=5, namespace=f"org_{org_id}")
                            formatted_notes = "\n".join([f"• {n.page_content}" for n in notes])
                            yield f"data: {json.dumps({'text': f'\n\n**Found Project Notes:**\n{formatted_notes}'})}\n\n"
                        
                        elif name == "SearchSchedule":
                            try:
                                days_ahead = args.get("days_ahead", 1)
                                start = datetime.now(timezone.utc)
                                end = start + timedelta(days=days_ahead)
                                
                                found_events = await scheduler.get_events_for_range(generator_db, user_id, start, end, org_id=org_id, workspace_id=workspace_id)
                                if not found_events:
                                    yield f"data: {json.dumps({'text': '\n\n**Search Result:** Your schedule is clear for this period.'})}\n\n"
                                else:
                                    results_text = "\n".join([f"• {e.title} ({e.start_time.strftime('%I:%M %p')})" for e in found_events])
                                    yield f"data: {json.dumps({'text': f'\n\n**Tomorrow\'s Agenda:**\n{results_text}'})}\n\n"
                            except Exception as e:
                                logger.error(f"SearchSchedule tool failed: {e}")
                                yield f"data: {json.dumps({'text': '\n\n**Note:** I had trouble searching your calendar, but I can try booking a new meeting for you.'})}\n\n"

                        elif name == "UpdateMeeting":
                            await scheduler.update_event(generator_db, args["event_id"], user_id, args, org_id=org_id, workspace_id=workspace_id)
                            yield f"data: {json.dumps({'action_result': 'Meeting updated successfully.', 'success': True})}\n\n"
                        elif name == "DeleteMeeting":
                            await scheduler.delete_event(generator_db, args["event_id"], user_id, org_id=org_id, workspace_id=workspace_id)
                            yield f"data: {json.dumps({'action_result': 'Meeting removed from calendar.', 'success': True})}\n\n"

                    except Exception as tool_err:
                        logger.error(f"Tool {name} failed: {tool_err}")
                        yield f"data: {json.dumps({'error': f'Failed to execute {name}: {str(tool_err)}'})}\n\n"

                # ── Step 3: Persistence ──
                if full_response_text:
                    memory.add_user_message(request.prompt)
                    memory.add_ai_message(full_response_text)

                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"AI Stream failed: {e}")
                yield f"data: {json.dumps({'error': 'The AI engine encountered a brief interruption. Please try again.'})}\n\n"
                yield "data: [DONE]\n\n"

    return StreamingResponse(generate_response(), media_type="text/event-stream")
