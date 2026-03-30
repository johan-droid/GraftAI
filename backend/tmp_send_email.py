import asyncio
import sys
from pathlib import Path

# Ensure package path is resolvable in raw script execution.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# If running from backend/ directory, package root is backend (contains backend/ package). 
# We also support running from repo root by adding parent path.
PARENT_ROOT = PROJECT_ROOT.parent
if str(PARENT_ROOT) not in sys.path:
    sys.path.insert(0, str(PARENT_ROOT))

from backend.services.email import send_email

async def test_send():
    try:
        await send_email(
            to_email='receiver@example.com',
            subject='GraftAI Test Email',
            html_body='<h1>GraftAI SMTP Test</h1><p>If you see this, email send works.</p>',
            text_body='GraftAI SMTP Test - if you see this, email send works.'
        )
        print('SEND_OK')
    except Exception as e:
        print('SEND_FAILED', e)

if __name__ == '__main__':
    asyncio.run(test_send())
