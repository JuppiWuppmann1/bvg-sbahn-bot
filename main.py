import asyncio
import logging
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scraper_bvg import fetch_bvg
from scraper_sbahn import fetch_sbahn
from utils import generate_tweets, post_threads, load_seen, save_seen

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI()
scheduler = AsyncIOScheduler()
seen = load_seen()

@app.get("/")
def root():
    return {"status": "ok", "message": "🚇 BVG / 🚆 S-Bahn Bot aktiv"}

@app.get("/run")
async def run_scraper():
    global seen
    logging.info("🚀 Starte Verarbeitung...")

    meldungen = []

    # BVG
    try:
        bvg = await fetch_bvg()
        logging.info(f"✅ {len(bvg)} Meldungen von BVG")
        meldungen.extend(bvg)
    except Exception as e:
        logging.error(f"❌ Fehler bei BVG: {e}")

    # S-Bahn
    try:
        sbahn = await fetch_sbahn()
        logging.info(f"✅ {len(sbahn)} Meldungen von S-Bahn")
        meldungen.extend(sbahn)
    except Exception as e:
        logging.error(f"❌ Fehler bei S-Bahn: {e}")

    neue = []
    for m in meldungen:
        key = f"{m.get('quelle')}-{m.get('titel')}-{m.get('beschreibung')}"
        if key not in seen:
            seen[key] = True
            neue.append(m)

    logging.info(f"📊 {len(neue)} neue Meldungen erkannt")
    save_seen(seen)

    if not neue:
        return {"status": "done", "meldungen": 0, "threads": 0}

    threads = generate_tweets(neue)
    await post_threads(threads)

    return {"status": "done", "meldungen": len(neue), "threads": len(threads)}

# Scheduler: alle 5 Minuten
@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(run_scraper, "interval", minutes=5)
    scheduler.start()

