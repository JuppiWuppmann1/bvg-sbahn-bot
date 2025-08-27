from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging

async def scrape_bvg():
    meldungen = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.bvg.de/de/verbindungen/stoerungsmeldungen", timeout=60000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        for item in soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq"):
            titel_tag = item.select_one("h3")
            beschreibung_tag = item.select_one("div.NotificationItemVersionTwo_content__kw1Ui p")

            titel = titel_tag.get_text(strip=True) if titel_tag else ""
            beschreibung = beschreibung_tag.get_text(" ", strip=True) if beschreibung_tag else ""

            logging.info(f"🚇 Vollständige Meldung:\nTitel: {titel}\nBeschreibung:\n{beschreibung}\n{'-'*60}")

            meldungen.append({
                "quelle": "BVG",
                "titel": titel,
                "beschreibung": beschreibung
            })

        await browser.close()
    return meldungen
