import os
import json
import logging
import re
from collections import OrderedDict
from playwright.async_api import async_playwright

SEEN_FILE = "seen.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)

def enrich_message(text: str) -> str:
    mapping = {
        "U-Bahn": ("🚇", "#BVG #UBahn"),
        "S-Bahn": ("🚆", "#SBahnBerlin"),
        "Straßenbahn": ("🚋", "#TramBerlin"),
        "Bus": ("🚌", "#BVG #Bus"),
        "Aufzug": ("🛗", "#Barrierefreiheit"),
        "Störung": ("⚠️", "#Störung"),
        "Baumaßnahme": ("🚧", "#Bauarbeiten"),
        "Verspätung": ("⏱️", "#Verspätung"),
        "Ausfall": ("❌", "#Ausfall"),
        "Schienenersatzverkehr": ("🚍", "#SEV"),
    }

    emojis, hashtags = [], []
    for key, (emoji, hashtag) in mapping.items():
        if re.search(rf"\b{re.escape(key)}\b", text, re.IGNORECASE):
            emojis.append(emoji)
            hashtags.extend(hashtag.split())

    emojis = " ".join(OrderedDict.fromkeys(emojis))
    hashtags = " ".join(OrderedDict.fromkeys(hashtags + ["#Berlin"]))

    return f"{emojis} {hashtags}".strip()

def generate_tweets(meldungen):
    threads = []
    for m in meldungen:
        beschreibung = m.get("beschreibung", "").strip()
        titel = m.get("titel") or "Störung"
        extras = enrich_message(f"{titel} {beschreibung}")
        prefix = "🚧 BVG:" if m.get("quelle") == "BVG" else "⚠️ S-Bahn:"
        header = f"{prefix} {titel}"

        full_text = f"{header}\n📝 {beschreibung}\n{extras}"

        if len(full_text) <= 280:
            threads.append([full_text])
        else:
            parts = [header]
            beschreibung_chunks = [beschreibung[i:i+240] for i in range(0, len(beschreibung), 240)]
            for chunk in beschreibung_chunks:
                parts.append(f"📝 {chunk.strip()}")
            if extras:
                parts.append(extras)
            threads.append(parts)

    return threads

async def post_threads(threads):
    user = os.getenv("TWITTER_USER")
    pw = os.getenv("TWITTER_PASS")

    if not user or not pw:
        logging.error("❌ Twitter-Credentials fehlen!")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            logging.info("🔐 Starte Login bei X...")
            await page.goto("https://twitter.com/login", timeout=60000)

            await page.fill('input[name="text"]', user)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)

            await page.fill('input[name="password"]', pw)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(7000)

            for thread in threads:
                first = True
                for tweet in thread:
                    await page.click('div[aria-label="Tweet text"]')
                    await page.keyboard.type(tweet)
                    if first:
                        await page.click('div[data-testid="tweetButtonInline"]')
                        first = False
                        await page.wait_for_timeout(3000)
                    else:
                        await page.click('div[data-testid="tweetButton"]')
                        await page.wait_for_timeout(3000)

            logging.info("✅ Alle Tweets gesendet!")
        except Exception as e:
            logging.error(f"❌ Fehler beim Tweeten: {e}")
        finally:
            await browser.close()
