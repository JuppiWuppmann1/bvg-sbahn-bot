import asyncio
import uuid
from playwright.async_api import async_playwright

async def scrape_bvg():
    url = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"
    items = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"📡 Lade Daten von BVG...")
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("li.DisruptionsOverviewVersionTwo_item__GvWfq", timeout=15000)

        elements = await page.query_selector_all("li.DisruptionsOverviewVersionTwo_item__GvWfq")
        print(f"✅ Gefundene Meldungen: {len(elements)}")

        for el in elements:
            # Titel (Linie + Station)
            title_el = await el.query_selector("h3")
            title = await title_el.inner_text() if title_el else "Unbekannt"

            # Tag (z. B. 'Aufzugsstörung')
            tag_el = await el.query_selector("strong")
            tag = await tag_el.inner_text() if tag_el else ""

            # Detailtext
            detail_el = await el.query_selector("div.NotificationItemVersionTwo_contentWrapper___O2nB")
            detail = await detail_el.inner_text() if detail_el else ""

            items.append({
                "id": str(uuid.uuid4()),  # eindeutige ID erzeugen
                "title": f"{tag} - {title}".strip(),
                "source": "BVG",
                "detail": detail.strip()
            })

        await browser.close()

    print(f"✅ {len(items)} Einträge geladen von BVG")
    return items


if __name__ == "__main__":
    result = asyncio.run(scrape_bvg())
    for item in result[:5]:
        print(item)
