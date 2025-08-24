import requests
from pathlib import Path
from twikit import Client
from .settings import settings

COOKIE_FILE = Path("cookies.json")
client = Client("de-DE")

async def ensure_login():
    # Versuche Cookies zu laden
    if COOKIE_FILE.exists():
        try:
            await client.load_cookies(str(COOKIE_FILE))
            # Test-Call (leichtgewichtig)
            await client.get_user_by_screen_name(settings.TWIKIT_USERNAME)
            return
        except Exception:
            pass  # Fallback: normal einloggen

    await client.login(
        auth_info_1=settings.TWIKIT_USERNAME,
        auth_info_2=settings.TWIKIT_EMAIL,
        password=settings.TWIKIT_PASSWORD,
    )
    client.save_cookies(str(COOKIE_FILE))

async def async_post_twikit(text: str):
    await ensure_login()
    await client.create_tweet(text)
    client.save_cookies(str(COOKIE_FILE))
    print("✅ Tweet via Twikit gesendet.")

def is_service_healthy() -> bool:
    url = settings.TWEET_SERVICE_URL.rstrip("/")
    if not url:
        return False
    try:
        r = requests.get(f"{url}/health", timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f"⚠️ Healthcheck fehlgeschlagen: {e}")
        return False

def post_via_service(text: str):
    url = settings.TWEET_SERVICE_URL.rstrip("/")
    headers = {"Authorization": f"Bearer {settings.TWEET_API_KEY}"} if settings.TWEET_API_KEY else {}
    r = requests.post(f"{url}", json={"text": text}, headers=headers, timeout=10)
    r.raise_for_status()
    print("✅ Tweet via Service gesendet.")

async def post_to_x(text: str, use_service: bool = True):
    if use_service and is_service_healthy():
        try:
            post_via_service(text)
            return
        except Exception as e:
            print(f"↪️ Fallback auf Twikit (Service-Fehler: {e})")

    await async_post_twikit(text)

