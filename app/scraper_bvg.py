import hashlib, re, time
import requests
from bs4 import BeautifulSoup
from .settings import settings

BASE_URL = "https://www.bvg.de"
LIST_URL = f"{BASE_URL}/de/verbindungen/stoerungsmeldungen"

HEADERS = {"User-Agent": settings.USER_AGENT}

def fetch_html(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

def extract_detail_text(href):
    if not href.startswith("http"):
        href = BASE_URL + href
    try:
        html = fetch_html(href)
        soup = BeautifulSoup(html, "html.parser")
        detail = soup.select_one("main")  # oder spezifischer: ".content", ".teaser", etc.
        return detail.get_text(" ", strip=True)[:1000] if detail else ""
    except Exception:
        return ""

def parse_items(html: str):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("[data-cmp-is='teaser'], article, li")
    items = []
    for c in cards:
        title = (c.get_text(" ", strip=True) or "")[:300]
        if not title:
            continue
        a = c.find("a", href=True)
        href = a["href"] if a else None
        m = re.search(r"(U\d+|S\d+|M\d+|Bus\s*\d+|Tram\s*\d+)", title)
        lines = m.group(0) if m else None
        key = (title + (lines or "") + (href or "")).encode("utf-8")
        _id = "BVG-" + hashlib.sha1(key).hexdigest()
        content_hash = hashlib.sha1(title.encode("utf-8")).hexdigest()
        detail_text = extract_detail_text(href) if href else ""
        items.append({
            "id": _id, "source": "BVG",
            "title": title,
            "lines": lines,
            "url": href,
            "content_hash": content_hash,
            "detail": detail_text
        })
    return items

def fetch_all_items():
    all_items = []
    page = 1
    while True:
        url = LIST_URL + f"?page={page}"
        html = fetch_html(url)
        items = parse_items(html)
        if not items:
            break
        all_items.extend(items)
        page += 1
        time.sleep(1)  # höflich bleiben
    return all_items
