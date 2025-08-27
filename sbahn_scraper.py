import httpx
from bs4 import BeautifulSoup

URL = "https://sbahn.berlin/fahren/bauen-stoerung/"

async def scrape_sbahn():
    meldungen = []
    async with httpx.AsyncClient() as client:
        r = await client.get(URL, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")

        for item in soup.select("div.teaser"):
            titel = item.select_one("h3")
            beschreibung = item.select_one("p")
            meldungen.append({
                "quelle": "S-Bahn",
                "titel": titel.get_text(strip=True) if titel else "",
                "beschreibung": beschreibung.get_text(" ", strip=True) if beschreibung else "",
            })
    return meldungen
