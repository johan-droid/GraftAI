import os
import sys

# Add the backend package root to PYTHONPATH so tests can import with 'import backend.*'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Ensure deterministic behavior for AI service unit tests using stubbed LLM path
os.environ.setdefault('FORCE_GROQ', '1')
