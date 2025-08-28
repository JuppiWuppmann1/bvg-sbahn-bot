from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging

async def scrape_bvg():
    url = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0.0.0 Safari/537.36",
            locale="de-DE",
            viewport={"width": 1280, "height": 800},
            device_scale_factor=1,
            timezone_id="Europe/Berlin"
        )
        page = await context.new_page()
        page.set_default_timeout(60000)

        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(3000)

        for page_num in range(1, 6):
            if page_num > 1:
                try:
                    await page.wait_for_timeout(2000)
                    elements = await page.locator("button, a").all()
                    found = False

                    for el in elements:
                        try:
                            if not await el.is_visible():
                                continue
                            text = await el.inner_text()
                            if text.strip() == str(page_num):
                                await el.scroll_into_view_if_needed()
                                await el.click()
                                logging.info(f"📄 Seite {page_num} geklickt...")
                                await page.wait_for_timeout(3000)
                                found = True
                                break
                        except Exception as inner:
                            logging.debug(f"🔍 Button-Check Fehler: {inner}")
                            continue

                    if not found:
                        logging.info(f"⏭️ Seite {page_num} nicht verfügbar – Button nicht gefunden.")
                        continue

                except Exception as e:
                    logging.warning(f"⚠️ Seite {page_num} konnte nicht geladen werden: {e}")
                    continue

            try:
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

            except Exception as e:
                logging.error(f"❌ Fehler beim Parsen der Seite {page_num}: {e}")

        await browser.close()

    logging.info(f"✅ BVG-Scraper hat insgesamt {len(meldungen)} Meldungen extrahiert.")
    return meldungen
