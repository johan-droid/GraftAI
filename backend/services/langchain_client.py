# LangChain and Vector DB Client Setup
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-west1-gcp")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

vector_store = None
llm = None

try:
    # Modern LangChain imports (v0.2+)
    try:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    except ImportError:
        ChatOpenAI = None
        OpenAIEmbeddings = None

    # Pinecone vector store
    try:
        from langchain_community.vectorstores import Pinecone as PineconeLangChain
    except ImportError:
        try:
            from langchain.vectorstores import Pinecone as PineconeLangChain
        except ImportError:
            PineconeLangChain = None

    # Initialize Pinecone
    if PINECONE_API_KEY:
        try:
            import pinecone
            if hasattr(pinecone, "init"):
                pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
            else:
                from pinecone import Pinecone as PineconeClient
                _pc = PineconeClient(api_key=PINECONE_API_KEY)
        except Exception as pe:
            print(f"[!] Pinecone init skipped: {pe}")

    # Initialize LLM and embeddings
    if OPENAI_API_KEY and ChatOpenAI is not None:
        try:
            llm = ChatOpenAI(model=OPENAI_MODEL, openai_api_key=OPENAI_API_KEY)
            if OpenAIEmbeddings is not None and PineconeLangChain is not None:
                embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
                vector_store = PineconeLangChain(
                    index_name="scheduler-context", embedding=embeddings
                )
        except Exception as le:
            print(f"[!] LangChain LLM/embeddings init skipped: {le}")

except Exception as e:
    print(f"[!] LangChain/Pinecone initialization skipped: {e}")


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
