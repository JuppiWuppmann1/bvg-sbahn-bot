import os
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

USERNAME = os.getenv("TWITTER_USERNAME")
PASSWORD = os.getenv("TWITTER_PASSWORD")


def post_thread(messages):
    """
    Postet eine Liste von Nachrichten als Thread auf Twitter/X.
    """
    if not USERNAME or not PASSWORD:
        raise ValueError("❌ TWITTER_USERNAME und TWITTER_PASSWORD müssen gesetzt sein!")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        logger.info("🌐 Rufe Twitter Login auf...")
        page.goto("https://x.com/i/flow/login", timeout=60000)

        page.fill('input[name="text"]', USERNAME)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)

        page.fill('input[name="password"]', PASSWORD)
        page.keyboard.press("Enter")

        page.wait_for_selector('div[aria-label="Tweet text"]', timeout=60000)

        for i, msg in enumerate(messages):
            logger.info(f"✍️ Schreibe Tweet {i+1}/{len(messages)}...")
            textarea = page.locator('div[aria-label="Tweet text"]')
            textarea.fill(msg)

            if i == len(messages) - 1:
                page.click('div[data-testid="tweetButtonInline"]')
            else:
                page.click('div[data-testid="tweetButtonInline"]')
                page.wait_for_timeout(3000)

        logger.info("✅ Thread erfolgreich gesendet")

        context.close()
        browser.close()
