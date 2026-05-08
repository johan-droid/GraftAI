import re

with open('frontend/src/lib/api-client.ts', 'r') as f:
    content = f.read()

# Fix 1: preserve-caught-error
# Line 167 & 173
content = content.replace('throw new Error(\n              "Cannot connect to backend server. Please ensure:\\n" +\n              "1. Backend is running on http://localhost:8000\\n" +\n              "2. Check NEXT_PUBLIC_API_BASE_URL in .env.local"\n            );', 'throw new Error(\n              "Cannot connect to backend server. Please ensure:\\n" +\n              "1. Backend is running on http://localhost:8000\\n" +\n              "2. Check NEXT_PUBLIC_API_BASE_URL in .env.local",\n              { cause: error }\n            );')

content = content.replace('throw new Error(\n              "Cannot connect to backend server. The service may be temporarily unavailable."\n            );', 'throw new Error(\n              "Cannot connect to backend server. The service may be temporarily unavailable.",\n              { cause: error }\n            );')

with open('frontend/src/lib/api-client.ts', 'w') as f:
    f.write(content)

with open('frontend/src/lib/offlineQueue.ts', 'r') as f:
    content = f.read()

# Fix 2: no-useless-assignment
# Line 273 & 274
content = re.sub(r'let endpoint = \'\';\n\s*let method: \'POST\' \| \'PUT\' \| \'DELETE\' = \'POST\';', 'let endpoint: string;\n    let method: \'POST\' | \'PUT\' | \'DELETE\';', content)

with open('frontend/src/lib/offlineQueue.ts', 'w') as f:
    f.write(content)
