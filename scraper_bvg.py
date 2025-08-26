import logging
import re
from playwright.async_api import async_playwright

def parse_bvg_details(text):
    von = re.search(r"Von\s+(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2})", text)
    bis = re.search(r"Bis\s+(?:auf weiteres|(\d{2}\.\d{2}\.\d{4}))", text)
    linien = re.findall(r"\b(?:Bus\s)?[MX]?\d{1,3}\b", text)
    maßnahme = re.search(r"(Haltestelle verlegt|Ersatzverkehr|Pendelverkehr)", text)
    ort = re.search(r"Haltestelle\s+verlegt.*?([A-Za-zäöüÄÖÜß\s\/\-]+)", text)

    return {
        "von": von.group(1) if von else None,
        "bis": bis.group(1) if bis and bis.group(1) else "Bis auf weiteres",
        "linien": ", ".join(linien),
        "maßnahme": maßnahme.group(1) if maßnahme else None,
        "ort": ort.group(1).strip() if ort else None
    }

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

                    details = parse_bvg_details(beschreibung)

                    meldung = {
                        "quelle": "BVG",
                        "titel": titel.strip(),
                        "beschreibung": beschreibung.strip(),
                        "details": details
                    }

                    logging.info(f"📍 BVG-Meldung: {meldung['titel']} | Details: {details}")
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
