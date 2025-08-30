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

last_titles = set()


async def job():
    global last_titles
    logging.info("🔎 Starte neuen Check...")

    # BVG
    bvg_disruptions = scrape_bvg_disruptions(max_pages=5)
    for d in bvg_disruptions:
        if d["title"] not in last_titles:
            msg = (
                f"🚇 **BVG Störung**: {d['title']}\n"
                f"📌 Typ: {d['type']}\n"
                f"🕒 Von: {d['start']}  Bis: {d['end']}\n"
                f"ℹ️ {d['details']}"
            )
            await send_discord_message(msg)
            last_titles.add(d["title"])

    # S-Bahn
    sbahn_disruptions = scrape_sbahn_disruptions()
    for d in sbahn_disruptions:
        if d["title"] not in last_titles:
            msg = (
                f"🚆 **S-Bahn Störung**: {d['title']}\n"
                f"🕒 {d['date']}\n"
                f"ℹ️ {d['subtitle']}\n"
                f"{d['details']}"
            )
            await send_discord_message(msg)
            last_titles.add(d["title"])


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
