
# AI/LLM Orchestration Service
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import hashlib
from .langchain_client import llm, vector_store, OPENAI_MODEL
from .cache import get_cache, set_cache
import logging

# Initialize logger
logger = logging.getLogger(__name__)

try:
    from groq import Groq
except ImportError:
    Groq = None

router = APIRouter(prefix="/ai", tags=["ai"])

class AIRequest(BaseModel):
    prompt: str
    context: Optional[List[str]] = None
    user_id: Optional[int] = None

class AIResponse(BaseModel):
    result: str
    model_used: Optional[str] = None

def _generate_with_groq(prompt: str, model_name: str = "llama-3.3-70b-versatile") -> str:
    if Groq is None:
        raise RuntimeError("Groq SDK not installed. Please pip install groq")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable not set")

    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.2,
    )

    if hasattr(resp, "choices") and resp.choices:
        first = resp.choices[0]
        if hasattr(first, "message") and hasattr(first.message, "content"):
            return first.message.content
        if isinstance(first, dict) and "message" in first and "content" in first["message"]:
            return first["message"]["content"]

    if isinstance(resp, dict) and "choices" in resp and len(resp["choices"]) > 0:
        c = resp["choices"][0]
        if isinstance(c, dict) and "message" in c and "content" in c["message"]:
            return c["message"]["content"]

    return ""


@router.post("/chat", response_model=AIResponse)
async def ai_chat(request: AIRequest):
    # Retrieve relevant context from vector DB (if populated)
    try:
        docs = vector_store.similarity_search(request.prompt, k=3)
        context_text = "\n".join([doc.page_content for doc in docs]) if docs else ""
    except Exception as e:
        logger.warning(f"Vector store similarity search failed: {type(e).__name__}")
        context_text = ""

    # Compose prompt with context
    full_prompt = f"Context:\n{context_text}\n\nUser: {request.prompt}\nAI:"

    # Cache key deterministically derived from prompt and context
    cache_key = "ai_cache:" + hashlib.sha256(full_prompt.encode("utf-8")).hexdigest()
    cached_value = get_cache(cache_key)
    if cached_value:
        return AIResponse(result=cached_value, model_used="cache-hit")
    result_text = ""
    model_used = None

    # Prefer Groq if configured
    if os.getenv("GROQ_API_KEY") and Groq is not None:
        try:
            result_text = _generate_with_groq(full_prompt)
            model_used = "llama-3.3-70b-versatile"
        except Exception as e:
            # fallback to langchain/OpenAI-style LLM
            logger.warning(f"Groq call failed, falling back to existing LLM: {type(e).__name__}")
            result_text = ""

    if not result_text:
        try:
            response = llm(full_prompt)
        except TypeError:
            response = llm([{"role": "user", "content": full_prompt}])

        if isinstance(response, dict) and "content" in response:
            result_text = response["content"]
        elif hasattr(response, "generations"):
            gens = response.generations
            if gens and len(gens) > 0 and len(gens[0]) > 0:
                result_text = getattr(gens[0][0], "text", "")
        elif isinstance(response, list) and len(response) > 0:
            first = response[0]
            if hasattr(first, "message") and hasattr(first.message, "content"):
                result_text = first.message.content
            elif isinstance(first, dict) and "content" in first:
                result_text = first["content"]

        if not model_used:
            model_used = OPENAI_MODEL if os.getenv("OPENAI_API_KEY") else "fallback-dummy"

    if result_text:
        set_cache(cache_key, result_text, expire_seconds=300)

    return AIResponse(result=result_text or "No response.", model_used=model_used)
