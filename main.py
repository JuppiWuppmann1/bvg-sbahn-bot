import asyncio
import logging
from fastapi import FastAPI
from startup import install_playwright

asyncio.run(install_playwright())

from scraper_bvg import fetch_bvg
from scraper_sbahn import fetch_sbahn
from utils import generate_tweets, post_threads

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "message": "🚇 BVG / 🚆 S-Bahn Bot aktiv"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/update")
def update():
    return {"status": "no update", "message": "Kein automatischer Update-Endpunkt definiert."}

@app.get("/run")
async def run_scraper():
    logging.info("🚀 Starte Verarbeitung...")

    meldungen = []

    try:
        bvg = await fetch_bvg()
        logging.info(f"✅ {len(bvg)} Meldungen von BVG")
        meldungen.extend(bvg)
    except Exception as e:
        logging.error(f"❌ Fehler bei BVG: {e}")

    try:
        sbahn = await fetch_sbahn()
        logging.info(f"✅ {len(sbahn)} Meldungen von S-Bahn")
        meldungen.extend(sbahn)
    except Exception as e:
        logging.error(f"❌ Fehler bei S-Bahn: {e}")

    if not meldungen:
        logging.warning("⚠️ Keine Meldungen gefunden.")
        return {"status": "done", "meldungen": 0, "threads": 0}

    threads = generate_tweets(meldungen)
    await post_threads(threads)

    return {"status": "done", "meldungen": len(meldungen), "threads": len(threads)}
