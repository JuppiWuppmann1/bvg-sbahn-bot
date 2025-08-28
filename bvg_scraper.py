import logging
import re
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen?p_p_id=101&p_p_lifecycle=0&p_p_state=maximized&p_p_mode=view&_101_delta=50&_101_cur={page}"

async def scrape_bvg():
    meldungen = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for page_num in range(1, 6):
            url = BASE_URL.format(page=page_num)
            logging.info(f"🌐 Lade BVG Seite {page_num}: {url}")

            try:
                r = await client.get(url)
                if r.status_code != 200:
                    logging.warning(f"⚠️ Fehler beim Laden von Seite {page_num}: {r.status_code}")
                    continue

                soup = BeautifulSoup(r.text, "html.parser")

                items = soup.select("li.DisruptionsOverviewVersionTwo_item__GvWfq")
                if not items:
                    logging.info(f"ℹ️ Keine Meldungen auf Seite {page_num}. Stoppe.")
                    break

                for item in items:
                    titel_tag = item.select_one("h3")
                    beschreibung_tag = item.select_one("span.NotificationItemVersionTwo_content__kw1Ui p")

                    titel_raw = titel_tag.get_text(" ", strip=True) if titel_tag else ""
                    beschreibung_raw = beschreibung_tag.get_text(" ", strip=True) if beschreibung_tag else ""

                    # Bereinigung
                    titel = re.sub(r"\b(\w+)\1\b", r"\1", titel_raw)
                    beschreibung_raw = re.sub(r"(Ausführliche Informationen|Bauvideo|schließen)+", "", beschreibung_raw, flags=re.IGNORECASE)
                    beschreibung_raw = re.sub(r"\s{2,}", " ", beschreibung_raw).strip()

                    beschreibung_parts = re.split(r'(?<=[.!?])\s+', beschreibung_raw)
                    beschreibung = "\n".join(beschreibung_parts)

                    logging.info(f"🚇 Vollständige Meldung:\nTitel: {titel}\nBeschreibung:\n{beschreibung}\n{'-'*60}")

                    meldungen.append({
                        "quelle": "BVG",
                        "titel": titel,
                        "beschreibung": beschreibung
                    })

            except Exception as e:
                logging.error(f"❌ Fehler beim BVG-Scraping (Seite {page_num}): {e}")

    logging.info(f"✅ BVG-Scraper hat {len(meldungen)} Meldungen gefunden.")
    return meldungen
