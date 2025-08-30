import os
import logging
import asyncio
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scraper_bvg import scrape_bvg_disruptions
from scraper_sbahn import scrape_sbahn_disruptions
from discord_bot import send_discord_message, client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI()
scheduler = AsyncIOScheduler()

# hier merken wir uns bekannte Störungen
active_disruptions = set()


async def job():
    global active_disruptions
    logging.info("🔎 Starte neuen Check...")

    current_titles = set()

    # --- BVG ---
    bvg_disruptions = scrape_bvg_disruptions(max_pages=5)
    for d in bvg_disruptions:
        title = f"BVG: {d['title']}"
        current_titles.add(title)

        if title not in active_disruptions:
            msg = (
                f"🚇 **Neue BVG Störung**: {d['title']}\n"
                f"📌 Typ: {d['type']}\n"
                f"🕒 Von: {d['start']}  Bis: {d['end']}\n"
                f"ℹ️ {d['details']}"
            )
            await send_discord_message(msg)

    # --- S-Bahn ---
    sbahn_disruptions = scrape_sbahn_disruptions()
    for d in sbahn_disruptions:
        title = f"S-Bahn: {d['title']}"
        current_titles.add(title)

        if title not in active_disruptions:
            msg = (
                f"🚆 **Neue S-Bahn Störung**: {d['title']}\n"
                f"🕒 {d['date']}\n"
                f"ℹ️ {d['subtitle']}\n"
                f"{d['details']}"
            )
            await send_discord_message(msg)

    # --- Prüfen ob etwas verschwunden ist ---
    disappeared = active_disruptions - current_titles
    for old in disappeared:
        await send_discord_message(f"✅ **Behoben:** {old}")

    # neuen Stand speichern
    active_disruptions = current_titles


@app.on_event("startup")
async def startup_event():
    scheduler.add_job(job, "interval", minutes=10)
    scheduler.start()
    logging.info("⏰ Scheduler gestartet (alle 10 Minuten)")
    asyncio.create_task(client.start(os.getenv("DISCORD_TOKEN")))


@app.get("/run")
async def run_once():
    await job()
    return {"status": "done"}
