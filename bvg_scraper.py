import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

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
                    found = False
                    pagination = await page.query_selector("nav[aria-label='Pagination']")
                    if pagination:
                        buttons = await pagination.query_selector_all("button, a")
                        for b in buttons:
                            try:
                                text = await b.inner_text()
                                if text.strip() == str(page_num):
                                    await b.scroll_into_view_if_needed()
                                    await b.click()
                                    logging.info(f"📄 Seite {page_num} geklickt...")
                                    await page.wait_for_timeout(3000)
                                    found = True
                                    break
                            except Exception as inner:
                                logging.debug(f"🔍 Button-Fehler: {inner}")
                                continue
                    if not found:
                        logging.info(f"⏭️ Seite {page_num} nicht verfügbar – Paginierungs-Button nicht klickbar.")
                        await page.screenshot(path=f"page_{page_num}_missing_button.png")
                        continue
                except Exception as e:
                    logging.warning(f"⚠️ Seite {page_num} konnte nicht geladen werden: {e}")
                    continue

            try:
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                items = soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq")

                if page_num == 1:
                    Path("bvg_debug.html").write_text(html, encoding="utf-8")
                    await page.screenshot(path="bvg_debug_screenshot.png")
                    logging.info("📸 Screenshot und HTML von Seite 1 gespeichert.")
                    pagination = await page.query_selector("nav[aria-label='Pagination']")
                    if pagination:
                        buttons = await pagination.query_selector_all("button, a")
                        for i, b in enumerate(buttons):
                            try:
                                text = await b.inner_text()
                                logging.info(f"🔘 Button {i+1}: '{text.strip()}'")
                            except Exception as e:
                                logging.warning(f"⚠️ Fehler beim Lesen von Button {i+1}: {e}")
                    else:
                        logging.warning("⚠️ Keine Paginierung gefunden.")
                    logging.info(f"📦 Gefundene Meldungen: {len(items)}")
                    for i, item in enumerate(items[:5], 1):
                        beschreibung = item.select_one(".NotificationItemVersionTwo_content__kw1Ui p")
                        datum = item.select_one("time")
                        logging.info(f"📝 Meldung {i}:")
                        logging.info(f"    Zeit: {datum.get('datetime') if datum else '–'}")
                        logging.info(f"    Text: {beschreibung.get_text(strip=True) if beschreibung else '–'}")

                for item in items:
                    beschreibung = item.select_one(".NotificationItemVersionTwo_content__kw1Ui p")
                    datum = item.select_one("time")
                    linien = [a.get_text(strip=True) for a in item.select("a._BdsSignetLine_8xinl_2")]
                    haltestelle = item.select_one(".NotificationItemVersionTwo_lineStopsRange__SdZDd")
                    typ = item.select_one(".NotificationItemVersionTwo_tagsItem__GBFLi strong")

                    if beschreibung and datum:
                        meldung = {
                            "zeit": datum.get("datetime"),
                            "beschreibung": beschreibung.get_text(" ", strip=True),
                            "linien": ", ".join(linien),
                            "haltestelle": haltestelle.get_text(strip=True) if haltestelle else None,
                            "typ": typ.get_text(strip=True) if typ else None,
                            "quelle": "BVG"
                        }
                        logging.info(f"🕒 {meldung['zeit']}\n📝 {meldung['beschreibung']}\n🚏 {meldung['haltestelle']}\n🚍 {meldung['linien']}\n🏷️ {meldung['typ']}\n{'-'*60}")
                        meldungen.append(meldung)
            except Exception as e:
                logging.error(f"❌ Fehler beim Parsen der Seite {page_num}: {e}")

        await browser.close()

    logging.info(f"✅ BVG-Scraper hat insgesamt {len(meldungen)} Meldungen extrahiert.")
    return meldungen

if __name__ == "__main__":
    asyncio.run(scrape_bvg())
