import hashlib
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from .settings import settings

BASE_URL = "https://www.bvg.de"
LIST_URL = f"{BASE_URL}/de/verbindungen/stoerungsmeldungen"

async def fetch_rendered_html(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector("li.DisruptionsOverviewVersionTwo_item__GvWfq", timeout=10000)

        # Alle Buttons mit aria-expanded="false" klicken
        buttons = await page.query_selector_all('button[aria-expanded="false"]')
        for btn in buttons:
            try:
                await btn.click()
                await page.wait_for_timeout(300)  # Warte kurz auf DOM-Update
            except Exception as e:
                print(f"⚠️ Fehler beim Klick auf Button: {e}")

        html = await page.content()
        await browser.close()
        return html

def clean_detail(text: str) -> str:
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

async def fetch_all_items():
    html = await fetch_rendered_html(LIST_URL)
    time.sleep(1)
    return parse_items(html)
