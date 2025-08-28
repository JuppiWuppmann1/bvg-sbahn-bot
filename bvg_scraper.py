import asyncio
from fastapi import FastAPI, Response
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from pathlib import Path
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DEBUG_FILE = Path("bvg_live_debug.html")

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

        html = await page.content()
        DEBUG_FILE.write_text(html, encoding="utf-8")  # 💾 HTML speichern

        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq")

        logging.info(f"📦 Gefundene Meldungen: {len(items)}")
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

        await browser.close()
    return meldungen

@app.get("/debug/bvg")
def get_bvg_debug():
    if DEBUG_FILE.exists():
        html = DEBUG_FILE.read_text(encoding="utf-8")
        return Response(content=html, media_type="text/html")
    return {"error": "Keine Debug-Datei gefunden."}

@app.get("/run-bvg")
async def run_bvg_scraper():
    try:
        await scrape_bvg()
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"❌ Fehler beim BVG-Scraper: {e}")
        return {"status": "error", "message": str(e)}
