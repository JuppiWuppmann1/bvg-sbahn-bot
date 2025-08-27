import logging
from playwright.async_api import async_playwright

async def fetch_sbahn():
    url = "https://sbahn.berlin/fahren/bauen-stoerung/"
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)

        await page.wait_for_selector("div.c-teaser", timeout=20000)
        items = await page.query_selector_all("div.c-teaser")

        for item in items:
            titel = (await item.query_selector("h3")).inner_text() if await item.query_selector("h3") else "Unbekannt"
            beschreibung = ""
            try:
                desc_node = await item.query_selector("p")
                if desc_node:
                    beschreibung = await desc_node.inner_text()
            except:
                pass

            meldungen.append({
                "quelle": "S-Bahn",
                "titel": titel.strip(),
                "beschreibung": beschreibung.strip(),
            })

        await browser.close()

    return meldungen
