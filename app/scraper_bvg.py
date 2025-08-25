import hashlib
from datetime import datetime
from playwright.async_api import async_playwright
from .storage import Incident

URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"

async def fetch_all_items():
    items = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, timeout=30000)

        await page.wait_for_selector("div.m-stoerungsmeldung", timeout=15000)
        cards = await page.query_selector_all("div.m-stoerungsmeldung")

        for card in cards:
            title = (await card.query_selector("h3")).inner_text() if await card.query_selector("h3") else ""
            detail = (await card.query_selector("p")).inner_text() if await card.query_selector("p") else ""
            lines = (await card.query_selector(".m-stoerungsmeldung__linien")).inner_text() if await card.query_selector(".m-stoerungsmeldung__linien") else ""
            url = await card.get_attribute("data-href") or URL

            raw = f"{title}|{detail}|{lines}"
            content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

            incident = Incident(
                id=f"BVG-{content_hash[:12]}",
                source="BVG",
                title=title.strip(),
                detail=detail.strip(),
                lines=lines.strip(),
                url=url,
                content_hash=content_hash,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
            )
            items.append(incident)

        await browser.close()
    return items
