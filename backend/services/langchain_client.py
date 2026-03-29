# LangChain and Vector DB Client Setup
import os
import logging

# Initialize logger
logger = logging.getLogger(__name__)
from pathlib import Path
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)
except ImportError:
    pass

# ── Provider Imports (Isolated to prevent cascading failures) ──
# Environment is loaded globally in app.py/main.py
# Optimized: Imports moved inside factory functions to speed up dev-server reloads.

# Helper to check for placeholders
def is_placeholder(key: str) -> bool:
    return not key or "placeholder" in key.lower() or key.startswith("sk-place")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "scheduler-context")

_llm = None
_vector_store = None

def get_llm():
    """Lazy initialization of the LLM chain."""
    global _llm
    if _llm is not None:
        return _llm
        
    groq_llm = None
    openai_llm = None
    
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # GROQ Init
    if not is_placeholder(GROQ_API_KEY):
        try:
            from langchain_groq import ChatGroq
            model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            groq_llm = ChatGroq(
                model=model_name, 
                groq_api_key=GROQ_API_KEY,
                max_retries=2
            )
            logger.info(f"[*] Groq LLM initialized ({model_name})")
        except (ImportError, Exception) as ge:
            logger.error(f"[!] Groq initialization failed: {ge}")

    # OpenAI Init
    if not is_placeholder(OPENAI_API_KEY):
        try:
            from langchain_openai import ChatOpenAI
            openai_llm = ChatOpenAI(
                model=OPENAI_MODEL, 
                openai_api_key=OPENAI_API_KEY,
                max_retries=2
            )
            logger.info(f"[*] OpenAI LLM initialized ({OPENAI_MODEL})")
        except (ImportError, Exception) as oe:
            logger.error(f"[!] OpenAI initialization failed: {oe}")

    # Assign global llm
    if groq_llm and openai_llm:
        _llm = groq_llm.with_fallbacks([openai_llm])
        logger.info("[*] LLM Fallback Chain active: Groq -> OpenAI")
    else:
        _llm = groq_llm or openai_llm

    if _llm is None:
        logger.warning("[!] No LLM configured - using Dummy fallback")
        _llm = _DummyLLM()
        
    return _llm

def get_vector_store():
    """Lazy initialization of the Vector Store."""
    global _vector_store
    if _vector_store is not None:
        return _vector_store
        
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    if not is_placeholder(PINECONE_API_KEY):
        try:
            from langchain_pinecone import PineconeVectorStore
            embeddings = None
            # Priority 1: OpenAI Embeddings
            if not is_placeholder(OPENAI_API_KEY):
                try:
                    from langchain_openai import OpenAIEmbeddings
                    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
                    logger.info("[*] Using OpenAI Embeddings for Vector Store")
                except ImportError:
                    pass
            
            # Priority 2: Local Embeddings
            if embeddings is None:
                try:
                    from langchain_huggingface import HuggingFaceEmbeddings
                    model_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
                    embeddings = HuggingFaceEmbeddings(model_name=model_name)
                    logger.info(f"[*] Using Local Sovereign Embeddings ({model_name})")
                except ImportError:
                    pass
            
            if embeddings:
                _vector_store = PineconeVectorStore(
                    index_name=PINECONE_INDEX,
                    embedding=embeddings,
                    pinecone_api_key=PINECONE_API_KEY,
                )
                logger.info(f"[*] Pinecone Vector Store initialized: {PINECONE_INDEX}")
        except (ImportError, Exception) as ve:
            logger.error(f"[!] Vector store initialization failed: {ve}")

    if _vector_store is None:
        _vector_store = _DummyVectorStore()
        
    return _vector_store

# Legacy property access for backward compatibility (will trigger lazy init)
@property
def llm():
    return get_llm()

@property
def vector_store():
    return get_vector_store()

# Backwards compatible module-level references (proxied)
class _ProxyModule:
    def __init__(self):
        self._real_llm = None
        self._real_vs = None
    
    @property
    def llm(self):
        if self._real_llm is None:
            self._real_llm = get_llm()
        return self._real_llm
        
    @property
    def vector_store(self):
        if self._real_vs is None:
            self._real_vs = get_vector_store()
        return self._real_vs

# Exporting proxies for backward compatibility with other modules (ai.py, scheduler.py)
# Using module-level __getattr__ (Python 3.7+) ensures these are only initialized when accessed.
def __getattr__(name: str):
    if name == "llm":
        return get_llm()
    if name == "vector_store":
        return get_vector_store()
    raise AttributeError(f"module {__name__} has no attribute {name}")

# ── Fallback stubs so the rest of the app never crashes ──
class _DummyVectorStore:
    def similarity_search(self, query, k=3):
        return []

class _DummyLLM:
    """Returns a safe fallback response when no real LLM is configured."""
    def invoke(self, messages, **kwargs):
        from types import SimpleNamespace
        return SimpleNamespace(content="AI service is not configured. Please check your API keys.")
    async def ainvoke(self, messages, **kwargs):
        return self.invoke(messages, **kwargs)
    async def astream(self, messages, **kwargs):
        from types import SimpleNamespace
        yield SimpleNamespace(content="AI service is not configured.")
    def bind_tools(self, tools, **kwargs):
        return self
    def __call__(self, messages, **kwargs):
        return self.invoke(messages, **kwargs)
