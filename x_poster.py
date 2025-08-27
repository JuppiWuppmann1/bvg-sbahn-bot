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
        context = await browser.new_context()
        page = await context.new_page()
        await page.set_viewport_size({"width": 1280, "height": 800})

        try:
            logging.info("🔐 Starte Login bei X...")
            await page.goto("https://twitter.com/login", timeout=60000)
            await page.wait_for_load_state("networkidle")

            # Benutzername
            await page.wait_for_selector('input[name="text"], input[name="username"]', timeout=20000)
            input_selector = 'input[name="text"]' if await page.query_selector('input[name="text"]') else 'input[name="username"]'
            await page.fill(input_selector, user)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)

            # Passwort
            await page.wait_for_selector('input[name="password"]', timeout=20000)
            await page.fill('input[name="password"]', pw)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000)

            # Navigiere zur Tweet-Seite
            await page.goto("https://twitter.com/compose/tweet", timeout=60000)
            await page.wait_for_load_state("networkidle")

            # Sicherstellen, dass Tweet-Feld existiert
            tweet_box = await page.query_selector('div[aria-label="Tweet text"]')
            if not tweet_box:
                html = await page.content()
                logging.error("❌ Tweet-Feld nicht gefunden.\n🔍 HTML-Snapshot:\n" + html[:1000])
                return

            for thread in threads:
                first = True
                for tweet in thread:
                    await tweet_box.click()
                    await tweet_box.fill("")
                    await tweet_box.type(tweet)
                    await page.wait_for_timeout(1000)

                    tweet_button = await page.query_selector('div[data-testid="tweetButtonInline"]') or await page.query_selector('div[data-testid="tweetButton"]')
                    if tweet_button:
                        await tweet_button.click()
                    else:
                        logging.warning("⚠️ Kein Tweet-Button gefunden.")
                    first = False

                    await page.wait_for_timeout(3000)

            logging.info("✅ Alle Tweets gesendet!")
        except Exception as e:
            html = await page.content()
            logging.error(f"❌ Fehler beim Tweeten: {e}\n🔍 HTML-Snapshot:\n{html[:1000]}")
        finally:
            await browser.close()
