import logging
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.bvg.de/de/verbindungen/stoerungen"

def scrape_bvg():
    meldungen = []
    logging.info("📡 Scraping BVG...")

    try:
        resp = httpx.get(BASE_URL, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.find_all("div", class_="NotificationItemVersionTwo_root__")
        for item in items:
            titel = item.find("h3")
            details = item.find("span", class_="NotificationItemVersionTwo_content__kw1Ui")
            zeitraum = item.find("div", class_="NotificationItemVersionTwo_date__")

            meldungen.append({
                "quelle": "BVG",
                "titel": titel.get_text(strip=True) if titel else "Unbekannt",
                "beschreibung": details.get_text(" ", strip=True) if details else "",
                "zeitraum": zeitraum.get_text(" ", strip=True) if zeitraum else None,
                "linien": []  # kannst du später erweitern
            })

        logging.info(f"✅ {len(meldungen)} Meldungen von BVG")
    except Exception as e:
        logging.error(f"❌ Fehler beim BVG-Scraping: {e}")

    return meldungen
