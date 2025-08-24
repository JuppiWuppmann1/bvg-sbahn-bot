import asyncio
import requests
from pathlib import Path
from twikit import Client
from .settings import settings

COOKIE_FILE = Path("cookies.json")
client = Client("de-DE")

async def ensure_login():
    if COOKIE_FILE.exists():
        await client.load_cookies(str(COOKIE_FILE))
        return
    await client.login(
        auth_info_1=settings.TWIKIT_USERNAME,
        auth_info_2=settings.TWIKIT_EMAIL,
        password=settings.TWIKIT_PASSWORD,
    )
    client.save_cookies(str(COOKIE_FILE))

async def async_post_twikit(text: str):
    try:
        await ensure_login()
        await client.create_tweet(text)
        client.save_cookies(str(COOKIE_FILE))
        print("✅ Tweet erfolgreich via Twikit gesendet.")
    except Exception as e:
        print(f"❌ Fehler beim Twikit-Tweet: {e}")

def is_service_healthy() -> bool:
    try:
        health_url = f"{settings.TWEET_SERVICE_URL.rstrip('/')}/health"
        response = requests.get(health_url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ Healthcheck fehlgeschlagen: {e}")
        return False

def post_via_service(text: str):
    try:
        url = settings.TWEET_SERVICE_URL
        headers = {"Authorization": f"Bearer {settings.TWEET_API_KEY}"}
        data = {"text": text}
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        print("✅ Tweet erfolgreich via Service gesendet.")
    except Exception as e:
        print(f"❌ Fehler beim Tweet-Service: {e}")
        raise

async def post_to_x(text: str, use_service: bool = True):
    if use_service and is_service_healthy():
        try:
            post_via_service(text)
        except Exception:
            print("↪️ Fallback auf Twikit...")
            await async_post_twikit(text)
    else:
        print("⚠️ Tweet-Service nicht verfügbar – nutze Twikit direkt.")
        await async_post_twikit(text)

