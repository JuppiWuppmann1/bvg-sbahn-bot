import hashlib, re
import requests
from bs4 import BeautifulSoup
from .settings import settings

URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"

def fetch_html():
    r = requests.get(URL, headers={"User-Agent": settings.USER_AGENT}, timeout=20)
    r.raise_for_status()
    return r.text

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
        items.append({
            "id": _id, "source": "BVG",
            "title": title, "lines": lines,
            "url": href, "content_hash": content_hash
        })
    return items
