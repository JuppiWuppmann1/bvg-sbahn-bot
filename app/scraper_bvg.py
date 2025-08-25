import asyncio
from playwright.async_api import async_playwright

URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"

async def fetch_all_items():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()

        print(f"🔄 Lade Seite: {URL}")
        await page.goto(URL, timeout=60000)

        try:
            # Warte auf neue Struktur
            await page.wait_for_selector("li.DisruptionsOverviewVersionTwo_item__GvWfq", timeout=30000)
        except Exception as e:
            print("⚠️ BVG-Seite geladen, aber Selektor nicht gefunden.")
            html = await page.content()
            print("📄 HTML-Dump (erste 2000 Zeichen):\n")
            print(html[:2000])
            await browser.close()
            raise e

        # Alle Meldungen holen
        elements = await page.query_selector_all("li.DisruptionsOverviewVersionTwo_item__GvWfq")
        print(f"✅ Gefundene Meldungen: {len(elements)}")

        items = []
        for el in elements:
            try:
                # Titel (Linie oder Hauptüberschrift)
                title_el = await el.query_selector("h3")
                title = await title_el.inner_text() if title_el else "Unbekannte Störung"

                # Kategorie (z. B. Aufzugsstörung, Signalstörung …)
                tag_el = await el.query_selector("span.NotificationItemVersionTwo_tagsItem__GBFLi strong")
                tag = await tag_el.inner_text() if tag_el else ""

                # Beschreibung
                detail_el = await el.query_selector("div.NotificationItemVersionTwo_content__kw1Ui")
                detail = await detail_el.inner_text() if detail_el else ""

                items.append({
                    "title": f"{tag} - {title}".strip(),
                    "source": "BVG",
                    "detail": detail.strip()
                })
            except Exception as inner_e:
                print("⚠️ Fehler beim Parsen eines Elements:", inner_e)

        await browser.close()
        return items

# Debug-Run
if __name__ == "__main__":
    asyncio.run(fetch_all_items())
