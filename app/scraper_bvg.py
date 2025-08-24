import hashlib
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen?page="

def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

async def scrape_once(max_pages: int = 5):
    incidents = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()

        for page_number in range(1, max_pages + 1):
            url = BASE_URL + str(page_number)
            print(f"🔄 Lade Seite {page_number}: {url}")
            try:
                await page.goto(url, timeout=60000)  # bis zu 60s für Seitenaufbau
                await page.wait_for_load_state("networkidle")  # warten bis Netz ruhig
                await page.wait_for_selector("div.m-stoerungsmeldung", timeout=30000)

                cards = await page.query_selector_all("div.m-stoerungsmeldung")
                print(f"🔍 Gefundene Cards: {len(cards)}")

                for idx, card in enumerate(cards, start=1):
                    try:
                        title_el = await card.query_selector("h3")
                        detail_el = await card.query_selector("div.m-richtext")

                        title = (await title_el.inner_text()) if title_el else "Ohne Titel"
                        detail = (await detail_el.inner_text()) if detail_el else ""

                        content = f"{title} {detail}"
                        content_hash = hash_content(content)

                        incidents.append({
                            "id": content_hash,
                            "source": "BVG",
                            "title": title.strip(),
                            "detail": detail.strip(),
                            "url": url,
                            "status": "active",
                            "first_seen": datetime.utcnow(),
                            "last_seen": datetime.utcnow(),
                            "content_hash": content_hash,
                        })

                    except Exception as e:
                        print(f"❌ Fehler bei Card {idx}: {e}")

            except Exception as e:
                print(f"❌ Fehler beim Laden von Seite {page_number}: {e}")

        await browser.close()

    return incidents


# Debug/Test: Direktes Ausführen
if __name__ == "__main__":
    results = asyncio.run(scrape_once(max_pages=1))
    print(f"✅ Gefundene Einträge: {len(results)}")
    for r in results[:3]:
        print(r)

