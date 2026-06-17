import logging
import os
from types import SimpleNamespace
from typing import Any

logger = logging.getLogger(__name__)

class LocalVectorStore:
    """In-memory vector store interface used when external vector backends are unavailable."""

    def __init__(self) -> None:
        self._docs: list[Any] = []

    def similarity_search(self, query: str, k: int=3) -> list[Any]:
        if not self._docs:
            return []
        return self._docs[:k]

    def add_documents(self, docs: list[Any], **kwargs: Any) -> list[str]:
        self._docs.extend(docs)
        return kwargs.get("ids") or []

    def delete(self, ids: list[str] | None=None, **kwargs: Any) -> None:
        if ids is None:
            self._docs.clear()
            return
        return

class LocalAssistantModel:
    """Deterministic local assistant for offline operation."""

    def invoke(self, messages: Any, **kwargs: Any) -> Any:
        msg_str = str(messages).lower()
        if "implementation context" in msg_str or "authoritative context" in msg_str:
            text = "I'm currently in High-Stability mode. I have access to your calendar data and the implementation context needed to keep scheduling behavior aligned. I can perform specific actions (list, schedule, update, delete). How would you like to proceed with your schedule?"
        else:
            text = "Local offline engine active. No cloud connection required for basic scheduling."
        return SimpleNamespace(content=text)

    async def ainvoke(self, messages: Any, **kwargs: Any) -> Any:
        """Async wrapper for the local deterministic engine."""
        return self.invoke(messages, **kwargs)

    def __call__(self, messages: Any, **kwargs: Any) -> Any:
        return self.invoke(messages, **kwargs)
vector_store: Any = LocalVectorStore()
llm: Any = LocalAssistantModel()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "scheduler-context")

def _safe_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)).strip())
    except Exception:
        return default

def _safe_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except Exception:
        return default

def _try_init() -> None:
    """Initializes provider-backed engines when configured; otherwise retains local engines."""
    global llm, vector_store
    if OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model=OPENAI_MODEL, temperature=_safe_float("OPENAI_TEMPERATURE", 0.2), max_retries=max(1, _safe_int("OPENAI_MAX_RETRIES", 2)))
            logger.info("Assistant model initialized: %s", OPENAI_MODEL)
        except Exception as exc:
            logger.warning("Assistant model initialization failed (%s); continuing in local mode", type(exc).__name__)
    if OPENAI_API_KEY and PINECONE_API_KEY:
        try:
            if len(OPENAI_API_KEY.strip()) > 0 and len(PINECONE_API_KEY.strip()) > 0:
                from langchain_openai import OpenAIEmbeddings
                from langchain_pinecone import PineconeVectorStore
                embeddings = OpenAIEmbeddings()
                vector_store = PineconeVectorStore(index_name=PINECONE_INDEX, embedding=embeddings, pinecone_api_key=PINECONE_API_KEY)
                logger.info(" Vector store initialized: %s", PINECONE_INDEX)
        except ImportError as e:
            logger.warning(" Vector store dependencies missing or broken: %s. Falling back to local mode.", e)
        except Exception as exc:
            logger.warning(" Vector store initialization failed (%s): %s. Falling back to local mode.", type(exc).__name__, exc)
try:
    _try_init()
except Exception as exc:
    logger.warning("Assistant stack initialization warning: %s", exc)
