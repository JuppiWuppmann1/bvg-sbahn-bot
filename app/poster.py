import asyncio
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

async def async_post(text: str):
    print("📝 Tweet wird vorbereitet:", text)
    try:
        await ensure_login()
        await client.create_tweet(text)
        client.save_cookies(str(COOKIE_FILE))
        print("✅ Tweet erfolgreich gesendet")
    except Exception as e:
        print("❌ Fehler beim Senden des Tweets:", e)

async def post_to_x(text: str):
    print("🚀 Starte Tweet-Vorgang...")
    await async_post(text)
