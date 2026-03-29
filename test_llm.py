import sys
from pathlib import Path
import os

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the llm client
from backend.services.langchain_client import llm
from langchain_core.messages import HumanMessage

def test_llm():
    print(f"[*] Testing LLM initialization...")
    print(f"[*] LLM type: {type(llm)}")
    
    if hasattr(llm, "model_name"):
        print(f"[*] Model name: {llm.model_name}")
    
    try:
        print("[*] Sending test prompt to LLM...")
        # Check if the LLM is actually usable
        if hasattr(llm, "invoke"):
            response = llm.invoke([HumanMessage(content="Hello, please respond with 'OK' if you can hear me.")])
            print(f"[*] Success! LLM response: {response.content}")
        else:
            print("[!] LLM does not have an invoke method (DummyLLM?).")
    except Exception as e:
        print(f"[!] LLM test failed: {e}")

if __name__ == "__main__":
    test_llm()
