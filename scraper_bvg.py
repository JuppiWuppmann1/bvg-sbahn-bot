import logging
from playwright.async_api import async_playwright

async def fetch_bvg():
    url = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=60000)
            page_nr = 1
            while True:
                logging.info(f"📡 BVG Seite {page_nr} laden...")
                await page.wait_for_selector("li.DisruptionsOverviewVersionTwo_item__GvWfq", timeout=15000)
                items = await page.query_selector_all("li.DisruptionsOverviewVersionTwo_item__GvWfq")

                for item in items:
                    titel_el = await item.query_selector("h3")
                    titel = await titel_el.inner_text() if titel_el else "Unbekannt"

                    beschreibung_el = await item.query_selector("div.NotificationItemVersionTwo_content__kw1Ui")
                    beschreibung = await beschreibung_el.inner_text() if beschreibung_el else ""

                    meldung = {
                        "quelle": "BVG",
                        "titel": titel.strip(),
                        "beschreibung": beschreibung.strip(),
                    }
                    logging.info(f"📍 BVG-Meldung gefunden: {meldung['titel']}")
                    meldungen.append(meldung)

                next_button = await page.query_selector("a[aria-label='Nächste Seite']")
                if next_button and await next_button.is_enabled():
                    await next_button.click()
                    await page.wait_for_timeout(2000)
                    page_nr += 1
                else:
                    break
        except Exception as e:
            logging.error(f"❌ Fehler beim BVG-Scraping: {e}")
        finally:
            await browser.close()

    return meldungen

