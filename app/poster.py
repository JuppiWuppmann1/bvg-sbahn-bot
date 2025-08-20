import asyncio
from pathlib import Path
from twikit import Client
from .settings import settings

COOKIE_FILE = Path("cookies.json")

client = Client("de-DE")

async def ensure_login():
    if COOKIE_FILE.exists():
        await client.load_cookies(str(COOKIE_FILE))
        return
    # Erstes Login
    await client.login(
        auth_info_1=settings.X_USERNAME,
        auth_info_2=settings.X_EMAIL,
        password=settings.X_PASSWORD,
    )
    client.save_cookies(str(COOKIE_FILE))

async def async_post(text: str):
    await ensure_login()
    await client.create_tweet(text)
    client.save_cookies(str(COOKIE_FILE))

def post_to_x(text: str):
    asyncio.run(async_post(text))
