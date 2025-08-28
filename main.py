import asyncio
import logging
import subprocess
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bvg_scraper import scrape_bvg
from sbahn_scraper import scrape_sbahn
from utils import load_seen, save_seen, generate_tweets
from x_poster import post_threads

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI()
scheduler = AsyncIOScheduler()
seen = load_seen()

# 🛠️ Playwright-Browserinstallation
def install_playwright_browser():
    try:
        logging.info("🛠️ Installiere Playwright-Browser...")
        subprocess.run(["python", "-m", "playwright", "install", "chromium"], check=True)
        logging.info("✅ Playwright-Browser erfolgreich installiert.")
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Fehler bei der Playwright-Installation: {e}")

# 🔄 Hauptjob für Scraping & Posting
async def job():
    global seen
    logging.info("🔎 Starte neuen Check...")

    bvg_meldungen = await scrape_bvg()
    sbahn_meldungen = await scrape_sbahn()
    alle = bvg_meldungen + sbahn_meldungen

    neue = []
    for m in alle:
        key = f"{m.get('quelle')}|{m.get('titel')}|{m.get('beschreibung')}"
        if key not in seen:
            seen[key] = True
            neue.append(m)

    if neue:
        logging.info(f"✅ {len(neue)} neue Meldungen gefunden!")
        threads = generate_tweets(neue)
        post_threads(threads)
        save_seen(seen)
    else:
        logging.info("ℹ️ Keine neuen Meldungen.")

# 🚀 Startup-Event: Browser installieren & Scheduler starten
@app.on_event("startup")
async def startup_event():
    install_playwright_browser()
    scheduler.add_job(job, "interval", minutes=5)
    scheduler.start()
    logging.info("⏰ Scheduler gestartet (alle 5 Minuten)")

# 🧪 Manuelles Auslösen via Endpoint
@app.get("/run")
async def run_once():
    try:
        logging.info("🚀 /run endpoint aufgerufen")
        await job()
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"❌ Fehler in /run: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
