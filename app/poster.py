import asyncio
import requests
from pathlib import Path
from twikit import Client
from .settings import settings

COOKIE_FILE = Path("cookies.json")
client = Client("de-DE")

async def ensure_login():
    print("🔐 Login wird geprüft...")
    try:
        if COOKIE_FILE.exists():
            print("📁 Cookies gefunden, lade...")
            await client.load_cookies(str(COOKIE_FILE))
            print("✅ Cookies geladen")
            return

        print("🔑 Kein Cookie vorhanden – führe Login durch...")
        await client.login(
            auth_info_1=settings.TWIKIT_USERNAME,
            auth_info_2=settings.TWIKIT_EMAIL,
            password=settings.TWIKIT_PASSWORD,
        )
        client.save_cookies(str(COOKIE_FILE))
        print("✅ Login erfolgreich und Cookies gespeichert")

    except Exception as e:
        print("❌ Fehler beim Login:", e)

async def async_post_twikit(text: str):
    print("📝 Tweet wird direkt über Twikit gesendet:", text)
    try:
        await ensure_login()
        await client.create_tweet(text)
        client.save_cookies(str(COOKIE_FILE))
        print("✅ Tweet erfolgreich gesendet via Twikit")
    except Exception as e:
        print("❌ Fehler beim Twikit-Tweet:", e)

def post_via_service(text: str):
    print("🌐 Sende Tweet an Tweet-Service:", text)
    try:
        url = settings.TWEET_SERVICE_URL
        headers = {"Authorization": f"Bearer {settings.TWEET_API_KEY}"}
        data = {"text": text}
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        print("✅ Tweet-Service hat geantwortet:", response.json())
    except Exception as e:
        print("❌ Fehler beim Senden an Tweet-Service:", e)

async def post_to_x(text: str, use_service: bool = False):
    print("🚀 Starte Tweet-Vorgang...")
    if use_service:
        post_via_service(text)
    else:
        await async_post_twikit(text)

