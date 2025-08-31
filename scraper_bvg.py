import requests
from bs4 import BeautifulSoup
import logging
import hashlib
import json
import os

BASE_URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
STORAGE_FILE = "disruptions_bvg.json"

def generate_disruption_id(description: str, start: str, end: str) -> str:
    raw = f"{description}-{start}-{end}"
    return hashlib.md5(raw.encode()).hexdigest()

def load_previous_disruptions():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r") as f:
            return json.load(f)
    return []

def save_current_disruptions(ids):
    with open(STORAGE_FILE, "w") as f:
        json.dump(ids, f)

def scrape_bvg_disruptions(max_pages=3):
    disruptions = []

    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}?page={page}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.find_all("li", class_="DisruptionsOverviewVersionTwo_item__GvWfq")

        for li in items:
            try:
                # Zeitraum
                time_blocks = li.find_all("time")
                start = time_blocks[0].get_text(strip=True) if len(time_blocks) > 0 else ""
                end = time_blocks[1].get_text(strip=True) if len(time_blocks) > 1 else "Bis auf weiteres"

                # Beschreibung
                description_tag = li.find("div", class_="NotificationItemVersionTwo_contentWrapper___O2nB")
                description = description_tag.get_text(" ", strip=True) if description_tag else ""

                disruption_id = generate_disruption_id(description, start, end)

                disruptions.append({
                    "id": disruption_id,
                    "start": start,
                    "end": end,
                    "description": description,
                })
            except Exception as e:
                logging.warning(f"⚠️ Fehler beim Parsen eines BVG-Items: {e}")
                continue

    return disruptions

async def run_bvg_scraper(send_func):
    try:
        current = scrape_bvg_disruptions()
        current_ids = [d["id"] for d in current]
        previous_ids = load_previous_disruptions()

        new_ids = set(current_ids) - set(previous_ids)
        ended_ids = set(previous_ids) - set(current_ids)

        # Neue Störungen posten
        for d in current:
            if d["id"] in new_ids:
                msg = (
                    f"🚇 **Neue BVG-Störung**\n"
                    f"📅 Zeitraum: {d['start']} – {d['end']}\n"
                    f"ℹ️ {d['description'][:300]}..."
                )
                await send_func(msg)

        # Beendete Störungen melden
        for old_id in ended_ids:
            await send_func(f"✅ BVG-Störung behoben (ID: `{old_id}`)")

        save_current_disruptions(current_ids)
        return [d for d in current if d["id"] in new_ids]
    except Exception as e:
        logging.error(f"❌ Fehler im BVG-Scraper: {e}")
        return []
