import logging
import re
from playwright.async_api import async_playwright

def is_relevant_sbahn_meldung(beschreibung):
    beschreibung = beschreibung.lower()
    if "wieso wird gebaut" in beschreibung or "gründe für störungen" in beschreibung:
        return False
    if not any(keyword in beschreibung for keyword in ["störung", "ausfall", "unterbrechung", "verspätung"]):
        return False
    return True

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
                titel = await titel_el.inner_text() if titel_el else None
                beschreibung = await item.inner_text() or ""

                if not is_relevant_sbahn_meldung(beschreibung):
                    logging.info("⏭️ Allgemeine Info übersprungen.")
                    continue

                linie = re.search(r"S\d+", beschreibung)
                grund = re.search(r"(Bauarbeiten|Störung|Verspätung|Ausfall)", beschreibung)
                zeitraum = re.findall(r"\d{2}\.\d{2}\.\d{4}", beschreibung)

                meldung = {
                    "quelle": "S-Bahn",
                    "titel": titel.strip() if titel else "Unbekannt",
                    "beschreibung": beschreibung.strip(),
                    "linie": linie.group(0) if linie else None,
                    "grund": grund.group(1) if grund else None,
                    "zeitraum": zeitraum
                }

                logging.info(f"📍 S-Bahn-Meldung: {meldung}")
                meldungen.append(meldung)

            logging.info(f"✅ {len(meldungen)} relevante Meldungen von S-Bahn")
        except Exception as e:
            logging.error(f"❌ Fehler beim S-Bahn-Scraping: {e}")
        finally:
            await browser.close()

    return meldungen
