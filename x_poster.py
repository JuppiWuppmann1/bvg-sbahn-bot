import logging
import json
import subprocess
from pathlib import Path

COOKIES_FILE = Path("x_cookies.json")

def post_threads(threads):
    try:
        payload = json.dumps(threads)
        result = subprocess.run(
            ["node", "x_bridge.js"],
            input=payload,
            text=True,
            capture_output=True,
            check=True
        )
        logging.info("✅ Threads erfolgreich über Puppeteer gepostet.")
        if result.stdout:
            logging.debug(f"📤 Puppeteer-Ausgabe:\n{result.stdout}")
        if result.stderr:
            logging.debug(f"⚠️ Puppeteer-Warnungen:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Fehler beim Puppeteer-Posten: {e}")
        if e.stdout:
            logging.error(f"📤 STDOUT:\n{e.stdout}")
        if e.stderr:
            logging.error(f"📥 STDERR:\n{e.stderr}")

