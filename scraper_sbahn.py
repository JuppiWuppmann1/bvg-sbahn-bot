import requests
from bs4 import BeautifulSoup
import logging
import hashlib
import json
import os

BASE_URL = "https://sbahn.berlin/fahren/bauen-stoerung/"
STORAGE_FILE = "disruptions_sbahn.json"

def generate_disruption_id(description: str, date: str) -> str:
    raw = f"{description}-{date}"
    return hashlib.md5(raw.encode()).hexdigest()

def load_previous_disruptions():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r") as f:
            return json.load(f)
    return []

def save_current_disruptions(ids):
    with open(STORAGE_FILE, "w") as f:
        json.dump(ids, f)

def scrape_sbahn_disruptions():
    disruptions = []

    resp = requests.get(BASE_URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    items = soup.find_all("li", class_="smc-tile")

    for li in items:
        try:
            # Zeitraum
            date = li.find("time").get_text(strip=True) if li.find("time") else ""

            # Beschreibung
            details_block = li.find("div", class_="c-construction-announcement-details")
            description = details_block.get_text(" ", strip=True) if details_block else li.get_text(" ", strip=True)

            disruption_id = generate_disruption_id(description, date)

            disruptions.append({
                "id": disruption_id,
                "date": date,
                "description": description,
            })
        except Exception as e:
            logging.warning(f"⚠️ Fehler beim Parsen eines S-Bahn-Items: {e}")
            continue

    return disruptions

async def run_sbahn_scraper(send_func):
    try:
        current = scrape_sbahn_disruptions()
        current_ids = [d["id"] for d in current]
        previous_ids = load_previous_disruptions()

        new_ids = set(current_ids) - set(previous_ids)
        ended_ids = set(previous_ids) - set(current_ids)

        # Neue Störungen posten
        for d in current:
            if d["id"] in new_ids:
                msg = (
                    f"🚆 **Neue S-Bahn-Störung**\n"
                    f"📅 Zeitraum: {d['date']}\n"
                    f"ℹ️ {d['description'][:300]}..."
                )
                await send_func(msg)

        # Beendete Störungen melden
        for old_id in ended_ids:
            await send_func(f"✅ S-Bahn-Störung behoben (ID: `{old_id}`)")

        save_current_disruptions(current_ids)
        return [d for d in current if d["id"] in new_ids]
    except Exception as e:
        logging.error(f"❌ Fehler im S-Bahn-Scraper: {e}")
        return []
