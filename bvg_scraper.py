from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging

async def scrape_bvg():
    url = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(3000)

        for page_num in range(1, 6):  # Seiten 1 bis 5
            logging.info(f"📄 Lade Seite {page_num}...")

            if page_num > 1:
                try:
                    await page.evaluate(f"""
                        [...document.querySelectorAll('button')].find(b => b.textContent.trim() === '{page_num}')?.click()
                    """)
                    await page.wait_for_timeout(3000)
                except Exception as e:
                    logging.warning(f"⚠️ Seite {page_num} konnte nicht per JS geklickt werden: {e}")
                    continue

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq")
            logging.info(f"📦 Seite {page_num}: {len(items)} Meldungen gefunden.")

            for item in items:
                beschreibung = item.select_one(".NotificationItemVersionTwo_content__kw1Ui p")
                datum = item.select_one("time")

                beschreibung_text = beschreibung.get_text(" ", strip=True) if beschreibung else ""
                datum_text = datum.get("datetime") if datum else ""

                meldung = {
                    "zeit": datum_text,
                    "beschreibung": beschreibung_text
                }

                logging.info(f"🕒 {meldung['zeit']}\n📝 {meldung['beschreibung']}\n{'-'*60}")
                meldungen.append(meldung)

        await browser.close()

    logging.info(f"✅ BVG-Scraper hat insgesamt {len(meldungen)} Meldungen extrahiert.")
    return meldungen
