import asyncio
from playwright.async_api import async_playwright

URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"

async def fetch_all_items():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()

        print(f"🔄 Lade Seite: {URL}")
        await page.goto(URL, timeout=60000)  # 60s Ladezeit, falls Render langsam ist

        try:
            # Warte auf BVG-Meldungen
            await page.wait_for_selector("div.m-stoerungsmeldung", timeout=30000)
        except Exception as e:
            print("⚠️ BVG-Seite geladen, aber Selektor nicht gefunden.")
            html = await page.content()
            print("📄 HTML-Dump (erste 2000 Zeichen):\n")
            print(html[:2000])  # nur ein Ausschnitt für Logs
            await browser.close()
            raise e

        # Alle Meldungen sammeln
        elements = await page.query_selector_all("div.m-stoerungsmeldung")
        print(f"✅ Gefundene Meldungen: {len(elements)}")

        items = []
        for el in elements:
            title = (await el.inner_text())[:280].strip()
            items.append({
                "title": title,
                "source": "BVG",
                "detail": title,
            })

        await browser.close()
        return items

# Debug-Run
if __name__ == "__main__":
    asyncio.run(fetch_all_items())

