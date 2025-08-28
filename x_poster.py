import logging
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

COOKIES_FILE = Path("x_cookies.json")

async def login_and_save_cookies(page, username, password):
    logging.info("🔐 Starte Login bei X...")

    await page.goto("https://twitter.com/login", timeout=60000)
    await page.wait_for_selector("input[name='text']", timeout=30000)
    await page.fill("input[name='text']", username)
    await page.press("input[name='text']", "Enter")

    await page.wait_for_selector("input[name='password']", timeout=30000)
    await page.fill("input[name='password']", password)
    await page.press("input[name='password']", "Enter")

    try:
        # Warte auf etwas, das NUR eingeloggt sichtbar ist
        await page.wait_for_selector("div[data-testid='tweetTextarea_0']", timeout=60000)
    except Exception as e:
        logging.error(f"❌ Login-Check fehlgeschlagen: {e}")
        await page.screenshot(path="login_failed.png")
        html = await page.content()
        Path("login_failed.html").write_text(html, encoding="utf-8")
        raise

    logging.info("✅ Login erfolgreich, speichere Cookies...")
    cookies = await page.context.cookies()
    COOKIES_FILE.write_text(json.dumps(cookies))

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
        page.set_default_timeout(60000)  # Timeout erhöhen

        from os import getenv
        username = getenv("TWITTER_USER")
        password = getenv("TWITTER_PASS")

        if not await load_cookies_if_exist(context):
            await login_and_save_cookies(page, username, password)

        # sicherstellen, dass wir eingeloggt sind
        await page.goto("https://twitter.com/home", timeout=60000)
        if "login" in page.url:
            logging.info("⚠️ Cookies ungültig, erneut einloggen...")
            await login_and_save_cookies(page, username, password)

        # jetzt Threads posten
        for i, thread in enumerate(threads, 1):
            try:
                logging.info(f"✍️ Starte Thread {i}...")
                await page.goto("https://twitter.com/compose/tweet", timeout=60000)
                await page.wait_for_selector("div[data-testid='tweetTextarea_0']", timeout=30000)
                await page.fill("div[data-testid='tweetTextarea_0']", thread[0])

                # wenn mehrere Teile → als Antwort posten
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
                logging.error(f"❌ Fehler beim Tweeten: {e} (siehe tweet_error_{i}.html / .png)")

        await browser.close()
