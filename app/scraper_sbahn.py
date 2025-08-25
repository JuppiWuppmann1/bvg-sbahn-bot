import hashlib
from datetime import datetime
from playwright.async_api import async_playwright
from .storage import Incident

URL = "https://sbahn.berlin/fahren/bauen-stoerung/"

async def fetch_all_items():
    items = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, timeout=30000)

        # Warten bis Karten vorhanden sind
        await page.wait_for_selector("div.c-construction-announcement--disorder", timeout=15000)

        cards = await page.query_selector_all("div.c-construction-announcement--disorder")
        for card in cards:
            title = (await card.query_selector("h3.o-construction-announcement-title__heading"))
            title_text = await title.inner_text() if title else "(ohne Titel)"

            detail = (
                await card.query_selector("div.c-construction-announcement-body")
             )
            detail_text = await detail.inner_text() if detail else ""

            # Linien extrahieren
            line_els = await card.query_selector_all("a.o-icon-css-line")
            lines = ", ".join([await el.inner_text() for el in line_els])

            raw = f"{title_text}|{detail_text}|{lines}"
            content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

            incident = Incident(
                id=f"SBAHN-{content_hash[:12]}",
                source="SBAHN",
                title=title_text.strip(),
                detail=detail_text.strip(),
                lines=lines,
                url=URL,
                content_hash=content_hash,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
            )
            items.append(incident)

        await browser.close()
    return items
