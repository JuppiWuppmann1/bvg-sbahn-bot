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

        for page_num in range(1, 6):
            if page_num > 1:
                try:
                    # Suche alle Buttons mit Seitenzahlen
                    buttons = await page.locator("button").all()
                    found = False

                    for b in buttons:
                        text = await b.inner_text()
                        if text.strip() == str(page_num):
                            await b.scroll_into_view_if_needed()
                            await b.click()
                            logging.info(f"📄 Seite {page_num} geklickt...")
                            await page.wait_for_timeout(3000)
                            found = True
                            break

                    if not found:
                        logging.info(f"⏭️ Seite {page_num} nicht verfügbar – Button nicht gefunden.")
                        continue

        except Exception as e:
            logging.warning(f"⚠️ Seite {page_num} konnte nicht geladen werden: {e}")
            continue

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq")

            for item in items:
                beschreibung = item.select_one(".NotificationItemVersionTwo_content__kw1Ui p")
                datum = item.select_one("time")

                if beschreibung and datum:
                    meldung = {
                        "zeit": datum.get("datetime"),
                        "beschreibung": beschreibung.get_text(" ", strip=True)
                    }
                    logging.info(f"🕒 {meldung['zeit']}\n📝 {meldung['beschreibung']}\n{'-'*60}")
                    meldungen.append(meldung)

        await browser.close()

    logging.info(f"✅ BVG-Scraper hat insgesamt {len(meldungen)} Meldungen extrahiert.")
    return meldungen

