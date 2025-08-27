import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"

async def scrape_bvg():
    meldungen = []
    async with httpx.AsyncClient() as client:
        for page in range(1, 4):  # z.B. 3 Seiten durchgehen
            url = f"{BASE_URL}?p_p_id=101&p_p_lifecycle=0&p_p_state=maximized&p_p_mode=view&_101_delta=50&_101_cur={page}"
            r = await client.get(url, timeout=30)
            soup = BeautifulSoup(r.text, "html.parser")

            for item in soup.select("li.NotificationItemVersionTwo"):
                titel = item.select_one("h3")
                beschreibung = item.select_one("span.NotificationItemVersionTwo_content__kw1Ui")
                meldungen.append({
                    "quelle": "BVG",
                    "titel": titel.get_text(strip=True) if titel else "",
                    "beschreibung": beschreibung.get_text(" ", strip=True) if beschreibung else "",
                })
    return meldungen

