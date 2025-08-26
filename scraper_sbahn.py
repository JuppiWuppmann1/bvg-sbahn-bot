import logging
from playwright.async_api import async_playwright

async def fetch_sbahn():
    url = "https://sbahn.berlin/fahren/bauen-stoerung/"
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_selector("div.c-teaser", timeout=20000)
            items = await page.query_selector_all("div.c-teaser")

            for item in items:
                titel = (await item.query_selector("h3")).inner_text() if await item.query_selector("h3") else "Unbekannt"
                beschreibung = (await item.inner_text()) or ""
                meldungen.append({
                    "quelle": "S-Bahn",
                    "titel": titel.strip(),
                    "beschreibung": beschreibung.strip(),
                })

            logging.info(f"📥 {len(meldungen)} Meldungen von S-Bahn geladen.")
        except Exception as e:
            logging.error(f"❌ Fehler beim S-Bahn-Scraping: {e}")
        finally:
            await browser.close()

    return meldungen
