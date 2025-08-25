import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BVG_URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
SBAHN_URL = "https://sbahn.berlin/fahren/bauen-stoerung/"

async def scrape_bvg():
    """BVG-Störungen mit Pagination und Logging abrufen"""
    results = []
    max_pages = 10  # Sicherheitsgrenze
    page_num = 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(BVG_URL, timeout=20000)

            while page_num <= max_pages:
                try:
                    await page.wait_for_selector("li.DisruptionsOverviewVersionTwo_item__GvWfq", timeout=10000)
                    items = await page.query_selector_all("li.DisruptionsOverviewVersionTwo_item__GvWfq")
                    for item in items:
                        text = await item.inner_text()
                        cleaned = text.strip()
                        if cleaned:
                            results.append(cleaned)
                            print(f"🔍 BVG Seite {page_num}: {cleaned}")

                    next_button = await page.query_selector("a[aria-label='Weiter']")
                    if next_button:
                        await next_button.click()
                        await page.wait_for_timeout(2000)
                        page_num += 1
                    else:
                        break
                except PlaywrightTimeoutError:
                    print(f"⚠️ Timeout auf Seite {page_num}, versuche weiter...")
                    break

        except Exception as e:
            print(f"❌ Fehler beim BVG-Scraping: {e}")

        finally:
            await browser.close()

    return results

async def scrape_sbahn():
    """S-Bahn-Störungen mit Logging abrufen"""
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(SBAHN_URL, timeout=20000)
            await page.wait_for_selector("div.c-teaser", timeout=10000)

            items = await page.query_selector_all("div.c-teaser")
            for item in items:
                text = await item.inner_text()
                cleaned = text.strip()
                if cleaned:
                    results.append(cleaned)
                    print(f"🔍 S-Bahn: {cleaned}")

        except PlaywrightTimeoutError:
            print("⚠️ Timeout beim Laden der S-Bahn-Seite.")
        except Exception as e:
            print(f"❌ Fehler beim S-Bahn-Scraping: {e}")

        finally:
            await browser.close()

    return results

async def main():
    print("🚦 Starte BVG-Scraper...")
    bvg_data = await scrape_bvg()
    print(f"✅ BVG-Ergebnisse: {len(bvg_data)} Einträge\n")

    print("🚉 Starte S-Bahn-Scraper...")
    sbahn_data = await scrape_sbahn()
    print(f"✅ S-Bahn-Ergebnisse: {len(sbahn_data)} Einträge\n")

    # Optional: Ergebnisse zusammenführen oder speichern
    all_data = {
        "bvg": bvg_data,
        "sbahn": sbahn_data
    }

    return all_data

if __name__ == "__main__":
    asyncio.run(main())
