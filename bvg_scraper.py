from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging

async def scrape_bvg():
    url = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
    logging.info(f"🌐 Lade BVG-Seite mit Playwright: {url}")
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(3000)  # Warte auf JS-Inhalte

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        items = soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq")
        logging.info(f"📦 {len(items)} BVG-Meldungen gefunden.")

        for item in items:
            beschreibung = item.select_one(".NotificationItemVersionTwo_content__kw1Ui p")
            linien = item.select(".NotificationItemVersionTwo_signetContainer__zqGlg ._BdsSignetLine_8xinl_2")
            von_bis = item.select_one(".LineStopsRange_LineStopsRange__I3I_1")
            datum = item.select_one("time")

            linien_text = ", ".join([l.get_text(strip=True) for l in linien]) if linien else ""
            von_bis_text = von_bis.get_text(" ", strip=True) if von_bis else ""
            beschreibung_text = beschreibung.get_text(" ", strip=True) if beschreibung else ""
            datum_text = datum.get("datetime") if datum else ""

            meldungen.append({
                "quelle": "BVG",
                "titel": f"Störung auf {linien_text}" if linien_text else "Unbekannte Linie",
                "beschreibung": beschreibung_text,
                "linie": linien_text,
                "strecke": von_bis_text,
                "zeit": datum_text
            })

        await browser.close()

    logging.info(f"✅ BVG-Scraper hat {len(meldungen)} Meldungen extrahiert.")
    return meldungen
