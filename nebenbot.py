import os
import asyncio
from playwright.async_api import async_playwright

USERNAME = os.getenv("TWITTER_USERNAME")
PASSWORD = os.getenv("TWITTER_PASSWORD")

async def twitter_login_and_tweet(text: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Debug-Modus bei Fehlern
        page = await browser.new_page()

        try:
            await page.goto("https://twitter.com/login", timeout=20000)
            await page.fill('input[name="text"]', USERNAME)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)

            await page.fill('input[name="password"]', PASSWORD)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000)

            await page.wait_for_selector('div[aria-label="Tweet text"]', timeout=30000)
            await page.fill('div[aria-label="Tweet text"]', text[:280])
            await page.click('div[data-testid="tweetButtonInline"]')

            print(f"✅ Tweet gesendet: {text[:50]}...")

        except PlaywrightTimeoutError:
            print("❌ Timeout beim Tweet-Versand. Möglicherweise DOM geändert oder Login fehlgeschlagen.")
            await page.screenshot(path="tweet_error.png")
        except Exception as e:
            print(f"❌ Fehler beim Tweeten: {e}")
            await page.screenshot(path="tweet_exception.png")

        await browser.close()
