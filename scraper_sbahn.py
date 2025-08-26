import logging
import re
from playwright.async_api import async_playwright

async def parse_sbahn_details(item):
    # Linien aus data-lines
    data_lines = await item.get_attribute("data-lines")
    linien = data_lines.upper().split(",") if data_lines else []

    # Titel (Streckenabschnitt)
    titel_el = await item.query_selector("h3.o-construction-announcement-title__heading")
    titel = await titel_el.inner_text() if titel_el else "Unbekannt"

    # Zeitraum
    zeitraum_el = await item.query_selector("div.o-timespan__center.o-timespan__cp")
    zeitraum_text = await zeitraum_el.inner_text() if zeitraum_el else ""
    zeitraum = re.findall(r"\d{2}\.\d{2}\.", zeitraum_text)

    # Maßnahme
    labels = await item.query_selector_all("div.c-construction-announcement-foot__labels span")
    maßnahmen = [await label.inner_text() for label in labels]
    maßnahme = ", ".join(maßnahmen) if maßnahmen else None

    # Beschreibung
    beschreibung_el = await item.query_selector("div.c-construction-announcement-details ul")
    beschreibung = await beschreibung_el.inner_text() if beschreibung_el else ""

    return {
        "linien": ", ".join(linien),
        "titel": titel.strip(),
        "zeitraum": zeitraum,
        "maßnahme": maßnahme,
        "beschreibung": beschreibung.strip()
    }

async def fetch_sbahn():
    url = "https://sbahn.berlin/fahren/bauen-stoerung/"
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_selector("div.c-construction-announcement", timeout=20000)
            items = await page.query_selector_all("div.c-construction-announcement")

            for item in items:
                details = await parse_sbahn_details(item)

                meldung = {
                    "quelle": "S-Bahn",
                    "titel": details["titel"],
                    "beschreibung": details["beschreibung"],
                    "linie": details["linien"],
                    "maßnahme": details["maßnahme"],
                    "zeitraum": details["zeitraum"]
                }

                logging.info(f"📍 S-Bahn-Meldung: {meldung}")
                meldungen.append(meldung)

            logging.info(f"✅ {len(meldungen)} relevante Meldungen von S-Bahn")
        except Exception as e:
            logging.error(f"❌ Fehler beim S-Bahn-Scraping: {e}")
        finally:
            await browser.close()

    return meldungen
