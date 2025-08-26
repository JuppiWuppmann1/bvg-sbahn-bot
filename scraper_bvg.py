import logging
import re
from collections import OrderedDict
from playwright.async_api import async_playwright

def parse_bvg_details(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    von, bis, linien, ort, maßnahme = None, "Bis auf weiteres", [], None, None

    for i, line in enumerate(lines):
        if re.match(r"^(U-Bahn|Bus)?\s?[MXU]?\d{1,3}$", line):
            linien.append(line)

        if "Störung" in line or "Unterbrechung" in line:
            maßnahme = "Störung/Unterbrechung"
        elif "Ersatzverkehr" in line:
            maßnahme = "Ersatzverkehr"
        elif "Pendelverkehr" in line:
            maßnahme = "Pendelverkehr"
        elif "Aufzugsstörung" in line:
            maßnahme = "Aufzugsstörung"
        elif "Haltestelle verlegt" in line:
            maßnahme = "Haltestelle verlegt"

        if "platz" in line.lower() or "straße" in line.lower() or "str." in line.lower() or "bahnhof" in line.lower():
            ort = line

        if i > 0 and lines[i - 1].lower().startswith("von"):
            if re.match(r"\d{2}\.\d{2}\.\d{4}", line):
                von = line
                if i + 1 < len(lines) and re.match(r"\d{2}:\d{2}", lines[i + 1]):
                    von += f" {lines[i + 1]}"
        if i > 0 and lines[i - 1].lower().startswith("bis"):
            if re.match(r"\d{2}\.\d{2}\.\d{4}", line):
                bis = line
                if i + 1 < len(lines) and re.match(r"\d{2}:\d{2}", lines[i + 1]):
                    bis += f" {lines[i + 1]}"
            elif "bis auf weiteres" in line.lower():
                bis = "Bis auf weiteres"

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

                    beschreibung_parts = await item.query_selector_all("div.NotificationItemVersionTwo_content__kw1Ui p")
                    beschreibung = " ".join([await part.inner_text() for part in beschreibung_parts]) if beschreibung_parts else ""

                    datum_el = await item.query_selector("time")
                    aktualisiert_am = await datum_el.get_attribute("datetime") if datum_el else None

                    details = parse_bvg_details(beschreibung)

                    meldung = {
                        "quelle": "BVG",
                        "titel": titel.strip(),
                        "beschreibung": beschreibung.strip(),
                        "details": details,
                        "aktualisiert_am": aktualisiert_am
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
