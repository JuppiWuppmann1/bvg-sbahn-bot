import logging
import httpx
from bs4 import BeautifulSoup

async def scrape_bvg():
    url_template = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen/"
    meldungen = []

    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(1, 4):
            url = url_template.format(page)
            r = await client.get(url)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            for item in soup.select("div.teaser"):
                titel = item.select_one("h3")
                beschreibung = item.select_one("p")
                t = titel.get_text(strip=True) if titel else ""
                b = beschreibung.get_text(" ", strip=True) if beschreibung else ""

                # 👉 Debug-Logging
                logging.info(f"📢 Gefunden: {t} – {b[:100]}")

                meldungen.append({
                    "quelle": "BVG",
                    "titel": t,
                    "beschreibung": b
                })

    logging.info(f"✅ BVG-Scraper hat {len(meldungen)} Meldungen gefunden.")
    return meldungen
