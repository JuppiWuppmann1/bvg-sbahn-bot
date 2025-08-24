import hashlib
import time
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from .settings import settings

BASE_URL = "https://www.bvg.de"
LIST_URL = f"{BASE_URL}/de/verbindungen/stoerungsmeldungen"

# 🔄 Scrollt die Seite vollständig nach unten
async def scroll_page_to_bottom(page, step=300, delay=0.1):
    previous_height = await page.evaluate("() => document.body.scrollHeight")
    while True:
        await page.evaluate(f"window.scrollBy(0, {step})")
        await asyncio.sleep(delay)
        new_height = await page.evaluate("() => document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

# 🧼 Bereinigt Text
def clean_detail(text: str) -> str:
    sentences = list(dict.fromkeys(text.split(". ")))
    cleaned = ". ".join(sentences)
    return cleaned[:280]

# 🧠 Extrahiert Items direkt nach Klick
async def extract_items_from_page(page):
    await page.wait_for_selector("li.DisruptionsOverviewVersionTwo_item__GvWfq", timeout=10000)
    await scroll_page_to_bottom(page)
    await asyncio.sleep(1)

    cards = await page.query_selector_all("li.DisruptionsOverviewVersionTwo_item__GvWfq")
    print(f"🔍 Gefundene Cards: {len(cards)}")

    items = []

    for i, card in enumerate(cards):
        try:
            button = await card.query_selector('button[aria-expanded="false"]')
            if not button:
                print(f"⛔️ Kein Button in Card {i+1}")
                continue

            await button.scroll_into_view_if_needed()
            await button.click(force=True)
            await asyncio.sleep(0.5)

            # Extrahiere Daten direkt aus dem Card-Element
            title_el = await card.query_selector("h3")
            title_text = await title_el.inner_text() if title_el else ""

            line_els = await card.query_selector_all("a._BdsSignetLine_8xinl_2")
            lines = ", ".join([await a.inner_text() for a in line_els]) if line_els else ""

            time_el = await card.query_selector("time")
            timestamp = await time_el.get_attribute("datetime") if time_el else ""

            detail_els = await card.query_selector_all("div.NotificationItemVersionTwo_content__kw1Ui p")
            raw_detail = " ".join([await p.inner_text() for p in detail_els]) if detail_els else title_text
            detail_text = clean_detail(raw_detail)

            key = (title_text + lines + timestamp).encode("utf-8")
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

            print(f"✅ Card {i+1} extrahiert: {title_text}")
        except Exception as e:
            print(f"❌ Fehler bei Card {i+1}: {e}")

    return items

# 🚀 Hauptfunktion
async def fetch_all_items():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 3000})

        all_items = []

        for page_num in range(1, 6):
            url = f"{LIST_URL}?page={page_num}"
            print(f"🔄 Lade Seite {page_num}: {url}")
            await page.goto(url)
            items = await extract_items_from_page(page)
            all_items.extend(items)

        await browser.close()
        return all_items

# 🧪 Testlauf
if __name__ == "__main__":
    items = asyncio.run(fetch_all_items())
    print(f"\n📦 Insgesamt extrahiert: {len(items)} Einträge")
    for item in items[:5]:  # Nur die ersten 5 anzeigen
        print(f"\n📝 {item['detail']}\n📅 {item['timestamp']}\n🔗 Linien: {item['lines']}")
