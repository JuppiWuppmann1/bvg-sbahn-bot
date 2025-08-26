import os
import logging
import re
import hashlib
from collections import OrderedDict
from playwright.async_api import async_playwright

posted_hashes = set()

def hash_meldung(meldung: dict) -> str:
    basis = f"{meldung.get('quelle')}|{meldung.get('titel')}|{meldung.get('beschreibung')}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()

def is_new(meldung: dict) -> bool:
    return hash_meldung(meldung) not in posted_hashes

def mark_as_posted(meldung: dict):
    posted_hashes.add(hash_meldung(meldung))

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
        context = await browser.new_context()
        page = await context.new_page()

        try:
            logging.info("🔐 Starte Login bei X...")
            await page.goto("https://x.com/i/flow/login", timeout=60000)

            await page.wait_for_selector('input', timeout=15000)
            inputs = await page.query_selector_all('input')
            for inp in inputs:
                placeholder = await inp.get_attribute("placeholder")
                if placeholder and "Telefonnummer" in placeholder:
                    await inp.fill(user)
                    await inp.press("Enter")
                    break
            await page.wait_for_timeout(3000)

            await page.wait_for_selector('input[name="password"]', timeout=15000)
            await page.fill('input[name="password"]', pw)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000)

            if await page.query_selector("iframe[src*='captcha']"):
                logging.error("🛑 Captcha erkannt – Login blockiert.")
                return

            await page.goto("https://x.com/compose/tweet", timeout=30000)
            await page.wait_for_selector('div[aria-label="Tweet text"]', timeout=20000)

            for thread in threads:
                first = True
                for tweet in thread:
                    tweet_box = page.locator('div[aria-label="Tweet text"]')
                    await tweet_box.click()
                    await tweet_box.fill(tweet)
                    await page.wait_for_timeout(1000)

                    await page.click('div[data-testid="tweetButtonInline"]')
                    await page.wait_for_timeout(3000)

                    if first:
                        first = False
                    await page.goto("https://x.com/compose/tweet", timeout=30000)
                    await page.wait_for_selector('div[aria-label="Tweet text"]', timeout=20000)

            logging.info("✅ Alle Tweets gesendet!")
        except Exception as e:
            logging.error(f"❌ Fehler beim Tweeten: {e}")
        finally:
            await browser.close()
