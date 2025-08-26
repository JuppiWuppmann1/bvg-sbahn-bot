import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"

def scrape_bvg(max_pages=3):
    """Scrapt BVG-Meldungen über mehrere Seiten"""
    results = []

    for page in range(1, max_pages+1):
        url = f"{BASE_URL}{page}"
        logger.info(f"🌐 Scraping {url}")
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        cards = soup.select(".m-teaser__inner")
        for card in cards:
            try:
                line = card.select_one(".m-teaser__eyebrow").get_text(strip=True)
                title = card.select_one(".m-teaser__headline").get_text(strip=True)
                body = card.select_one(".m-teaser__content").get_text(" ", strip=True)

                msg = format_bvg_message(line, title, body)
                results.append(msg)
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Parsen: {e}")

    return results

def format_bvg_message(line, title, body):
    """Formatiert eine BVG-Meldung kompakt"""
    msg = f"🚌 BVG-Meldung: {title}\n"
    if line:
        msg += f"🔹 Linie: {line}\n"
    msg += f"📍 {body[:200]}..." if len(body) > 200 else f"📍 {body}"
    return msg
