import logging
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://sbahn.berlin/meldungen/"

def scrape_sbahn():
    meldungen = []
    logging.info("📡 Scraping S-Bahn...")

    try:
        resp = httpx.get(BASE_URL, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.find_all("div", class_="teaser")
        for item in items:
            titel = item.find("h3")
            beschreibung = item.find("p")

            meldungen.append({
                "quelle": "S-Bahn",
                "titel": titel.get_text(strip=True) if titel else "Unbekannt",
                "beschreibung": beschreibung.get_text(" ", strip=True) if beschreibung else "",
                "zeitraum": None,
                "linien": []
            })

        logging.info(f"✅ {len(meldungen)} Meldungen von S-Bahn")
    except Exception as e:
        logging.error(f"❌ Fehler beim S-Bahn-Scraping: {e}")

    return meldungen
