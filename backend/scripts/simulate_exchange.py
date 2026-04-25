import httpx

url = "http://127.0.0.1:8000/api/v1/auth/social/exchange"
payload = {
    "provider": "google",
    "access_token": "fake-token-1234567890",
    "provider_account_id": "test-provider-id",
    "email": "test@example.com",
}

print('POST', url)
with httpx.Client() as client:
    r = client.post(url, json=payload, timeout=10.0)
    print('status:', r.status_code)
    try:
        print('body:', r.json())
    except Exception:
        print('body (text):', r.text)
