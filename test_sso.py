import httpx
import asyncio
import urllib.parse

async def async_sso_probe():
    # Make a request to the backend with fake code and state
    state = "fake_state"
    code = "fake_code"
    
    url = f"http://127.0.0.1:8000/api/v1/auth/sso/callback?code={code}&state={state}&fetch=true"
    print(f"Fetching: {url}")
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            print("Status:", resp.status_code)
            print("Response:", resp.text)
    except Exception as e:
        print("Exception:", e)


if __name__ == "__main__":
    asyncio.run(async_sso_probe())
