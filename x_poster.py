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
        await page.set_viewport_size({"width": 1280, "height": 800})

        try:
            logging.info("🔐 Starte Login bei X...")
            await page.goto("https://twitter.com/login", timeout=60000)

            # Schritt 1: Benutzername
            await page.wait_for_selector('input[name="text"], input[name="username"]', timeout=20000)
            if await page.query_selector('input[name="text"]'):
                await page.fill('input[name="text"]', user)
            else:
                await page.fill('input[name="username"]', user)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)

            # Schritt 2: Passwort
            await page.wait_for_selector('input[name="password"]', timeout=20000)
            await page.fill('input[name="password"]', pw)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000)

            # Schritt 3: Navigiere zur Tweet-Seite
            await page.goto("https://twitter.com/compose/tweet", timeout=60000)
            await page.wait_for_selector('div[aria-label="Tweet text"]', timeout=20000)

            for thread in threads:
                first = True
                for tweet in thread:
                    tweet_box = await page.query_selector('div[aria-label="Tweet text"]')
                    if tweet_box:
                        await tweet_box.click()
                        await tweet_box.fill("")  # Leeren für Sicherheit
                        await tweet_box.type(tweet)
                        await page.wait_for_timeout(1000)

                        # Button-Logik
                        tweet_button = await page.query_selector('div[data-testid="tweetButtonInline"]') or await page.query_selector('div[data-testid="tweetButton"]')
                        if tweet_button:
                            await tweet_button.click()
                        else:
                            logging.warning("⚠️ Kein Tweet-Button gefunden.")
                        first = False

                        await page.wait_for_timeout(3000)
                    else:
                        logging.warning("⚠️ Tweet-Feld nicht gefunden.")

            logging.info("✅ Alle Tweets gesendet!")
        except Exception as e:
            html = await page.content()
            logging.error(f"❌ Fehler beim Tweeten: {e}\n🔍 HTML-Snapshot:\n{html[:1000]}")
        finally:
            await browser.close()
