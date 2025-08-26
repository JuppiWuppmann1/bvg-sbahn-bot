import os
import asyncio
from playwright.async_api import async_playwright

USERNAME = os.getenv("TWITTER_USERNAME")
PASSWORD = os.getenv("TWITTER_PASSWORD")

async def twitter_login_and_tweet(thread: list[str]):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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

            # Ersten Tweet posten
            await page.fill('div[aria-label="Tweet text"]', thread[0][:280])
            await page.click('div[data-testid="tweetButtonInline"]')
            print(f"✅ Tweet gesendet: {thread[0][:50]}...")

            # Folge-Tweets als Thread posten
            for reply in thread[1:]:
                await page.wait_for_timeout(3000)
                await page.goto("https://twitter.com/compose/tweet", timeout=20000)
                await page.fill('div[aria-label="Tweet text"]', reply[:280])
                await page.click('div[data-testid="tweetButtonInline"]')
                print(f"🔁 Antwort gesendet: {reply[:50]}...")

        except TimeoutError:
            print("❌ Timeout beim Tweet-Versand.")
            await page.screenshot(path="tweet_error.png")
        except Exception as e:
            print(f"❌ Fehler beim Tweeten: {e}")
            await page.screenshot(path="tweet_exception.png")

        await browser.close()
