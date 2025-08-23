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
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.text

def extract_detail_text(_href: str):
    # Bei den neuen BVG-Meldungen gibt es keine Detailseiten mehr → nur Headline
    return ""

def parse_items(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # Selektor robuster machen (enthält NotificationItemVersionTwo)
    cards = soup.select("div[class*='NotificationItemVersionTwo_contentWrapper']")
    print("DEBUG BVG: Gefundene Cards:", len(cards))

    items = []
    for c in cards:
        # Titel/Überschrift
        title_el = c.select_one("[class*='NotificationItemVersionTwo_headline']")
        title = title_el.get_text(" ", strip=True) if title_el else ""
        if not title:
            continue

        # Datum + Uhrzeit zusammensetzen
        date_parts = [
            d.get_text(" ", strip=True)
            for d in c.select("[class*='NotificationItemVersionTwo_moddateText']")
        ]
        timestamp = " ".join(date_parts).strip()

        # Linien herausziehen (U/S/M/Bus/Tram)
        m = re.search(r"(U\d+|S\d+|M\d+|Bus\s*\d+|Tram\s*\d+)", title)
        lines = m.group(0) if m else None

        # Eindeutige ID inkl. Zeitstempel
        key = (title + (lines or "") + timestamp).encode("utf-8")
        _id = "BVG-" + hashlib.sha1(key).hexdigest()

        # Content Hash nur auf Basis des Titels
        content_hash = hashlib.sha1(title.encode("utf-8")).hexdigest()

        items.append({
            "id": _id,
            "source": "BVG",
            "title": title,
            "lines": lines,
            "url": None,
            "content_hash": content_hash,
            "detail": title,
            "timestamp": timestamp
        })

    print("DEBUG BVG: Items extrahiert:", len(items))
    return items

def fetch_all_items():
    html = fetch_html(LIST_URL)
    items = parse_items(html)
    time.sleep(1)
    return items

