import logging
from playwright.sync_api import sync_playwright
from utils import generate_tweets

import os

logger = logging.getLogger(__name__)

TWITTER_USER = os.getenv("TWITTER_USER")
TWITTER_PASS = os.getenv("TWITTER_PASS")

def post_update(meldungen):
    """Postet eine oder mehrere Meldungen (Thread) auf X/Twitter"""
    threads = generate_tweets(meldungen if isinstance(meldungen, list) else [meldungen])

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        logger.info("🌐 Öffne Twitter/X...")
        page.goto("https://x.com/login", timeout=60000)

        # Login
        page.fill("input[name='text']", TWITTER_USER)
        page.keyboard.press("Enter")
        page.wait_for_selector("input[name='password']", timeout=30000)
        page.fill("input[name='password']", TWITTER_PASS)
        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)

        for parts in threads:
            prev_tweet_url = None
            for idx, text in enumerate(parts):
                page.goto(prev_tweet_url or "https://x.com/compose/tweet", timeout=60000)

                logger.info(f"✍️ Sende Tweet ({idx+1}/{len(parts)}): {text[:50]}...")
                page.wait_for_selector("div[aria-label='Tweet text']", timeout=30000)
                page.fill("div[aria-label='Tweet text']", text)

                page.click("div[data-testid='tweetButtonInline']")
                page.wait_for_timeout(5000)

                # Nach dem ersten Tweet holen wir die URL, um den Thread fortzusetzen
                if idx == 0:
                    page.goto("https://x.com/home", timeout=60000)
                    page.wait_for_selector("article", timeout=30000)
                    first_tweet = page.query_selector("article a[href*='/status/']")
                    if first_tweet:
                        prev_tweet_url = "https://x.com" + first_tweet.get_attribute("href")

        browser.close()
