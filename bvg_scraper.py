from playwright.async_api import async_playwright
import logging
import json

async def scrape_bvg():
    url = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Intercept JSON responses
        async def handle_response(response):
            if "stoerungsmeldungen" in response.url and response.headers.get("content-type", "").startswith("application/json"):
                try:
                    data = await response.json()
                    for item in data.get("items", []):
                        meldung = {
                            "zeit": item.get("date"),
                            "beschreibung": item.get("description")
                        }
                        logging.info(f"🕒 {meldung['zeit']}\n📝 {meldung['beschreibung']}\n{'-'*60}")
                        meldungen.append(meldung)
                except Exception as e:
                    logging.warning(f"⚠️ Fehler beim Parsen der JSON-Daten: {e}")

        page.on("response", handle_response)

        logging.info(f"🌐 Lade BVG-Seite: {url}")
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(5000)

        await browser.close()

    logging.info(f"✅ BVG-Scraper hat insgesamt {len(meldungen)} Meldungen extrahiert.")
    return meldungen
