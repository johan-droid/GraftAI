import os
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ── Dummy stubs — used when real services are not configured ──────────────────

class _DummyVectorStore:
    """Absorbs all vector-store calls without error."""

    def similarity_search(self, query: str, k: int = 3) -> list:
        return []

    def add_documents(self, docs: list, **kwargs: Any) -> list:
        logger.debug("VectorStore not configured — skipping add_documents")
        return []

    def delete(self, ids: list | None = None, **kwargs: Any) -> None:
        logger.debug("VectorStore not configured — skipping delete")


class _DummyLLM:
    """Returns a safe fallback when no LLM is configured."""

    def invoke(self, messages: Any, **kwargs: Any) -> Any:
        from types import SimpleNamespace
        return SimpleNamespace(content="AI service is not configured.")

    def __call__(self, messages: Any, **kwargs: Any) -> Any:
        return self.invoke(messages, **kwargs)


# ── Lazy real initialisation ──────────────────────────────────────────────────

vector_store: Any = _DummyVectorStore()
llm: Any = _DummyLLM()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "scheduler-context")


def _try_init() -> None:
    """Called once at startup. Failures are logged and silently ignored."""
    global llm, vector_store

    if not OPENAI_API_KEY:
        logger.info("OPENAI_API_KEY not set — using dummy LLM")
        return

    try:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # type: ignore
        llm = ChatOpenAI(model=OPENAI_MODEL, openai_api_key=OPENAI_API_KEY)
        logger.info(f"LLM initialised: {OPENAI_MODEL}")
    except Exception as exc:
        logger.warning(f"LLM init failed ({type(exc).__name__}) — using dummy")
        return

    if not PINECONE_API_KEY:
        logger.info("PINECONE_API_KEY not set — vector store disabled")
        return

    try:
        from langchain_openai import OpenAIEmbeddings  # type: ignore
        from langchain_pinecone import PineconeVectorStore  # type: ignore

        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vector_store = PineconeVectorStore(
            index_name=PINECONE_INDEX,
            embedding=embeddings,
            pinecone_api_key=PINECONE_API_KEY,
        )
        logger.info(f"Pinecone vector store initialised: {PINECONE_INDEX}")
    except Exception as exc:
        logger.warning(f"Pinecone init failed ({type(exc).__name__}) — using dummy vector store")


# Run at import time — non-fatal
try:
    _try_init()
except Exception:
    pass
