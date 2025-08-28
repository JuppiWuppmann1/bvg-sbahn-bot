import logging
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

COOKIES_FILE = Path("x_cookies.json")

async def load_cookies(context):
    if COOKIES_FILE.exists():
        try:
            cookies = json.loads(COOKIES_FILE.read_text())
            for cookie in cookies:
                if "sameSite" not in cookie or cookie["sameSite"].lower() not in ["strict", "lax", "none"]:
                    cookie["sameSite"] = "Lax"
            await context.add_cookies(cookies)
            logging.info("🍪 Cookies geladen und hinzugefügt.")
        except Exception as e:
            logging.error(f"❌ Fehler beim Laden der Cookies: {e}")
            raise
    else:
        raise Exception("❌ Cookie-Datei x_cookies.json nicht gefunden.")

async def post_threads(threads):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0.0.0 Safari/537.36",
            locale="de-DE",
            viewport={"width": 1280, "height": 800},
            device_scale_factor=1,
            timezone_id="Europe/Berlin"
        )
        page = await context.new_page()
        page.set_default_timeout(60000)

        try:
            await load_cookies(context)
        except Exception as e:
            logging.error(f"❌ Abbruch: Cookies konnten nicht geladen werden: {e}")
            await browser.close()
            return

        await page.goto("https://x.com/home", timeout=60000)
        html = await page.content()
        logging.debug("📄 HTML-Ausschnitt der Startseite:\n" + html[:1000])

        # Session-Check: Compose-Link muss vorhanden sein
        if not await page.query_selector("a[href='/compose/tweet']"):
            logging.error("❌ Session nicht aktiv – kein Compose-Link gefunden.")
            Path("session_invalid.html").write_text(html, encoding="utf-8")
            await page.screenshot(path="session_invalid.png")
            await browser.close()
            return

        for i, thread in enumerate(threads, 1):
            try:
                logging.info(f"✍️ Starte Thread {i}...")
                await page.goto("https://x.com/compose/tweet", timeout=60000)

                tweet_field = None
                selectors = [
                    "div[data-testid='tweetTextarea_0']",
                    "div[aria-label='Tweet verfassen']",
                    "div[role='textbox']",
                    "textarea"
                ]

                for attempt in range(3):
                    for selector in selectors:
                        try:
                            await page.wait_for_selector(selector, timeout=5000)
                            tweet_field = await page.query_selector(selector)
                            if tweet_field:
                                break
                        except:
                            continue
                    if tweet_field:
                        break
                    logging.warning(f"⚠️ Versuch {attempt+1}: Tweet-Feld nicht sichtbar...")
                    await asyncio.sleep(2)

                if not tweet_field:
                    logging.error("❌ Tweet-Feld nicht gefunden – Screenshot & HTML gespeichert.")
                    await page.screenshot(path=f"tweet_field_missing_{i}.png")
                    html = await page.content()
                    Path(f"tweet_field_missing_{i}.html").write_text(html, encoding="utf-8")
                    continue

                await tweet_field.fill(thread[0])

                for reply in thread[1:]:
                    await page.click("div[data-testid='tweetButtonInline']")
                    await page.wait_for_selector("div[data-testid='tweetTextarea_0']", timeout=30000)
                    await page.fill("div[data-testid='tweetTextarea_0']", reply)

                await page.click("div[data-testid='tweetButtonInline']")
                logging.info(f"✅ Thread {i} gepostet!")
                await asyncio.sleep(5)

            except Exception as e:
                html = await page.content()
                Path(f"tweet_error_{i}.html").write_text(html, encoding="utf-8")
                await page.screenshot(path=f"tweet_error_{i}.png")
                logging.error(f"❌ Fehler beim Tweeten: {e}")

        await browser.close()
