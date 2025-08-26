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
                titel_el = await item.query_selector("h3")
                titel = await titel_el.inner_text() if titel_el else "Unbekannt"

                beschreibung = await item.inner_text() or ""

                meldung = {
                    "quelle": "S-Bahn",
                    "titel": titel.strip(),
                    "beschreibung": beschreibung.strip(),
                }
                logging.info(f"📍 S-Bahn-Meldung gefunden: {meldung['titel']}")
                meldungen.append(meldung)

            logging.info(f"📥 {len(meldungen)} Meldungen von S-Bahn geladen.")
        except Exception as e:
            logging.error(f"❌ Fehler beim S-Bahn-Scraping: {e}")
        finally:
            await browser.close()

    return meldungen

