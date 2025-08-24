import hashlib
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from .settings import settings

BASE_URL = "https://www.bvg.de"
LIST_URL = f"{BASE_URL}/de/verbindungen/stoerungsmeldungen?page="


async def fetch_rendered_html(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector("div.m-stoerungsmeldung", timeout=10000)
        html = await page.content()
        await browser.close()
        return html


def clean_detail(text: str) -> str:
    sentences = list(dict.fromkeys(text.split(". ")))
    cleaned = ". ".join(sentences)
    return cleaned[:280]


async def parse_incident(card, page):
    # Titel
    title_el = card.select_one("h3")
    title = title_el.get_text(strip=True) if title_el else ""

    # Linien
    line_els = card.select("div.m-stoerungsmeldung__linien span")
    lines = [el.get_text(strip=True) for el in line_els]

    # Versuche Details direkt zu lesen (ohne Klick)
    detail_paragraphs = card.select("div.m-stoerungsmeldung__beschreibung p")
    detail = " ".join(p.get_text(" ", strip=True) for p in detail_paragraphs)

    # Falls leer → Klick versuchen
    if not detail:
        try:
            element_handle = await page.query_selector(f"#{card['id']}")
            if element_handle:
                await element_handle.scroll_into_view_if_needed()
                await element_handle.click()
                await page.wait_for_timeout(500)

                html_after_click = await page.content()
                soup_after_click = BeautifulSoup(html_after_click, "html.parser")
                expanded = soup_after_click.select_one(f"#{card['id']}")
                if expanded:
                    detail_paragraphs = expanded.select("div.m-stoerungsmeldung__beschreibung p")
                    detail = " ".join(p.get_text(" ", strip=True) for p in detail_paragraphs)
        except Exception as e:
            print(f"❌ Klick fehlgeschlagen bei Card {title}: {e}")

    if not title or not detail or not lines:
        return None

    key = (title + "".join(lines)).encode("utf-8")
    _id = "BVG-" + hashlib.sha1(key).hexdigest()
    content_hash = hashlib.sha1((title + detail).encode("utf-8")).hexdigest()

    return {
        "id": _id,
        "source": "BVG",
        "title": title,
        "lines": ", ".join(lines),
        "url": BASE_URL,
        "content_hash": content_hash,
        "detail": clean_detail(detail),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


async def fetch_all_items():
    items = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for page_num in range(1, 6):  # Seiten 1–5
            url = LIST_URL + str(page_num)
            print(f"🔄 Lade Seite {page_num}: {url}")
            await page.goto(url)
            await page.wait_for_selector("div.m-stoerungsmeldung", timeout=10000)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("div.m-stoerungsmeldung")
            print("🔍 Gefundene Cards:", len(cards))

            for idx, c in enumerate(cards, start=1):
                try:
                    incident = await parse_incident(c, page)
                    if incident:
                        items.append(incident)
                except Exception as e:
                    print(f"❌ Fehler bei Card {idx}: {e}")

        await browser.close()
    print("✅ Gesamt extrahierte Items:", len(items))
    return items
