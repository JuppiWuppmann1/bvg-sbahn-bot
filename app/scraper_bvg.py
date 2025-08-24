import asyncio
from playwright.async_api import async_playwright

EXCLUDE_KEYWORDS = [
    "aufzug", "fahrtreppe", "bauinfos", "wieso wird gebaut", "fahrplanänderung"
]

async def fetch_all_items():
    url = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen?page=1"
    items = []

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=20000)

            try:
                await page.wait_for_selector("div.m-stoerungsmeldung", timeout=15000)
            except Exception:
                print("❌ BVG: Keine Störungsmeldungen-Elemente gefunden (Timeout).")
                await browser.close()
                return []

            cards = await page.query_selector_all("div.m-stoerungsmeldung")
            for card in cards:
                title = (await card.inner_text()).strip()
                if any(word in title.lower() for word in EXCLUDE_KEYWORDS):
                    continue
                items.append({
                    "id": hash(title),
                    "source": "BVG",
                    "title": title,
                    "detail": title,
                    "content_hash": str(hash(title))
                })

            await browser.close()

    except Exception as e:
        print("❌ Fehler beim BVG-Scraping:", e)

    return items
