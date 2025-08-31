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


async def job():
    logging.info("🔎 Starte neuen Check...")
    try:
        bvg_result = await run_bvg_scraper()
        sbahn_result = await run_sbahn_scraper()

        if bvg_result:
            await send_discord_message(f"🚇 BVG-Update: {bvg_result}")
        if sbahn_result:
            await send_discord_message(f"🚆 S-Bahn-Update: {sbahn_result}")

        if not bvg_result and not sbahn_result:
            logging.info("ℹ️ Keine neuen Störungen gefunden.")
    except Exception as e:
        logging.error(f"❌ Fehler im Job: {e}")


@app.on_event("startup")
async def startup_event():
    scheduler.add_job(job, "interval", minutes=10)
    scheduler.start()
    logging.info("⏰ Scheduler gestartet (alle 10 Minuten)")

    # Testnachricht an Discord
    asyncio.create_task(send_discord_message("🚀 Bot erfolgreich gestartet und verbunden!"))


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/run")
async def run_check():
    await job()
    return {"status": "check completed"}


# Discord-Bot starten
async def start_discord_bot():
    await client.start(client.http.token)


# Hintergrund-Task für Discord starten
@app.on_event("startup")
async def start_discord_task():
    asyncio.create_task(start_discord_bot())

