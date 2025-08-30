import requests
from bs4 import BeautifulSoup

URL = "https://sbahn.berlin/fahren/bauen-stoerung/"

def scrape_sbahn_constructions():
    res = requests.get(URL)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    results = []

    # Alle Meldungen finden
    for con in soup.select("div.c-construction-announcement"):
        try:
            lines = con.get("data-lines", "").split(",")
            title = con.select_one("h3.o-construction-announcement-title__heading").get_text(strip=True)
            timespan = con.select_one("div.o-timespan__center").get_text(strip=True)
            
            # Detail-Text
            detail_block = con.select_one("div.c-construction-announcement-details ul")
            details = " ".join(li.get_text(" ", strip=True) for li in detail_block.select("li")) if detail_block else ""

            results.append({
                "lines": [l.upper() for l in lines if l],
                "title": title,
                "timespan": timespan,
                "details": details
            })
        except Exception as e:
            print("Fehler beim Parsen einer Meldung:", e)

    return results


if __name__ == "__main__":
    meldungen = scrape_sbahn_constructions()
    for m in meldungen:
        print("🚆 Linien:", ", ".join(m["lines"]))
        print("📌 Titel:", m["title"])
        print("🕒 Zeitraum:", m["timespan"])
        print("ℹ️ Details:", m["details"])
        print("-" * 50)
