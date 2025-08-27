import subprocess
import logging

def install_playwright_browser():
    try:
        logging.info("🛠️ Installiere Playwright-Browser...")
        subprocess.run(["python", "-m", "playwright", "install", "chromium"], check=True)
        logging.info("✅ Playwright-Browser erfolgreich installiert.")
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Fehler bei der Playwright-Installation: {e}")
