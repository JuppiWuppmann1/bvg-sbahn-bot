import requests
from bs4 import BeautifulSoup
import logging

BASE_URL = "https://sbahn.berlin/fahren/bauen-stoerung/"


def scrape_sbahn_disruptions():
    disruptions = []

    resp = requests.get(BASE_URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    items = soup.find_all("li", class_="smc-tile")

    for li in items:
        try:
            title = li.find("h3").get_text(" ", strip=True) if li.find("h3") else "Unbekannt"
            subtitle = li.find("p").get_text(" ", strip=True) if li.find("p") else ""
            date = li.find("time").get_text(" ", strip=True) if li.find("time") else ""
            details = li.get_text(" ", strip=True)

            disruptions.append({
                "title": title,
                "subtitle": subtitle,
                "date": date,
                "details": details,
            })
        except Exception:
            continue

    return disruptions


async def run_sbahn_scraper():
    try:
        disruptions = scrape_sbahn_disruptions()
        if disruptions:
            messages = [
                f"🚆 **S-Bahn-Störung**\n"
                f"🔹 {d['title']} ({d['date']})\n"
                f"ℹ️ {d['subtitle']}\n"
                f"📄 {d['details'][:300]}..."
                for d in disruptions
            ]
            return messages
        return []
    except Exception as e:
        logging.error(f"❌ Fehler im S-Bahn-Scraper: {e}")
        return []
