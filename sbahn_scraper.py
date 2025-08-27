import logging
import httpx
from bs4 import BeautifulSoup
import re

async def scrape_sbahn():
    url = "https://sbahn.berlin/fahren/bauen-stoerung/"
    meldungen = []

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SBahn-Scraper/1.0; +https://bvg-sbahn-bot.onrender.com)"
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for item in soup.select("div.c-construction-announcement"):
            titel_tag = item.select_one("h3.o-construction-announcement-title__heading")
            beschreibung_tag = item.select_one("div.c-construction-announcement-details")

            titel = titel_tag.get_text(strip=True) if titel_tag else ""
            beschreibung_raw = beschreibung_tag.get_text(" ", strip=True) if beschreibung_tag else ""

            # 🔍 Beschreibung in sinnvolle Abschnitte aufteilen
            beschreibung_parts = re.split(r'(?<=[.!?])\s+', beschreibung_raw)
            beschreibung = "\n".join(beschreibung_parts)

            # 🧾 Vollständige Meldung ins Log schreiben
            logging.info(f"🚆 Vollständige Meldung:\nTitel: {titel}\nBeschreibung:\n{beschreibung}\n{'-'*80}")

            meldungen.append({
                "quelle": "S-Bahn",
                "titel": titel,
                "beschreibung": beschreibung
            })

    logging.info(f"✅ S-Bahn-Scraper hat {len(meldungen)} Meldungen gefunden.")
    return meldungen
