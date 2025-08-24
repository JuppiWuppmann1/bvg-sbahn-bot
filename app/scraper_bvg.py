import hashlib
import time
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from .settings import settings

BASE_URL = "https://www.bvg.de"
LIST_URL = f"{BASE_URL}/de/verbindungen/stoerungsmeldungen"

# 🛡️ Robuste Klick-Funktion mit Scroll & Sichtbarkeit
async def safe_click_visible_buttons(page, buttons, retries=3):
    for i, btn in enumerate(buttons):
        try:
            if not await btn.is_visible():
                print(f"⛔️ Button {i+1} ist nicht sichtbar – wird übersprungen.")
                continue

            await btn.scroll_into_view_if_needed()
            await page.evaluate("(el) => el.scrollIntoView({behavior: 'auto', block: 'center'})", btn)

            for attempt in range(retries):
                try:
                    await btn.click(force=True)
                    print(f"✅ Klick auf Button {i+1} erfolgreich.")
                    await asyncio.sleep(0.3)
                    break
                except Exception as e:
                    print(f"⚠️ Versuch {attempt+1} für Button {i+1} fehlgeschlagen: {e}")
                    await asyncio.sleep(0.5 * (attempt + 1))
            else:
                print(f"❌ Button {i+1} konnte nicht geklickt werden – wird übersprungen.")
        except Exception as e:
            print(f"⚠️ Fehler bei Button {i+1}: {e}")

# 🔄 Seitenabruf mit automatischem Scroll
async def fetch_all_pages(base_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 3000})

        all_html = []

        for page_num in range(1, 6):
            url = f"{base_url}?page={page_num}"
            print(f"🔄 Lade Seite {page_num}: {url}")
            await page.goto(url)
            await page.wait_for_selector("li.DisruptionsOverviewVersionTwo_item__GvWfq", timeout=10000)

            # Automatisch scrollen, um alle Buttons sichtbar zu machen
            await page.evaluate("""
                let scrollInterval = setInterval(() => {
                    window.scrollBy(0, 300);
                    if (window.scrollY + window.innerHeight >= document.body.scrollHeight) {
                        clearInterval(scrollInterval);
                    }
                }, 100);
            """)
            await asyncio.sleep(2)

            buttons = await page.query_selector_all('button[aria-expanded="false"]')
            print(f"➡️ Gefundene Detail-Buttons: {len(buttons)}")
            await safe_click_visible_buttons(page, buttons)

            html = await page.content()
            all_html.append(html)

        await browser.close()
        return all_html

# 🧼 Textbereinigung
def clean_detail(text: str) -> str:
    sentences = list(dict.fromkeys(text.split(". ")))
    cleaned = ". ".join(sentences)
    return cleaned[:280]

# 🧠 HTML-Parsing
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

# 🚀 Hauptfunktion zum Abrufen aller Items
async def fetch_all_items():
    html_pages = await fetch_all_pages(LIST_URL)
    time.sleep(1)

    all_items = []
    for html in html_pages:
        items = parse_items(html)
        all_items.extend(items)

    return all_items
