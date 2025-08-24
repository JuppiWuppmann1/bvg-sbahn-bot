import hashlib
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

BASE_URL = "https://sbahn.berlin"
LIST_URL = f"{BASE_URL}/fahren/bauen-stoerung/"

# Wörter, die klar auf Störung hindeuten
STOERUNG_KEYWORDS = [
    "störung", "einschränkung", "unterbrechung", "ausfall",
    "signalstörung", "polizeieinsatz", "weichenstörung", "takt geändert",
]

# Wörter, die auf reine Baumaßnahme/Info deuten (ausschließen)
BAU_EXCLUDES = [
    "baumaßnahme", "bauarbeiten", "bauinfos", "fahrplanänderungen",
]

async def fetch_rendered_html(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 2200})
        await page.goto(url)
        # Seite hat beide Sektionen; Cards erscheinen lazy – kurz warten
        await page.wait_for_selector("div.c-construction-announcement--disorder", timeout=10000)
        await asyncio.sleep(0.4)
        html = await page.content()
        await browser.close()
        return html

def clean_text(t: str) -> str:
    t = " ".join(t.split())
    return (t[:277] + "…") if len(t) > 280 else t

def is_real_disruption(card: BeautifulSoup) -> bool:
    full_text = card.get_text(" ", strip=True).lower()

    if any(bad in full_text for bad in BAU_EXCLUDES):
        return False
    if any(ok in full_text for ok in STOERUNG_KEYWORDS):
        return True

    # Zusatzheuristik: Wenn es Chips/Badges mit "Takt geändert" o. ä. gibt
    badge = card.find(string=lambda s: s and "takt geändert" in s.lower())
    return bool(badge)

def parse_items(html: str):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.c-construction-announcement--disorder")
    print("DEBUG SBAHN: Gefundene Cards:", len(cards))

    items = []
    for c in cards:
        if not is_real_disruption(c):
            continue

        title_el = c.select_one("h3.o-construction-announcement-title__heading")
        title = title_el.get_text(" ", strip=True) if title_el else ""

        # Update-/Zeit-Info
        update_el = c.select_one("p.o-last-update")
        timestamp = update_el.get_text(" ", strip=True) if update_el else ""

        # Linien
        line_els = c.select("a.o-icon-css-line")
        lines = ", ".join(el.get_text(" ", strip=True) for el in line_els) if line_els else ""

        # Detail
        detail_paragraphs = c.select("div.c-construction-announcement-body p")
        detail_raw = " ".join(p.get_text(" ", strip=True) for p in detail_paragraphs)
        detail = clean_text(detail_raw or title)

        if not title:
            continue

        # URL (falls vorhanden)
        a = c.find("a", href=True)
        href = a["href"] if a else None
        if href and not href.startswith("http"):
            href = BASE_URL + href

        # IDs & Hash
        key_id = (title + (lines or "") + (timestamp or "")).encode("utf-8")
        _id = "SBAHN-" + hashlib.sha1(key_id).hexdigest()

        key_hash = (title + detail + (lines or "")).encode("utf-8")
        content_hash = hashlib.sha1(key_hash).hexdigest()

        items.append({
            "id": _id,
            "source": "SBAHN",
            "title": title,
            "lines": lines,
            "url": href,
            "content_hash": content_hash,
            "detail": detail,
            "timestamp": timestamp
        })

    print("DEBUG SBAHN: Items extrahiert:", len(items))
    return items

async def fetch_all_items():
    html = await fetch_rendered_html(LIST_URL)
    return parse_items(html)

