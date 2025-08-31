import logging
import hashlib
import json
import os
from playwright.async_api import async_playwright

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

async def scrape_sbahn_disruptions():
    disruptions = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path="/opt/render/.cache/ms-playwright/chromium-1187/chrome-linux/chrome")
        page = await browser.new_page()
        await page.goto(BASE_URL, timeout=60000)
        await page.wait_for_selector("li.smc-tile", timeout=10000)

        items = await page.query_selector_all("li.smc-tile")
        for item in items:
            try:
                date_tag = await item.query_selector("time")
                date = await date_tag.inner_text() if date_tag else ""

                details_block = await item.query_selector("div.c-construction-announcement-details")
                description = await details_block.inner_text() if details_block else await item.inner_text()

                disruption_id = generate_disruption_id(description.strip(), date.strip())

                disruptions.append({
                    "id": disruption_id,
                    "date": date.strip(),
                    "description": description.strip(),
                })
            except Exception as e:
                logging.warning(f"⚠️ Fehler beim Parsen eines S-Bahn-Items: {e}")
                continue

        await browser.close()
    return disruptions

async def run_sbahn_scraper(send_func):
    try:
        current = await scrape_sbahn_disruptions()
        current_ids = [d["id"] for d in current]
        previous_ids = load_previous_disruptions()

        new_ids = set(current_ids) - set(previous_ids)
        ended_ids = set(previous_ids) - set(current_ids)

        for d in current:
            if d["id"] in new_ids:
                msg = (
                    f"🚆 **Neue S-Bahn-Störung**\n"
                    f"📅 Zeitraum: {d['date']}\n"
                    f"ℹ️ {d['description'][:300]}..."
                )
                await send_func(msg)

        for old_id in ended_ids:
            await send_func(f"✅ S-Bahn-Störung behoben (ID: `{old_id}`)")

        save_current_disruptions(current_ids)
        return [d for d in current if d["id"] in new_ids]
    except Exception as e:
        logging.error(f"❌ Fehler im S-Bahn-Scraper: {e}")
        return []
