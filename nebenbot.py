import os
import asyncio
from playwright.async_api import async_playwright

USERNAME = os.getenv("TWITTER_USERNAME")
PASSWORD = os.getenv("TWITTER_PASSWORD")

async def twitter_login_and_tweet(text: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("https://twitter.com/login")
        await page.fill('input[name="text"]', USERNAME)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(2000)

        await page.fill('input[name="password"]', PASSWORD)
        await page.keyboard.press("Enter")

        await page.wait_for_selector('div[aria-label="Tweet text"]', timeout=15000)
        await page.fill('div[aria-label="Tweet text"]', text[:280])  # Twitter max 280 Zeichen
        await page.click('div[data-testid="tweetButtonInline"]')

        print(f"✅ Tweet gesendet: {text[:50]}...")
        await browser.close()
