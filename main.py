import logging
import asyncio
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from sbahn_scraper import scrape_sbahn
from bvg_scraper import scrape_bvg
from thread_builder import build_threads
from discord_poster import post_to_discord

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = FastAPI()
scheduler = AsyncIOScheduler()

async def job():
    logging.info("🔎 Starte neuen Check...")

    sbahn_meldungen = await scrape_sbahn()
    bvg_meldungen = await scrape_bvg()

    meldungen = sbahn_meldungen + bvg_meldungen
    if not meldungen:
        logging.info("ℹ️ Keine neuen Meldungen gefunden.")
        return

    threads = build_threads(meldungen)

    await post_to_discord(threads)

@app.get("/run")
async def run_once():
    logging.info("🚀 /run endpoint aufgerufen")
    await job()
    return {"status": "done"}

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(job, "interval", minutes=5, id="job")
    scheduler.start()
    logging.info("⏰ Scheduler gestartet (alle 5 Minuten)")
