import logging
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

COOKIES_FILE = Path("x_cookies.json")

async def login_and_save_cookies(page, username, password, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"🔐 Login-Versuch {attempt} bei X...")
            await page.goto("https://x.com/i/flow/login", timeout=60000)

            # Schritt 1: Benutzername eingeben
            await page.wait_for_selector("input", timeout=30000)
            await page.fill("input", username)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)

            # Schritt 2: Passwortfeld erscheint
            await page.wait_for_selector("input[type='password']", timeout=30000)
            await page.fill("input[type='password']", password)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000)

            # Schritt 3: Weiterleitung prüfen
            await page.goto("https://x.com/home", timeout=60000)
            await page.wait_for_timeout(8000)
            current_url = page.url
            logging.info(f"🔍 Aktuelle URL nach Login: {current_url}")

            if "login" in current_url or "flow" in current_url:
                raise Exception("Noch im Login-Flow – Login fehlgeschlagen")

            # Schritt 4: Tweet-Feld oder Compose-Link prüfen
            tweet_field = await page.query_selector("div[data-testid='tweetTextarea_0']")
            compose_link = await page.query_selector("a[href='/compose/tweet']")
            compose_button = await page.query_selector("div[aria-label='Tweet verfassen']")

            if tweet_field or compose_link or compose_button:
                logging.info("✅ Login erfolgreich, speichere Cookies...")
                cookies = await page.context.cookies()
                COOKIES_FILE.write_text(json.dumps(cookies))
                return
            else:
                logging.warning("⚠️ Tweet-Feld nicht gefunden – versuche direkten Zugriff...")
                await page.goto("https://x.com/compose/tweet", timeout=60000)
                try:
                    await page.wait_for_selector("div[data-testid='tweetTextarea_0']", timeout=10000)
                    logging.info("✅ Tweet-Feld über Compose-Seite gefunden – Login abgeschlossen.")
                    cookies = await page.context.cookies()
                    COOKIES_FILE.write_text(json.dumps(cookies))
                    return
                except Exception:
                    raise Exception("Tweet-Feld auch über Compose-Seite nicht erreichbar.")

        except Exception as e:
            logging.error(f"❌ Login-Versuch {attempt} fehlgeschlagen: {e}")
            await page.screenshot(path=f"login_failed_{attempt}.png")
            html = await page.content()
            Path(f"login_failed_{attempt}.html").write_text(html, encoding="utf-8")

    raise Exception("❌ Alle Login-Versuche fehlgeschlagen")

async def load_cookies_if_exist(context):
    if COOKIES_FILE.exists():
        try:
            cookies = json.loads(COOKIES_FILE.read_text())
            await context.add_cookies(cookies)
            logging.info("🍪 Cookies geladen, versuche Session wiederzuverwenden...")
            return True
        except Exception as e:
            logging.warning(f"⚠️ Konnte Cookies nicht laden: {e}")
    return False

async def post_threads(threads):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(60000)

        from os import getenv
        username = getenv("TWITTER_USER")
        password = getenv("TWITTER_PASS")

        if not await load_cookies_if_exist(context):
            await login_and_save_cookies(page, username, password)

        await page.goto("https://x.com/home", timeout=60000)
        if "login" in page.url or "flow" in page.url:
            logging.info("⚠️ Cookies ungültig, erneut einloggen...")
            await login_and_save_cookies(page, username, password)

        for i, thread in enumerate(threads, 1):
            try:
                logging.info(f"✍️ Starte Thread {i}...")
                await page.goto("https://x.com/compose/tweet", timeout=60000)

                tweet_field = await page.query_selector("div[data-testid='tweetTextarea_0']")
                if not tweet_field:
                    logging.info("🕵️ Tweet-Feld nicht sichtbar – versuche erneut...")
                    await page.goto("https://x.com/compose/tweet", timeout=60000)
                    await page.wait_for_selector("div[data-testid='tweetTextarea_0']", timeout=30000)

                await page.fill("div[data-testid='tweetTextarea_0']", thread[0])

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
