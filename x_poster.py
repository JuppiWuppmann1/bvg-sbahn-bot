import os
import logging
from playwright.async_api import async_playwright

async def post_threads(threads):
    user = os.getenv("TWITTER_USER")
    pw = os.getenv("TWITTER_PASS")

    if not user or not pw:
        logging.error("❌ Twitter-Credentials fehlen!")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            logging.info("🔐 Starte Login bei X...")
            await page.goto("https://twitter.com/login", timeout=60000)

            await page.fill('input[name="text"]', user)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', pw)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000)

            for thread in threads:
                first = True
                for tweet in thread:
                    await page.click('div[aria-label="Tweet text"]')
                    await page.keyboard.type(tweet)
                    if first:
                        await page.click('div[data-testid="tweetButtonInline"]')
                        first = False
                    else:
                        await page.click('div[data-testid="tweetButton"]')
                    await page.wait_for_timeout(3000)

            logging.info("✅ Alle Tweets gesendet!")
        except Exception as e:
            logging.error(f"❌ Fehler beim Tweeten: {e}")
        finally:
            await browser.close()
