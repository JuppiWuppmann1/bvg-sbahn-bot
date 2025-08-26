import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

URL = "https://sbahn.berlin/fahren/bauen-stoerung/"


def scrape_sbahn():
    """
    Holt S-Bahn-Störungen.
    Gibt eine Liste von Dicts zurück:
    {
        "quelle": "S-Bahn",
        "titel": "...",
        "beschreibung": "...",
        "von": "...",
        "bis": "...",
        "zeitraum": "...",
        "linien": ["S1", "S25"],
    }
    """
    meldungen = []

    resp = requests.get(URL, timeout=20)
    if resp.status_code != 200:
        logger.error(f"⚠️ Konnte S-Bahn-Seite nicht laden (HTTP {resp.status_code})")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select("div.module-teaser--disruption")

    for item in items:
        try:
            titel = item.select_one(".module-teaser__title")
            titel = titel.get_text(strip=True) if titel else "S-Bahn-Meldung"

            beschreibung = item.select_one(".module-teaser__text")
            beschreibung = beschreibung.get_text(" ", strip=True) if beschreibung else ""

            zeitraum = item.select_one(".module-teaser__date")
            zeitraum = zeitraum.get_text(" ", strip=True) if zeitraum else None

            von, bis = None, None
            if zeitraum and "bis" in zeitraum:
                parts = zeitraum.split("bis")
                von = parts[0].strip()
                bis = parts[1].strip()

            linien = [l.get_text(strip=True) for l in item.select(".module-teaser__lines span")] or []

            meldungen.append({
                "quelle": "S-Bahn",
                "titel": titel,
                "beschreibung": beschreibung,
                "zeitraum": zeitraum,
                "von": von,
                "bis": bis,
                "linien": linien,
            })
        except Exception as e:
            logger.error(f"❌ Fehler beim Parsen einer S-Bahn-Meldung: {e}")

    logger.info(f"✅ {len(meldungen)} S-Bahn-Meldungen gesammelt")
    return meldungen

