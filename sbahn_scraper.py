import logging
import httpx
from bs4 import BeautifulSoup

async def scrape_sbahn():
    url = "https://sbahn.berlin/fahren/bauen-stoerung/"
    meldungen = []

    logging.info(f"🌐 Lade S-Bahn-Seite: {url}")
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=30)
        r.raise_for_status()
        html = r.text

    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("div.meldungsteaser")

    for item in items:
        titel_tag = item.select_one("h3")
        beschreibung_tag = item.select_one("p")

        titel = titel_tag.get_text(strip=True) if titel_tag else "Unbekannt"
        beschreibung = beschreibung_tag.get_text(strip=True) if beschreibung_tag else ""

        meldungen.append({
            "quelle": "S-Bahn",
            "titel": titel,
            "beschreibung": beschreibung
        })

        logging.info(f"🚆 Vollständige Meldung:\nTitel: {titel}\nBeschreibung:\n{beschreibung}\n{'-'*60}")

    logging.info(f"✅ S-Bahn-Scraper hat {len(meldungen)} Meldungen gefunden.")
    return meldungen
