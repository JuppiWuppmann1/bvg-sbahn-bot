import hashlib
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

BASE_URL = "https://www.bvg.de"
LIST_URL = f"{BASE_URL}/de/verbindungen/stoerungsmeldungen"

async def scroll_page_to_bottom(page, step=300, delay=0.1):
    prev = await page.evaluate("() => document.body.scrollHeight")
    while True:
        await page.evaluate(f"window.scrollBy(0, {step})")
        await asyncio.sleep(delay)
        cur = await page.evaluate("() => document.body.scrollHeight")
        if cur == prev:
            break
        prev = cur

def clean_detail(text: str) -> str:
    parts = [p.strip() for p in text.split() if p.strip()]
    s = " ".join(parts)
    return (s[:277] + "…") if len(s) > 280 else s

async def extract_items_from_page(page):
    await page.wait_for_selector("li.DisruptionsOverviewVersionTwo_item__GvWfq", timeout=10000)
    await scroll_page_to_bottom(page)
    await asyncio.sleep(0.5)

    cards = await page.query_selector_all("li.DisruptionsOverviewVersionTwo_item__GvWfq")
    print(f"🔍 BVG Cards: {len(cards)}")

    items = []
    for i, card in enumerate(cards):
        try:
            btn = await card.query_selector('button[aria-expanded="false"]')
            if btn:
                await btn.click(force=True)
                await asyncio.sleep(0.2)

            title_el = await card.query_selector("h3")
            title = await title_el.inner_text() if title_el else ""

            line_els = await card.query_selector_all("a._BdsSignetLine_8xinl_2")
            lines = ", ".join([await a.inner_text() for a in line_els]) if line_els else ""

            time_el = await card.query_selector("time")
            timestamp = await time_el.get_attribute("datetime") if time_el else ""

            # Detail: Absätze zusammenfassen
            detail_els = await card.query_selector_all("div.NotificationItemVersionTwo_content__kw1Ui p")
            raw_detail = " ".join([await p.inner_text() for p in detail_els]) if detail_els else title
            detail = clean_detail(raw_detail)

            key_id = (title + lines + (timestamp or "")).encode("utf-8")
            _id = "BVG-" + hashlib.sha1(key_id).hexdigest()

            key_hash = (title + detail + lines).encode("utf-8")
            content_hash = hashlib.sha1(key_hash).hexdigest()

            items.append({
                "id": _id,
                "source": "BVG",
                "title": title.strip(),
                "lines": lines.strip(),
                "url": None,
                "content_hash": content_hash,
                "detail": detail,
                "timestamp": timestamp
            })
        except Exception as e:
            print(f"❌ BVG Card {i+1}: {e}")

    return items

async def fetch_all_items():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 2400})
        all_items = []
        for num in range(1, 4):
            url = f"{LIST_URL}?page={num}"
            print(f"🔄 BVG Seite {num}: {url}")
            await page.goto(url)
            all_items.extend(await extract_items_from_page(page))
        await browser.close()
        return all_items
