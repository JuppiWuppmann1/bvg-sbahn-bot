import logging
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def scrape_sbahn():
    url = "https://sbahn.berlin/fahren/bauen-stoerung/"
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(3000)  # Warten auf JS-Inhalte

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        for item in soup.select("div.c-construction-announcement"):
            titel_tag = item.select_one("h3.o-construction-announcement-title__heading")
            beschreibung_tag = item.select_one("div.c-construction-announcement-details")

            titel = titel_tag.get_text(strip=True) if titel_tag else ""
            beschreibung_raw = beschreibung_tag.get_text(" ", strip=True) if beschreibung_tag else ""

            # 🧹 Entferne irrelevante UI-Texte
            beschreibung_raw = re.sub(r"(Ausführliche Informationen\s*)?(schließen\s*){1,}", "", beschreibung_raw, flags=re.IGNORECASE)

            # ✂️ Beschreibung in Absätze aufteilen
            beschreibung_parts = re.split(r'(?<=[.!?])\s+', beschreibung_raw)
            beschreibung = "\n".join(beschreibung_parts)

            # 🧾 Vollständige Meldung ins Log schreiben
            logging.info(f"🚆 Vollständige Meldung:\nTitel: {titel}\nBeschreibung:\n{beschreibung}\n{'-'*80}")

            meldungen.append({
                "quelle": "S-Bahn",
                "titel": titel,
                "beschreibung": beschreibung
            })

        await browser.close()

    logging.info(f"✅ S-Bahn-Scraper hat {len(meldungen)} Meldungen gefunden.")
    return meldungen
