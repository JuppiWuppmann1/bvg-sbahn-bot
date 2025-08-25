import asyncio
from playwright.async_api import async_playwright

BVG_URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
SBAHN_URL = "https://sbahn.berlin/fahren/bauen-stoerung/"

async def scrape_bvg():
    """BVG-Störungen abrufen"""
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(BVG_URL)
        await page.wait_for_selector("li.DisruptionsOverviewVersionTwo_item__GvWfq")

        items = await page.query_selector_all("li.DisruptionsOverviewVersionTwo_item__GvWfq")
        for item in items:
            text = await item.inner_text()
            results.append(text.strip())

        await browser.close()
    return results

async def scrape_sbahn():
    """S-Bahn-Störungen abrufen"""
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(SBAHN_URL)
        await page.wait_for_selector("div.c-teaser")

        items = await page.query_selector_all("div.c-teaser")
        for item in items:
            text = await item.inner_text()
            results.append(text.strip())

        await browser.close()
    return results
