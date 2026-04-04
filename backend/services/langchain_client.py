# LangChain and Vector DB Client Setup
import os
import logging

# Initialize logger
logger = logging.getLogger(__name__)
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-west1-gcp")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "scheduler-context")

vector_store = None
llm = None

_has_openai = False
_has_pinecone_lc = False

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # type: ignore
    _has_openai = True
except ImportError as e:
    logger.error(f"langchain-openai not installed: {e}. AI features will be disabled.")
    ChatOpenAI = None
    OpenAIEmbeddings = None

try:
    from langchain_pinecone import PineconeVectorStore  # type: ignore
    _has_pinecone_lc = True
except ImportError as e:
    logger.error(f"langchain-pinecone not installed: {e}. Vector memory will be disabled.")
    PineconeVectorStore = None

if PINECONE_API_KEY:
    try:
        from pinecone import Pinecone as PineconeClient  # type: ignore
        _pc = PineconeClient(api_key=PINECONE_API_KEY)
        logger.info("✅ Pinecone client initialized")
    except ImportError as e:
        logger.error(f"pinecone SDK not installed: {e}. Vector memory disabled.")
        _pc = None
    except Exception as e:
        logger.error(f"Pinecone client init failed: {type(e).__name__}: {e}")
        _pc = None
else:
    logger.warning("PINECONE_API_KEY not set — vector memory disabled")

if OPENAI_API_KEY and _has_openai:
    try:
        llm = ChatOpenAI(model=OPENAI_MODEL, openai_api_key=OPENAI_API_KEY)
        logger.info(f"✅ OpenAI LLM initialized: {OPENAI_MODEL}")
    except Exception as e:
        logger.error(f"ChatOpenAI initialization failed: {type(e).__name__}: {e}")
        llm = None

    if _has_openai and _has_pinecone_lc and PINECONE_API_KEY:
        try:
            embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            vector_store = PineconeVectorStore(
                index_name=PINECONE_INDEX,
                embedding=embeddings,
                pinecone_api_key=PINECONE_API_KEY,
            )
            logger.info(f"✅ Pinecone VectorStore initialized: index={PINECONE_INDEX}")
        except Exception as e:
            logger.error(
                f"PineconeVectorStore initialization failed: {type(e).__name__}: {e}. "
                f"Check PINECONE_INDEX ('{PINECONE_INDEX}') exists and PINECONE_API_KEY is valid."
            )
            vector_store = None
else:
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set — LLM and embeddings disabled")
    elif not _has_openai:
        logger.warning("langchain-openai not available — LLM disabled")


# ── Robust Stubs ─────────────────────────────────────────────────────────────


class _DummyVectorStore:
    """
    FIX ISS-001: Full stub that mirrors the PineconeVectorStore interface so
    scheduler.py never raises AttributeError when Pinecone is unconfigured.
    All operations log a warning instead of silently succeeding or crashing.
    """

    def similarity_search(self, query: str, k: int = 3, **kwargs):
        logger.warning("VectorStore not configured — similarity_search returning empty")
        return []

    def add_documents(self, documents, namespace=None, ids=None, **kwargs):
        logger.warning(
            f"VectorStore not configured — add_documents skipped for {len(documents)} doc(s)"
        )
        return []

    def delete(self, ids=None, namespace=None, **kwargs):
        logger.warning(
            f"VectorStore not configured — delete skipped for ids={ids}"
        )
        return None


class _DummyLLM:
    """Returns a safe fallback response when no real LLM is configured."""

    def invoke(self, messages, **kwargs):
        from types import SimpleNamespace

        logger.warning("LLM not configured — returning fallback response")
        return SimpleNamespace(content="AI service is not configured. Please set OPENAI_API_KEY.")

    def __call__(self, messages, **kwargs):
        return self.invoke(messages, **kwargs)


if llm is None:
    llm = _DummyLLM()
    logger.warning("Using DummyLLM — set OPENAI_API_KEY and GROQ_API_KEY to enable AI")

if vector_store is None:
    vector_store = _DummyVectorStore()
    logger.warning("Using DummyVectorStore — set PINECONE_API_KEY and OPENAI_API_KEY to enable vector memory")
