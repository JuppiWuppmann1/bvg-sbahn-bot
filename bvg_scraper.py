import logging
import httpx
from bs4 import BeautifulSoup

async def scrape_bvg():
    url = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
    logging.info(f"🌐 Lade BVG-Seite: {url}")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Jede Meldung steckt in einem <li>
    items = soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq")
    logging.info(f"📦 {len(items)} BVG-Meldungen gefunden.")

    meldungen = []
    for item in items:
        titel = item.select_one("h4")
        beschreibung = item.select_one(".NotificationItemVersionTwo_content__kw1Ui")
        linie = item.select_one("._BdsSignetLine_8xinl_2")
        von_bis = item.select_one(".LineStopsRange_LineStopsRange__I3I_1")
        von_bis_text = von_bis.get_text(" ", strip=True) if von_bis else ""

        meldungen.append({
            "quelle": "BVG",
            "titel": titel.get_text(strip=True) if titel else "Unbekannt",
            "beschreibung": beschreibung.get_text(" ", strip=True) if beschreibung else "",
            "linie": linie.get_text(strip=True) if linie else "",
            "strecke": von_bis_text,
        })

    logging.info(f"✅ BVG-Scraper hat {len(meldungen)} Meldungen extrahiert.")
    return meldungen
