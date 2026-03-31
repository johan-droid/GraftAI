import sys
import os
from pathlib import Path

# Fix sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from backend.services.langchain_client import llm, vector_store

print(f"LLM instance: {type(llm).__name__}")
print(f"Vector Store instance: {type(vector_store).__name__}")

if llm is not None:
    print("✅ LLM proxy is working")
else:
    print("❌ LLM proxy is None")

if vector_store is not None:
    print("✅ Vector Store proxy is working")
else:
    print("❌ Vector Store proxy is None")
