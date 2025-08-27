import logging
import httpx
from bs4 import BeautifulSoup

async def scrape_bvg():
    url = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
    meldungen = []

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; BVG-Scraper/1.0; +https://bvg-sbahn-bot.onrender.com)"
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for item in soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq"):
            titel_tag = item.select_one("h3")
            beschreibung_tag = item.select_one("div.NotificationItemVersionTwo_content__kw1Ui p")

            titel = titel_tag.get_text(strip=True) if titel_tag else ""
            beschreibung = beschreibung_tag.get_text(" ", strip=True) if beschreibung_tag else ""

            logging.info(f"📢 Gefunden: {titel} – {beschreibung[:100]}")

            meldungen.append({
                "quelle": "BVG",
                "titel": titel,
                "beschreibung": beschreibung
            })

    logging.info(f"✅ BVG-Scraper hat {len(meldungen)} Meldungen gefunden.")
    return meldungen
