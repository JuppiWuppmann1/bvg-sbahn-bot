import os
import asyncio
import logging
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scraper_bvg import run_bvg_scraper
from scraper_sbahn import run_sbahn_scraper
from discord_bot import send_discord_message, client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI()
scheduler = AsyncIOScheduler()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

async def job():
    logging.info("🔎 Starte neuen Check...")
    try:
        bvg_result = await run_bvg_scraper(send_discord_message)
        sbahn_result = await run_sbahn_scraper(send_discord_message)

        for msg in sbahn_result:
            await send_discord_message(msg)

        if not bvg_result and not sbahn_result:
            logging.info("ℹ️ Keine neuen Störungen gefunden.")
    except Exception as e:
        logging.error(f"❌ Fehler im Job: {e}")


@app.on_event("startup")
async def startup_event():
    scheduler.add_job(job, "interval", minutes=10)
    scheduler.start()
    logging.info("⏰ Scheduler gestartet (alle 10 Minuten)")

    # Starte Discord-Bot separat
    asyncio.create_task(start_discord_bot())

@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/run")
async def run_check():
    await job()
    return {"status": "check completed"}

async def start_discord_bot():
    if not DISCORD_TOKEN:
        logging.error("❌ Kein DISCORD_TOKEN gefunden!")
        return
    try:
        await client.start(DISCORD_TOKEN)
    except Exception as e:
        logging.error(f"❌ Fehler beim Starten des Discord-Bots: {e}")
