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

def extract_detail_text(href):
    if not href:
        return ""
    if not href.startswith("http"):
        href = BASE_URL + href
    try:
        html = fetch_html(href)
        soup = BeautifulSoup(html, "html.parser")
        detail = soup.select_one("main")
        return detail.get_text(" ", strip=True)[:1000] if detail else ""
    except Exception:
        return ""

def extract_lines(text):
    return re.findall(r"S\d{1,2}", text)

def parse_incident(card):
    title_el = card.select_one("h3.o-construction-announcement-title__heading")
    title = title_el.get_text(strip=True) if title_el else ""

    detail_el = card.select("p")
    detail = " ".join(p.get_text(" ", strip=True) for p in detail_el)

    line_el = card.select_one("a.o-icon-css-line")
    line = line_el.get_text(strip=True) if line_el else ""

    if not title or not detail or not line:
        return None

    return {
        "title": title,
        "detail": detail,
        "lines": [line]
    }

def parse_items(html: str):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.c-construction-announcement-body")
    print("DEBUG SBAHN: Gefundene Cards:", len(cards))

    items = []
    for c in cards:
        incident = parse_incident(c)
        if not incident:
            continue

        a = c.find("a", href=True)
        href = a["href"] if a else None

        key = (incident["title"] + (href or "")).encode("utf-8")
        _id = "SBAHN-" + hashlib.sha1(key).hexdigest()
        content_hash = hashlib.sha1(incident["title"].encode("utf-8")).hexdigest()

        detail_text = extract_detail_text(href) if href else ""

        # Convert lines list to string for DB compatibility
        lines_str = ", ".join(incident["lines"]) if isinstance(incident["lines"], list) else incident["lines"]

        items.append({
            "id": _id,
            "source": "SBAHN",
            "title": incident["title"],
            "lines": lines_str,
            "url": href,
            "content_hash": content_hash,
            "detail": detail_text
        })

    print("DEBUG SBAHN: Items extrahiert:", len(items))
    return items

def fetch_all_items():
    html = fetch_html(LIST_URL)
    return parse_items(html)

