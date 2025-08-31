import logging
import hashlib
import json
import os
from playwright.async_api import async_playwright

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

async def scrape_bvg_disruptions(max_pages=3):
    disruptions = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path="/opt/render/.cache/ms-playwright/chromium-1187/chrome-linux/chrome")
        page = await browser.new_page()

        for page_num in range(1, max_pages + 1):
            await page.goto(f"{BASE_URL}?page={page_num}", timeout=60000)
            await page.wait_for_selector("li.DisruptionsOverviewVersionTwo_item__GvWfq", timeout=10000)

            items = await page.query_selector_all("li.DisruptionsOverviewVersionTwo_item__GvWfq")
            for item in items:
                try:
                    time_tags = await item.query_selector_all("time")
                    start = await time_tags[0].inner_text() if len(time_tags) > 0 else ""
                    end = await time_tags[1].inner_text() if len(time_tags) > 1 else "Bis auf weiteres"

                    description_block = await item.query_selector("div.NotificationItemVersionTwo_contentWrapper___O2nB")
                    description = await description_block.inner_text() if description_block else await item.inner_text()

                    disruption_id = generate_disruption_id(description.strip(), start.strip(), end.strip())

                    disruptions.append({
                        "id": disruption_id,
                        "start": start.strip(),
                        "end": end.strip(),
                        "description": description.strip(),
                    })
                except Exception as e:
                    logging.warning(f"⚠️ Fehler beim Parsen eines BVG-Items: {e}")
                    continue

        await browser.close()
    return disruptions

async def run_bvg_scraper(send_func):
    try:
        current = await scrape_bvg_disruptions()
        current_ids = [d["id"] for d in current]
        previous_ids = load_previous_disruptions()

        new_ids = set(current_ids) - set(previous_ids)
        ended_ids = set(previous_ids) - set(current_ids)

        for d in current:
            if d["id"] in new_ids:
                msg = (
                    f"🚇 **Neue BVG-Störung**\n"
                    f"📅 Zeitraum: {d['start']} – {d['end']}\n"
                    f"ℹ️ {d['description'][:300]}..."
                )
                await send_func(msg)

        for old_id in ended_ids:
            await send_func(f"✅ BVG-Störung behoben (ID: `{old_id}`)")

        save_current_disruptions(current_ids)
        return [d for d in current if d["id"] in new_ids]
    except Exception as e:
        logging.error(f"❌ Fehler im BVG-Scraper: {e}")
        return []
