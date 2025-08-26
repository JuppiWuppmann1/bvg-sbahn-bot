import os
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

TWITTER_USER = os.getenv("TWITTER_USER")
TWITTER_PASS = os.getenv("TWITTER_PASS")

def split_message(msg, limit=280):
    """Teilt Nachrichten in mehrere Tweets (Thread)"""
    parts = []
    while len(msg) > limit:
        cut = msg.rfind(" ", 0, limit)
        if cut == -1:
            cut = limit
        parts.append(msg[:cut])
        msg = msg[cut:].lstrip()
    parts.append(msg)
    return parts

def find_tweet_box(page):
    """Sucht Tweet-Eingabefeld robust"""
    selectors = [
        'div[aria-label="Tweet text"]',
        'div[aria-label="Post text"]',
        'div[aria-label="Beitragstext"]',
        'div[aria-label="Posten"]',
        'div[role="textbox"]'
    ]
    for sel in selectors:
        try:
            return page.wait_for_selector(sel, timeout=5000)
        except:
            continue
    raise Exception("Tweet-Box nicht gefunden!")

def login(page):
    logger.info("🔑 Login bei Twitter/X")
    page.goto("https://x.com/login", timeout=60000)
    page.fill('input[name="text"]', TWITTER_USER)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)

    page.fill('input[name="password"]', TWITTER_PASS)
    page.keyboard.press("Enter")
    page.wait_for_timeout(5000)

def post_update(msg):
    """Postet Meldungen, automatisch als Thread wenn nötig"""
    parts = split_message(msg)

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        try:
            login(page)

            for i, part in enumerate(parts):
                tweet_box = find_tweet_box(page)
                tweet_box.fill(part)

                page.click('div[data-testid="tweetButtonInline"]')
                page.wait_for_timeout(4000)

                if i == 0:
                    logger.info("✅ Erster Tweet gesendet")
                else:
                    logger.info(f"↪️ Thread-Tweet #{i} gesendet")

            browser.close()
        except Exception as e:
            logger.error(f"❌ Fehler beim Tweeten: {e}")
            browser.close()

