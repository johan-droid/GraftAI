import sys
import os
from pathlib import Path

# Fix paths
backend_root = Path(__file__).resolve().parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from dotenv import load_dotenv
load_dotenv(backend_root / ".env", override=True)

try:
    from langchain_groq import ChatGroq
    from langchain_openai import ChatOpenAI
    print("Imports successful")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

groq_key = os.getenv("GROQ_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

print(f"GROQ_API_KEY sets: {bool(groq_key)}")
print(f"OPENAI_API_KEY sets: {bool(openai_key)}")

if groq_key:
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_key)
        resp = llm.invoke("Hello")
        print(f"Groq Test Success: {resp.content[:20]}...")
    except Exception as e:
        print(f"Groq Test Failed: {type(e).__name__}: {e}")

if openai_key and "placeholder" not in openai_key.lower():
    try:
        llm = ChatOpenAI(openai_api_key=openai_key)
        resp = llm.invoke("Hello")
        print(f"OpenAI Test Success: {resp.content[:20]}...")
    except Exception as e:
        print(f"OpenAI Test Failed: {type(e).__name__}: {e}")
