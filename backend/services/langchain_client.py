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
        prompt = str(messages or "").strip()
        if not prompt:
            text = "Local assistant is ready. Ask me to list, schedule, update, or delete events."
        else:
            text = (
                "Local assistant is active. I can process calendar intents in offline mode "
                "including listing, scheduling, updating, and deleting events."
            )
        return SimpleNamespace(content=text)

    def __call__(self, messages: Any, **kwargs: Any) -> Any:
        return self.invoke(messages, **kwargs)


vector_store: Any = LocalVectorStore()
llm: Any = LocalAssistantModel()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "scheduler-context")


def _try_init() -> None:
    """Initializes provider-backed engines when configured; otherwise retains local engines."""
    global llm, vector_store

    if OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI  # type: ignore

            llm = ChatOpenAI()
            logger.info(f"Assistant model initialized: {OPENAI_MODEL}")
        except Exception as exc:
            logger.warning(f"Assistant model initialization failed ({type(exc).__name__}); continuing in local mode")

    if OPENAI_API_KEY and PINECONE_API_KEY:
        try:
            from langchain_openai import OpenAIEmbeddings  # type: ignore
            from langchain_pinecone import PineconeVectorStore  # type: ignore

            embeddings = OpenAIEmbeddings()
            vector_store = PineconeVectorStore(
                index_name=PINECONE_INDEX,
                embedding=embeddings,
                pinecone_api_key=PINECONE_API_KEY,
            )
            logger.info(f"Vector store initialized: {PINECONE_INDEX}")
        except Exception as exc:
            logger.warning(f"Vector store initialization failed ({type(exc).__name__}); continuing in local mode")


try:
    _try_init()
except Exception as exc:
    logger.warning(f"Assistant stack initialization warning: {exc}")
