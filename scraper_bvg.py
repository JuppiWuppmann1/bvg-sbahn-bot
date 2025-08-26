import asyncio
import logging
from playwright.async_api import async_playwright

async def fetch_bvg():
    url = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)

        page_nr = 1
        while True:
            logging.info(f"📡 BVG Seite {page_nr} laden...")
            await page.wait_for_selector("div.m-stoerungsmeldung", timeout=15000)
            items = await page.query_selector_all("div.m-stoerungsmeldung")

            for item in items:
                titel = (await item.query_selector("h3")).inner_text() if await item.query_selector("h3") else "Unbekannt"
                beschreibung = (await item.inner_text()) or ""
                meldungen.append({
                    "quelle": "BVG",
                    "titel": titel.strip(),
                    "beschreibung": beschreibung.strip(),
                })

            # Nächste Seite?
            next_button = await page.query_selector("a[aria-label='Nächste Seite']")
            if next_button and await next_button.is_enabled():
                await next_button.click()
                await page.wait_for_timeout(2000)
                page_nr += 1
            else:
                break

        await browser.close()

    return meldungen
