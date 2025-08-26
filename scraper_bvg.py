import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"


def scrape_bvg(max_pages: int = 5):
    """
    Holt BVG-Störungen inkl. aller Seiten (Pagination).
    Gibt eine Liste von Dicts zurück:
    {
        "quelle": "BVG",
        "titel": "...",
        "beschreibung": "...",
        "von": "...",
        "bis": "...",
        "zeitraum": "...",
        "linien": ["M5", "U2"],
        "art": "Aufzugsstörung"
    }
    """
    meldungen = []

    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}?p={page}"
        logger.info(f"🔎 Lade BVG-Seite {page}: {url}")
        resp = requests.get(url, timeout=20)

        if resp.status_code != 200:
            logger.warning(f"⚠️ Konnte BVG-Seite {page} nicht laden (HTTP {resp.status_code})")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("li.traffic-item")

        if not items:
            logger.info(f"ℹ️ Keine weiteren BVG-Meldungen auf Seite {page}")
            break

        for item in items:
            try:
                titel = item.select_one(".traffic-item-title")
                titel = titel.get_text(strip=True) if titel else "BVG-Meldung"

                beschreibung = item.select_one(".traffic-item-description")
                beschreibung = beschreibung.get_text(" ", strip=True) if beschreibung else ""

                zeitraum = item.select_one(".traffic-item-date")
                zeitraum = zeitraum.get_text(" ", strip=True) if zeitraum else None

                von, bis = None, None
                if zeitraum and "bis" in zeitraum:
                    parts = zeitraum.split("bis")
                    von = parts[0].strip()
                    bis = parts[1].strip()

                linien = [l.get_text(strip=True) for l in item.select(".traffic-item-lines span")] or []

                art = "Aufzugsstörung" if "Aufzug" in titel else "Störung"

                meldungen.append({
                    "quelle": "BVG",
                    "titel": titel,
                    "beschreibung": beschreibung,
                    "zeitraum": zeitraum,
                    "von": von,
                    "bis": bis,
                    "linien": linien,
                    "art": art,
                })
            except Exception as e:
                logger.error(f"❌ Fehler beim Parsen einer BVG-Meldung: {e}")

    logger.info(f"✅ {len(meldungen)} BVG-Meldungen gesammelt")
    return meldungen

