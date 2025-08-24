import asyncio
from playwright.async_api import async_playwright

EXCLUDE_KEYWORDS = [
    "aufzug", "fahrtreppe", "bauinfos", "wieso wird gebaut", "fahrplanänderung"
]

async def fetch_all_items():
    url = "https://sbahn.berlin/fahren/bauen-stoerung/"  # ggf. richtige URL anpassen
    items = []

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=20000)

            try:
                await page.wait_for_selector("div.stoerungsmeldung, article, li", timeout=15000)
            except Exception:
                print("❌ S-Bahn: Keine Störungsmeldungen-Elemente gefunden (Timeout).")
                await browser.close()
                return []

            cards = await page.query_selector_all("div.stoerungsmeldung, article, li")
            for card in cards:
                title = (await card.inner_text()).strip()
                if any(word in title.lower() for word in EXCLUDE_KEYWORDS):
                    continue
                items.append({
                    "id": hash(title),
                    "source": "SBAHN",
                    "title": title,
                    "detail": title,
                    "content_hash": str(hash(title))
                })

            await browser.close()

    except Exception as e:
        print("❌ Fehler beim S-Bahn-Scraping:", e)

    return items

    print("✅ Gesamt extrahierte SBAHN-Items:", len(items))
    return items
