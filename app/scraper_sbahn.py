import hashlib, re, time
import requests
from bs4 import BeautifulSoup
from .settings import settings

BASE_URL = "https://sbahn.berlin"
LIST_URL = f"{BASE_URL}/fahren/bauen-stoerung/"

HEADERS = {
    "User-Agent": settings.USER_AGENT or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                          "(KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


def extract_detail_text(href: str) -> str:
    if not href.startswith("http"):
        href = BASE_URL + href
    try:
        html = fetch_html(href)
        soup = BeautifulSoup(html, "html.parser")
        detail = soup.select_one("main")
        return detail.get_text(" ", strip=True)[:1000] if detail else ""
    except Exception:
        return ""


def parse_items(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # Störungsmeldungen sind auf der Seite in "teasern"
    cards = soup.select("article.m-teaser")  # spezifischer Selektor
    items = []

    for c in cards:
        # Titel
        title_el = c.select_one(".m-teaser__headline, h3, h2")
        title = title_el.get_text(" ", strip=True) if title_el else ""
        if not title:
            continue

        # Link
        a = c.find("a", href=True)
        href = a["href"] if a else None

        # Linien rausziehen (z. B. "S3", "S7")
        m = re.search(r"S\d+", title)
        lines = m.group(0) if m else None

        # Eindeutige ID
        key = (title + (href or "")).encode("utf-8")
        _id = "SBAHN-" + hashlib.sha1(key).hexdigest()

        # Content Hash
        content_hash = hashlib.sha1(title.encode("utf-8")).hexdigest()

        # Detailtext von der Unterseite
        detail_text = extract_detail_text(href) if href else ""

        items.append({
            "id": _id,
            "source": "SBAHN",
            "title": title,
            "lines": lines,
            "url": href,
            "content_hash": content_hash,
            "detail": detail_text
        })

    return items


def fetch_all_items():
    html = fetch_html(LIST_URL)
    items = parse_items(html)
    time.sleep(1)
    return items

