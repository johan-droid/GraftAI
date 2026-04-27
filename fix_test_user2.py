import re
import uuid

with open('backend/tests/conftest.py', 'r') as f:
    content = f.read()

# make sure we return unique username
content = content.replace(
    'f"testuser_{uuid.uuid4().hex[:8]}"',
    'f"testuser_{str(uuid.uuid4())[:8]}"'
)

content = content.replace(
    'f"test_{uuid.uuid4().hex[:8]}@example.com"',
    'f"test_{str(uuid.uuid4())[:8]}@example.com"'
)

with open('backend/tests/conftest.py', 'w') as f:
    f.write(content)
