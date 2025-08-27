from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging
import re

async def scrape_bvg():
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Seiten 1 bis 5 durchgehen
        for page_num in range(1, 6):
            url = f"https://www.bvg.de/de/verbindungen/stoerungsmeldungen?page={page_num}"
            logging.info(f"🌐 Lade BVG-Seite {page_num}: {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(3000)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            for item in soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq"):
                titel_tag = item.select_one("h3")
                beschreibung_tag = item.select_one("span.NotificationItemVersionTwo_content__kw1Ui p")

                titel = titel_tag.get_text(strip=True) if titel_tag else ""
                beschreibung_raw = beschreibung_tag.get_text(" ", strip=True) if beschreibung_tag else ""

                # 🧹 Bereinige irrelevante UI-Texte
                beschreibung_raw = re.sub(r"(Ausführliche Informationen|Bauvideo|schließen)+", "", beschreibung_raw, flags=re.IGNORECASE)
                beschreibung_raw = re.sub(r"\s{2,}", " ", beschreibung_raw).strip()

                # ✂️ Beschreibung in Absätze aufteilen
                beschreibung_parts = re.split(r'(?<=[.!?])\s+', beschreibung_raw)
                beschreibung = "\n".join(beschreibung_parts)

                logging.info(f"🚇 Vollständige Meldung:\nTitel: {titel}\nBeschreibung:\n{beschreibung}\n{'-'*60}")

                meldungen.append({
                    "quelle": "BVG",
                    "titel": titel,
                    "beschreibung": beschreibung
                })

        await browser.close()

    logging.info(f"✅ BVG-Scraper hat {len(meldungen)} Meldungen gefunden.")
    return meldungen

