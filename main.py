import subprocess
import os
from fastapi import FastAPI
from scraper import scrape_bvg, scrape_sbahn
from nebenbot import twitter_login_and_tweet
from utils import generate_tweets
from db import is_new_message, save_message, init_db, reset_db_if_monday
import logging
import asyncio

# 🔧 Playwright-Browser installieren, falls sie fehlen
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/tmp/playwright"
try:
    print("🔄 Playwright-Browser werden installiert...")
    subprocess.run(["playwright", "install"], check=True)
    print("✅ Installation erfolgreich.")
except Exception as e:
    print(f"❌ Fehler bei playwright install: {e}")

# Logger Setup
logger = logging.getLogger("bvg-sbahn-bot")
logging.basicConfig(level=logging.INFO)

# Datenbank initialisieren
init_db()
reset_db_if_monday()

app = FastAPI(title="BVG & S-Bahn Bot")

@app.get("/")
def home():
    return {"status": "running"}

@app.get("/update")
async def update():
    logger.info("🔄 Update gestartet")

    # Asynchrone Scraper ausführen
    bvg_msgs = await scrape_bvg()
    sbahn_msgs = await scrape_sbahn()

    all_msgs = bvg_msgs + sbahn_msgs
    threads = generate_tweets(all_msgs)

    posted = 0
    for thread in threads:
        # Prüfe nur den ersten Tweet auf Duplikat
        if is_new_message(thread[0]):
            save_message(thread[0])
            await twitter_login_and_tweet(thread)
            posted += 1
        else:
            logger.info("⏭️ Thread bereits bekannt, wird übersprungen.")

    return {"posted": posted, "total_scraped": len(all_msgs)}
