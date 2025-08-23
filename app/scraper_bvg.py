import hashlib, time
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

def clean_detail(text: str) -> str:
    # Entferne doppelte Sätze und kürze auf 280 Zeichen
    sentences = list(dict.fromkeys(text.split(". ")))
    cleaned = ". ".join(sentences)
    return cleaned[:280]

def parse_items(html: str):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("li:has(h4):has(p)")
    print("DEBUG BVG: Gefundene Cards:", len(cards))

    items = []
    for c in cards:
        title = c.select_one("h4")
        title_text = title.get_text(strip=True) if title else ""

        line = c.select_one("a")
        lines = line.get_text(strip=True) if line else None

        time_el = c.select_one("time")
        timestamp = time_el.get_text(strip=True) if time_el else ""

        detail_el = c.select_one("p") or c.select_one("div")
        raw_detail = detail_el.get_text(strip=True) if detail_el else title_text
        detail_text = clean_detail(raw_detail)

        if not title_text:
            continue

        key = (title_text + (lines or "") + timestamp).encode("utf-8")
        _id = "BVG-" + hashlib.sha1(key).hexdigest()
        content_hash = hashlib.sha1(title_text.encode("utf-8")).hexdigest()

        items.append({
            "id": _id,
            "source": "BVG",
            "title": title_text,
            "lines": lines,
            "url": None,
            "content_hash": content_hash,
            "detail": detail_text,
            "timestamp": timestamp
        })

    print(f"DEBUG BVG: Items extrahiert: {len(items)}")
    return items

def fetch_all_items():
    html = fetch_html(LIST_URL)
    items = parse_items(html)
    time.sleep(1)
    return items
