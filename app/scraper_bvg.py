import hashlib, re, time
import requests
from bs4 import BeautifulSoup
from .settings import settings

BASE_URL = "https://www.bvg.de"
LIST_URL = f"{BASE_URL}/de/verbindungen/stoerungsmeldungen"

HEADERS = {"User-Agent": settings.USER_AGENT}

def fetch_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.text

def extract_detail_text(_href: str):
    # Bei den neuen BVG-Meldungen gibt es keine Detailseiten mehr → nur Headline
    return ""

def parse_items(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # Jedes Störungskärtchen
    cards = soup.select("div.NotificationItemVersionTwo_contentWrapper__Q2nB")
    items = []

    for c in cards:
        # Titel/Überschrift
        title_el = c.select_one(".NotificationItemVersionTwo_headline__1jvz2")
        title = title_el.get_text(" ", strip=True) if title_el else ""
        if not title:
            continue

        # Datum + Uhrzeit zusammensetzen
        date_parts = [
            d.get_text(" ", strip=True)
            for d in c.select(".NotificationItemVersionTwo_moddateText__Y5lQ7")
        ]
        timestamp = " ".join(date_parts).strip()

        # Linien herausziehen (U/S/M/Bus/Tram)
        m = re.search(r"(U\d+|S\d+|M\d+|Bus\s*\d+|Tram\s*\d+)", title)
        lines = m.group(0) if m else None

        # Eindeutige ID inkl. Zeitstempel, damit Updates erkannt werden
        key = (title + (lines or "") + timestamp).encode("utf-8")
        _id = "BVG-" + hashlib.sha1(key).hexdigest()

        # Content Hash nur auf Basis des Titels
        content_hash = hashlib.sha1(title.encode("utf-8")).hexdigest()

        items.append({
            "id": _id,
            "source": "BVG",
            "title": title,
            "lines": lines,
            "url": None,         # kein Link vorhanden
            "content_hash": content_hash,
            "detail": title,     # Detailtext = Headline
            "timestamp": timestamp
        })

    return items

def fetch_all_items():
    all_items = []
    # Bei BVG gibt es aktuell keine Pagination → nur eine Seite holen
    html = fetch_html(LIST_URL)
    items = parse_items(html)
    all_items.extend(items)
    time.sleep(1)
    return all_items
