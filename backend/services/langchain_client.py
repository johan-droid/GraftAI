import logging
import os
from types import SimpleNamespace
from typing import Any

logger = logging.getLogger(__name__)


class LocalVectorStore:
    """In-memory vector store interface used when external vector backends are unavailable."""

    def __init__(self) -> None:
        self._docs: list[Any] = []

    def similarity_search(self, query: str, k: int = 3) -> list[Any]:
        if not self._docs:
            return []
        return self._docs[:k]

    def add_documents(self, docs: list[Any], **kwargs: Any) -> list[str]:
        self._docs.extend(docs)
        ids = kwargs.get("ids") or []
        return ids

    def delete(self, ids: list[str] | None = None, **kwargs: Any) -> None:
        if ids is None:
            self._docs.clear()
            return
        # Local store keeps no direct id index; this remains no-op safe for interface compatibility.
        return


class LocalAssistantModel:
    """Deterministic local assistant for offline operation."""

    def invoke(self, messages: Any, **kwargs: Any) -> Any:
        # Optimized for High-Stability fallback
        msg_str = str(messages).lower()
        if "authoritative context" in msg_str:
            text = (
                "I'm currently in High-Stability mode. I have access to your calendar data "
                "and can perform specific actions (list, add, update, delete). "
                "How would you like to proceed with your schedule?"
            )
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
            from langchain_openai import ChatOpenAI  # type: ignore

            llm = ChatOpenAI(
                model=OPENAI_MODEL,
                temperature=_safe_float("OPENAI_TEMPERATURE", 0.2),
                max_retries=max(1, _safe_int("OPENAI_MAX_RETRIES", 2)),
            )
            logger.info(f"Assistant model initialized: {OPENAI_MODEL}")
        except Exception as exc:
            logger.warning(f"Assistant model initialization failed ({type(exc).__name__}); continuing in local mode")

    if OPENAI_API_KEY and PINECONE_API_KEY:
        try:
            # Re-verifying key length to avoid importing when key is empty string ""
            if len(OPENAI_API_KEY.strip()) > 0 and len(PINECONE_API_KEY.strip()) > 0:
                from langchain_openai import OpenAIEmbeddings  # type: ignore
                from langchain_pinecone import PineconeVectorStore  # type: ignore

                embeddings = OpenAIEmbeddings()
                vector_store = PineconeVectorStore(
                    index_name=PINECONE_INDEX,
                    embedding=embeddings,
                    pinecone_api_key=PINECONE_API_KEY,
                )
                logger.info(f"✅ Vector store initialized: {PINECONE_INDEX}")
        except ImportError as e:
            logger.warning(f"⚠️ Vector store dependencies missing or broken: {e}. Falling back to local mode.")
        except Exception as exc:
            logger.warning(f"⚠️ Vector store initialization failed ({type(exc).__name__}): {exc}. Falling back to local mode.")


try:
    _try_init()
except Exception as exc:
    logger.warning(f"Assistant stack initialization warning: {exc}")
