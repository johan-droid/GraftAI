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

try:
    # Modern LangChain imports (v0.2+)
    try:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # type: ignore
    except (ImportError, ModuleNotFoundError):
        ChatOpenAI = None
        OpenAIEmbeddings = None

    # Pinecone vector store
    try:
        from langchain_pinecone import PineconeVectorStore  # type: ignore
    except (ImportError, ModuleNotFoundError):
        PineconeVectorStore = None

    # Initialize Pinecone Client (Modern SDK v3.0+)
    if PINECONE_API_KEY:
        try:
            from pinecone import Pinecone as PineconeClient  # type: ignore
        except (ImportError, ModuleNotFoundError):
            PineconeClient = None  # Set to None if import fails

        if PineconeClient:  # Only proceed if PineconeClient was successfully imported
            try:
                # No need for pinecone.init() in v3.0+
                _pc = PineconeClient(api_key=PINECONE_API_KEY)
            except Exception as pe:
                logger.error(f"[!] Pinecone client init skipped: {type(pe).__name__}")

    # Initialize LLM and embeddings
    if OPENAI_API_KEY and ChatOpenAI is not None:
        try:
            llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY)
            if OpenAIEmbeddings is not None and PineconeVectorStore is not None:
                embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
                # Using the modern PineconeVectorStore from langchain-pinecone
                vector_store = PineconeVectorStore(
                    index_name=PINECONE_INDEX,
                    embedding=embeddings,
                    pinecone_api_key=PINECONE_API_KEY,
                )
        except Exception as le:
            logger.error(
                f"[!] LangChain LLM/embeddings init skipped: {type(le).__name__}"
            )

except Exception as e:
    logger.error(f"[!] LangChain/Pinecone initialization skipped: {type(e).__name__}")


# ── Fallback stubs so the rest of the app never crashes ──


class _DummyVectorStore:
    def similarity_search(self, query, k=3):
        return []


class _DummyLLM:
    """Returns a safe fallback response when no real LLM is configured."""

    def invoke(self, messages, **kwargs):
        from types import SimpleNamespace

        return SimpleNamespace(content="AI service is not configured.")

    def __call__(self, messages, **kwargs):
        return self.invoke(messages, **kwargs)


if llm is None:
    llm = _DummyLLM()

if vector_store is None:
    vector_store = _DummyVectorStore()
