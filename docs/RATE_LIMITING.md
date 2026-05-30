Rate limiting: tiered API key handling and tests
===============================================

Summary
-------
This project uses a Redis-backed RateLimiter (`backend/utils/rate_limiter.py`) that supports per-endpoint limits, multiple strategies, and tiered limits for API keys and users.

Key features
- Cached mapping of API-key prefixes to stored key hashes and user `tier` to speed verification at runtime.
- Full verification of an incoming `X-API-Key` by computing `sha256(api_key)` and comparing to stored `api_keys.key_hash`.
- Startup population of the in-memory prefix index to reduce DB queries in production.

Running tests
-------------
Install project dependencies (use a venv):

Windows PowerShell example:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
pip install pytest pytest-asyncio
python -m pytest -q
```

Focused tests (rate limiter only):
```powershell
python -m pytest backend/tests/unit/test_rate_limiter.py -q
```

Notes
-----
- The DB schema contains `api_keys.key_prefix` and `api_keys.key_hash` (SHA256 hex). The runtime resolves the prefix to one or more key hashes and compares the hash of the presented key before assigning the associated `tier`.
- If you want me to change the hashing algorithm or to use a different verification method (e.g., HMAC or Argon2), tell me where keys are created so I can mirror that algorithm.

Pluggable hash function & periodic refresh
-----------------------------------------
- The runtime uses a pluggable hash function `RateLimiter.api_key_hash_func` (default is `sha256(api_key).hexdigest()`). To switch algorithms, set `rate_limiter.api_key_hash_func` at startup to a callable that accepts the raw API key and returns its stored representation.
- The prefix index is populated at startup and refreshed periodically. Configure the refresh interval via `API_KEY_PREFIX_REFRESH_SECONDS` (default 300s).
