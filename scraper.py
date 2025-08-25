import asyncio
import re
from playwright.async_api import async_playwright

BVG_URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
SBAHN_URL = "https://sbahn.berlin/fahren/bauen-stoerung/"

async def scrape_bvg():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(BVG_URL, timeout=20000)
            await page.wait_for_selector('li[class^="DisruptionsOverviewVersionTwo_item__"]', timeout=10000)
            items = await page.query_selector_all('li[class^="DisruptionsOverviewVersionTwo_item__"]')

            for item in items:
                try:
                    text = await item.inner_text()
                    von = re.search(r"Von\s+(\d{2}\.\d{2}\.\d{4})", text)
                    bis = re.search(r"Bis\s+(\d{2}\.\d{2}\.\d{4}|Bis auf weiteres)", text)
                    art = re.search(r"(Ersatzverkehr|Aufzugsstörung|Umleitung|Kein Halt|Unterbrechung|Haltestelle verlegt)", text)

                    von_str = von.group(1) if von else None
                    bis_str = bis.group(1) if bis else None
                    art_str = art.group(1) if art else "Unbekannt"

                    detail_el = await item.query_selector('div[class*="NotificationItemVersionTwo_content__"]')
                    detail = await detail_el.inner_text() if detail_el else "Keine Details"

                    if von_str and bis_str and detail:
                        results.append({
                            "von": von_str,
                            "bis": bis_str,
                            "art": art_str,
                            "beschreibung": detail.strip()
                        })
                        print(f"✅ BVG: {art_str} | {von_str} → {bis_str}\n📝 {detail.strip()[:100]}...\n")

                except Exception as e:
                    print(f"⚠️ Fehler beim BVG-Eintrag: {e}")
        except Exception as e:
            print(f"❌ Fehler beim BVG-Scraping: {e}")
        finally:
            await browser.close()
    return results

async def scrape_sbahn():
    results = []
    seen = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(SBAHN_URL, timeout=20000)
            await page.wait_for_selector("div.c-construction-announcement", timeout=10000)
            items = await page.query_selector_all("div.c-construction-announcement")

            for item in items:
                try:
                    lines = await item.get_attribute("data-lines")
                    lines_list = lines.split(",") if lines else []

                    title_el = await item.query_selector("h3.o-construction-announcement-title__heading")
                    title = await title_el.inner_text() if title_el else "Kein Titel"

                    time_el = await item.query_selector("div.o-timespan__center.o-timespan__cp")
                    time_text = await time_el.inner_text() if time_el else "Kein Zeitraum"

                    detail_el = await item.query_selector("div.c-construction-announcement-details")
                    detail_text = await detail_el.inner_text() if detail_el else "Keine Beschreibung"

                    key = f"{title.strip()}|{time_text.strip()}"
                    if key in seen:
                        continue
                    seen.add(key)

                    results.append({
                        "linien": lines_list,
                        "titel": title.strip(),
                        "zeitraum": time_text.strip(),
                        "beschreibung": detail_text.strip()
                    })
                    print(f"✅ S-Bahn: {title.strip()} ({', '.join(lines_list)})\n🕒 {time_text.strip()}\n📝 {detail_text.strip()[:100]}...\n")

                except Exception as e:
                    print(f"⚠️ Fehler beim S-Bahn-Eintrag: {e}")
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

    tweet_candidates = [
        *[entry for entry in bvg_data if entry.get("beschreibung")],
        *[entry for entry in sbahn_data if entry.get("beschreibung") and entry.get("zeitraum")]
    ]
    print(f"🐦 Tweetbare Meldungen: {len(tweet_candidates)}\n")

    return {
        "bvg": bvg_data,
        "sbahn": sbahn_data,
        "tweets": tweet_candidates
    }

if __name__ == "__main__":
    asyncio.run(main())
