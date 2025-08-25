import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BVG_URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
SBAHN_URL = "https://sbahn.berlin/fahren/bauen-stoerung/"

async def scrape_bvg():
    """BVG-Störungen mit Detailabruf bei Zeitangabe"""
    results = []
    max_pages = 10
    page_num = 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(BVG_URL, timeout=20000)

            while page_num <= max_pages:
                await page.wait_for_selector("li.DisruptionsOverviewVersionTwo_item__GvWfq", timeout=10000)
                items = await page.query_selector_all("li.DisruptionsOverviewVersionTwo_item__GvWfq")

                for item in items:
                    text = await item.inner_text()
                    if "Von" in text and "Bis" in text:
                        von = re.search(r"Von\s+(\d{2}\.\d{2}\.\d{4}\s*\d{2}:\d{2})", text)
                        bis = re.search(r"Bis\s+(\d{2}\.\d{2}\.\d{4}\s*\d{2}:\d{2}|Bis auf weiteres)", text)
                        art = re.search(r"(Ersatzverkehr|Aufzugsstörung|Umleitung|Kein Halt|Unterbrechung|Haltestelle verlegt)", text)

                        von_str = von.group(1) if von else None
                        bis_str = bis.group(1) if bis else None
                        art_str = art.group(1) if art else "Unbekannt"

                        try:
                            await item.click()
                            await page.wait_for_selector("div.DisruptionDetailVersionTwo_content__", timeout=5000)
                            detail = await page.inner_text("div.DisruptionDetailVersionTwo_content__")
                            results.append({
                                "von": von_str,
                                "bis": bis_str,
                                "art": art_str,
                                "beschreibung": detail.strip()
                            })
                            print(f"✅ BVG: {art_str} | {von_str} → {bis_str}\n📝 {detail.strip()[:100]}...")
                            await page.go_back()
                            await page.wait_for_timeout(1000)
                        except Exception as e:
                            print(f"⚠️ Fehler beim Detailabruf: {e}")
                            await page.go_back()
                            await page.wait_for_timeout(1000)

                next_button = await page.query_selector("a[aria-label='Weiter']")
                if next_button:
                    await next_button.click()
                    await page.wait_for_timeout(2000)
                    page_num += 1
                else:
                    break

        except Exception as e:
            print(f"❌ Fehler beim BVG-Scraping: {e}")
        finally:
            await browser.close()

    return results

async def scrape_sbahn():
    """S-Bahn-Störungen aus Detailmodulen extrahieren"""
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(SBAHN_URL, timeout=20000)
            await page.wait_for_selector("div.c-construction-announcement", timeout=10000)
            items = await page.query_selector_all("div.c-construction-announcement")

            for item in items:
                try:
                    # Linien
                    lines = await item.get_attribute("data-lines")
                    lines_list = lines.split(",") if lines else []

                    # Titel
                    title_el = await item.query_selector("h3.o-construction-announcement-title__heading")
                    title = await title_el.inner_text() if title_el else "Kein Titel"

                    # Zeitraum
                    time_el = await item.query_selector("div.o-timespan__center.o-timespan__cp")
                    time_text = await time_el.inner_text() if time_el else "Kein Zeitraum"

                    # Beschreibung
                    detail_el = await item.query_selector("div.c-construction-announcement-details")
                    detail_text = await detail_el.inner_text() if detail_el else "Keine Details"

                    results.append({
                        "linien": lines_list,
                        "titel": title.strip(),
                        "zeitraum": time_text.strip(),
                        "beschreibung": detail_text.strip()
                    })

                    print(f"✅ S-Bahn: {title.strip()} ({', '.join(lines_list)})\n🕒 {time_text.strip()}\n📝 {detail_text.strip()[:100]}...\n")

                except Exception as e:
                    print(f"⚠️ Fehler beim S-Bahn-Eintrag: {e}")
                    continue

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

    return {
        "bvg": bvg_data,
        "sbahn": sbahn_data
    }

if __name__ == "__main__":
    asyncio.run(main())

