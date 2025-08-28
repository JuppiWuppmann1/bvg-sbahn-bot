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
                if "sameSite" not in cookie or cookie["sameSite"] not in ["Strict", "Lax", "None"]:
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
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(60000)

        try:
            await load_cookies(context)
        except Exception as e:
            logging.error(f"❌ Abbruch: Cookies konnten nicht geladen werden: {e}")
            await browser.close()
            return

        await page.goto("https://x.com/home", timeout=60000)
        if any(keyword in page.url for keyword in ["login", "flow", "redirect_after_login"]):
            logging.error("❌ Cookies ungültig – bitte manuell erneuern.")
            await browser.close()
            return

        for i, thread in enumerate(threads, 1):
            try:
                logging.info(f"✍️ Starte Thread {i}...")
                await page.goto("https://x.com/compose/tweet", timeout=60000)

                try:
                    await page.wait_for_selector("div[data-testid='tweetTextarea_0']", timeout=30000)
                except Exception:
                    logging.warning("⚠️ Tweet-Feld nicht sichtbar – Screenshot zur Analyse...")
                    await page.screenshot(path=f"tweet_field_missing_{i}.png")
                    continue

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
