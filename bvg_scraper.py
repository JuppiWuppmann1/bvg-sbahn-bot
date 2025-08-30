import logging
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def scrape_bvg():
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        logging.info("🌐 Lade BVG-Seite: https://www.bvg.de/de/verbindungen/stoerungsmeldungen")
        await page.goto("https://www.bvg.de/de/verbindungen/stoerungsmeldungen", timeout=60000)
        await page.wait_for_timeout(3000)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        for item in soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq"):
            titel_tag = item.select_one("h3")
            beschreibung_tag = item.select_one("span.NotificationItemVersionTwo_content__kw1Ui p")

            titel = titel_tag.get_text(" ", strip=True) if titel_tag else ""
            beschreibung_raw = beschreibung_tag.get_text(" ", strip=True) if beschreibung_tag else ""

            beschreibung_raw = re.sub(r"(Ausführliche Informationen|Bauvideo|schließen)+", "", beschreibung_raw, flags=re.IGNORECASE)
            beschreibung_raw = re.sub(r"\s{2,}", " ", beschreibung_raw).strip()

            meldungen.append({
                "quelle": "BVG",
                "titel": titel,
                "beschreibung": beschreibung_raw
            })

            logging.info(f"🚇 Vollständige Meldung:\nTitel: {titel}\nBeschreibung:\n{beschreibung_raw}\n{'-'*60}")

        await browser.close()

    logging.info(f"✅ BVG-Scraper hat {len(meldungen)} Meldungen extrahiert.")
    return meldungen
