import hashlib, re, time
import requests
from bs4 import BeautifulSoup
from .settings import settings

BASE_URL = "https://sbahn.berlin"
LIST_URL = f"{BASE_URL}/fahren/bauen-stoerung/"
HEADERS = {"User-Agent": settings.USER_AGENT}

def fetch_html(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

def clean_detail(text: str) -> str:
    # Entferne doppelte Sätze und kürze auf 280 Zeichen
    sentences = list(dict.fromkeys(text.split(". ")))
    cleaned = ". ".join(sentences)
    return cleaned[:280]

def parse_incident(card):
    title_el = card.select_one("h3.o-construction-announcement-title__heading")
    title = title_el.get_text(strip=True) if title_el else ""

    update_el = card.select_one("p.o-last-update")
    update = update_el.get_text(strip=True) if update_el else ""

    line_els = card.select("a.o-icon-css-line")
    lines = [el.get_text(strip=True) for el in line_els]

    detail_paragraphs = card.select("div.c-construction-announcement-body p")
    detail = " ".join(p.get_text(" ", strip=True) for p in detail_paragraphs)

    if not title or not detail or not lines:
        return None

    return {
        "title": title,
        "detail": clean_detail(detail),
        "lines": lines,
        "last_update": update
    }

def parse_items(html: str):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.c-construction-announcement--disorder")
    print("DEBUG SBAHN: Gefundene Cards:", len(cards))

    items = []
    for c in cards:
        incident = parse_incident(c)
        if not incident:
            continue

        a = c.find("a", href=True)
        href = a["href"] if a else None
        if href and not href.startswith("http"):
            href = BASE_URL + href

        key = (incident["title"] + (href or "")).encode("utf-8")
        _id = "SBAHN-" + hashlib.sha1(key).hexdigest()
        content_hash = hashlib.sha1(incident["title"].encode("utf-8")).hexdigest()

        lines_str = ", ".join(incident["lines"])

        items.append({
            "id": _id,
            "source": "SBAHN",
            "title": incident["title"],
            "lines": lines_str,
            "url": href,
            "content_hash": content_hash,
            "detail": incident["detail"],
            "timestamp": incident["last_update"]
        })

    print("DEBUG SBAHN: Items extrahiert:", len(items))
    return items

def fetch_all_items():
    html = fetch_html(LIST_URL)
    time.sleep(1)
    return parse_items(html)
