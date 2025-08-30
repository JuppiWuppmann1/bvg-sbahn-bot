import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.bvg.de/de/verbindungen/stoerungsmeldungen"


def scrape_bvg_disruptions(max_pages=5):
    disruptions = []

    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}?page={page}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.find_all("li", class_="DisruptionsOverviewVersionTwo_item__GvWfq")

        for li in items:
            try:
                title = li.find("h3").get_text(" ", strip=True)
                type_tag = li.find("strong").get_text(" ", strip=True) if li.find("strong") else "Unbekannt"
                date_blocks = li.find_all("time")
                start, end = "", ""
                if len(date_blocks) >= 1:
                    start = date_blocks[0].get_text(" ", strip=True)
                if len(date_blocks) >= 2:
                    end = date_blocks[1].get_text(" ", strip=True)
                details = li.get_text(" ", strip=True)

                disruptions.append({
                    "title": title,
                    "type": type_tag,
                    "start": start,
                    "end": end,
                    "details": details,
                })
            except Exception:
                continue

    return disruptions
