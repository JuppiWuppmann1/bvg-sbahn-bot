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
    await ensure_login()
    await client.create_tweet(text)
    client.save_cookies(str(COOKIE_FILE))

def post_via_service(text: str):
    url = settings.TWEET_SERVICE_URL
    headers = {"Authorization": f"Bearer {settings.TWEET_API_KEY}"}
    data = {"text": text}
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()

async def post_to_x(text: str, use_service: bool = True):
    if use_service:
        post_via_service(text)
    else:
        await async_post_twikit(text)

