import logging
import httpx
from bs4 import BeautifulSoup

async def scrape_sbahn():
    url = "https://sbahn.berlin/fahren/bauen-stoerung/"
    meldungen = []

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Beispiel: alle Cards mit Störungsmeldungen
        for item in soup.select("div.card"):
            titel = item.select_one("h3, h2")
            beschreibung = item.select_one("p")
            t = titel.get_text(strip=True) if titel else ""
            b = beschreibung.get_text(" ", strip=True) if beschreibung else ""

            # 👉 Debug-Logging
            logging.info(f"🚆 Gefunden: {t} – {b[:100]}")

            meldungen.append({
                "quelle": "S-Bahn",
                "titel": t,
                "beschreibung": b
            })

    logging.info(f"✅ S-Bahn-Scraper hat {len(meldungen)} Meldungen gefunden.")
    return meldungen
