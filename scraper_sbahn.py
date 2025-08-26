import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

URL = "https://sbahn.berlin/fahren/bauen-stoerung/"

def scrape_sbahn():
    """Scrapt aktuelle S-Bahn Meldungen"""
    results = []
    r = requests.get(URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.select(".mod-message-teaser")
    for item in items:
        try:
            title = item.select_one(".mod-message-teaser__headline").get_text(strip=True)
            details = item.select_one(".mod-message-teaser__content").get_text(" ", strip=True)

            msg = format_sbahn_message(title, details)
            results.append(msg)
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Parsen S-Bahn: {e}")

    return results

def format_sbahn_message(title, details):
    """Formatiert eine S-Bahn Meldung kompakt"""
    msg = f"🚆 S-Bahn-Meldung: {title}\n"
    msg += f"📍 {details[:200]}..." if len(details) > 200 else f"📍 {details}"
    return msg
