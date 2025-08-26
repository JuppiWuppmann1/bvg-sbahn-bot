import logging
import re
from collections import OrderedDict
from playwright.async_api import async_playwright

def parse_bvg_details(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    von, bis, linien, ort, maßnahme = None, "Bis auf weiteres", [], None, None

    for i, line in enumerate(lines):
        if re.match(r"\d{2}\.\d{2}\.\d{4}", line):
            if i > 0 and lines[i - 1].lower().startswith("von"):
                von = f"{line} {lines[i + 1]}" if i + 1 < len(lines) and re.match(r"\d{2}:\d{2}", lines[i + 1]) else line
        elif "bis auf weiteres" in line.lower():
            bis = "Bis auf weiteres"
        elif "haltestelle verlegt" in line.lower():
            maßnahme = "Haltestelle verlegt"
        elif re.match(r"(Bus|M|X)\d+", line):
            linien.append(line)
        elif "straße" in line.lower() or "platz" in line.lower():
            ort = line

    return {
        "von": von,
        "bis": bis,
        "linien": ", ".join(OrderedDict.fromkeys(linien)),
        "maßnahme": maßnahme,
        "ort": ort
    }

async def fetch_bvg():
    url = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
    meldungen = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=60000)
            page_nr = 1
            while True:
                logging.info(f"📡 BVG Seite {page_nr} laden...")
                await page.wait_for_selector("li.DisruptionsOverviewVersionTwo_item__GvWfq", timeout=15000)
                items = await page.query_selector_all("li.DisruptionsOverviewVersionTwo_item__GvWfq")

                for item in items:
                    titel_el = await item.query_selector("h3")
                    titel = await titel_el.inner_text() if titel_el else "Unbekannt"

                    beschreibung_el = await item.query_selector("div.NotificationItemVersionTwo_content__kw1Ui")
                    beschreibung = await beschreibung_el.inner_text() if beschreibung_el else ""

                    details = parse_bvg_details(beschreibung)

                    meldung = {
                        "quelle": "BVG",
                        "titel": titel.strip(),
                        "beschreibung": beschreibung.strip(),
                        "details": details
                    }

                    logging.info(f"📍 BVG-Meldung: {meldung['titel']} | Details: {details}")
                    meldungen.append(meldung)

                next_button = await page.query_selector("a[aria-label='Nächste Seite']")
                if next_button and await next_button.is_enabled():
                    await next_button.click()
                    await page.wait_for_timeout(2000)
                    page_nr += 1
                else:
                    break
        except Exception as e:
            logging.error(f"❌ Fehler beim BVG-Scraping: {e}")
        finally:
            await browser.close()

    logging.info(f"✅ {len(meldungen)} Meldungen von BVG")
    return meldungen
