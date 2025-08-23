import hashlib
import time
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
    cards = soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq")
    print("DEBUG BVG: Gefundene Cards:", len(cards))

    items = []
    for c in cards:
        try:
            title_el = c.select_one("h3")
            title_text = title_el.get_text(strip=True) if title_el else ""

            line_links = c.select("a._BdsSignetLine_8xinl_2")
            lines = ", ".join([a.get_text(strip=True) for a in line_links]) if line_links else None

            time_tags = c.select("time")
            timestamp = time_tags[0].get("datetime") if time_tags else ""

            detail_paragraphs = c.select("div.NotificationItemVersionTwo_content__kw1Ui p")
            raw_detail = " ".join(p.get_text(strip=True) for p in detail_paragraphs) if detail_paragraphs else title_text
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
        except Exception as e:
            print(f"⚠️ Fehler beim Parsen eines Eintrags: {e}")

    print(f"DEBUG BVG: Items extrahiert: {len(items)}")
    return items

def fetch_all_items():
    html = fetch_html(LIST_URL)
    items = parse_items(html)
    time.sleep(1)
    return items

