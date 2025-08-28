from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging

async def scrape_bvg():
    base_url = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for page_num in range(1, 6):  # Seiten 1 bis 5
            url = f"{base_url}?page={page_num}"
            logging.info(f"🌐 Lade BVG-Seite {page_num}: {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(3000)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq")
            logging.info(f"📦 Seite {page_num}: {len(items)} Meldungen gefunden.")

            for item in items:
                beschreibung = item.select_one(".NotificationItemVersionTwo_content__kw1Ui p")
                linien = item.select(".NotificationItemVersionTwo_signetContainer__zqGlg ._BdsSignetLine_8xinl_2")
                von_bis = item.select_one(".LineStopsRange_LineStopsRange__I3I_1")
                datum = item.select_one("time")

                linien_text = ", ".join([l.get_text(strip=True) for l in linien]) if linien else ""
                von_bis_text = von_bis.get_text(" ", strip=True) if von_bis else ""
                beschreibung_text = beschreibung.get_text(" ", strip=True) if beschreibung else ""
                datum_text = datum.get("datetime") if datum else ""

                meldung = {
                    "quelle": "BVG",
                    "titel": f"Störung auf {linien_text}" if linien_text else "Unbekannte Linie",
                    "beschreibung": beschreibung_text,
                    "linie": linien_text,
                    "strecke": von_bis_text,
                    "zeit": datum_text
                }

                logging.info(f"📝 BVG-Meldung:\nTitel: {meldung['titel']}\nLinie: {meldung['linie']}\nStrecke: {meldung['strecke']}\nZeit: {meldung['zeit']}\nBeschreibung: {meldung['beschreibung']}\n{'-'*80}")
                meldungen.append(meldung)

        await browser.close()

    logging.info(f"✅ BVG-Scraper hat insgesamt {len(meldungen)} Meldungen extrahiert.")
    return meldungen
    
