import asyncio
import threading
import time
from fastapi import FastAPI

from scraper import scrape_bvg, scrape_sbahn
from db import init_db, is_new_message, save_message
from nebenbot import twitter_login_and_tweet
from utils import enrich_message

# FastAPI-App für Render Webservice
app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Bot läuft", "info": "Tweets werden regelmäßig gesendet"}

# Bot-Logik
async def run_bot():
    print("🚀 Starte Verarbeitung...")
    init_db()

    print("📡 Lade Daten von BVG...")
    bvg_meldungen = await scrape_bvg()
    print(f"✅ {len(bvg_meldungen)} Meldungen von BVG")

    print("📡 Lade Daten von S-Bahn...")
    sbahn_meldungen = await scrape_sbahn()
    print(f"✅ {len(sbahn_meldungen)} Meldungen von S-Bahn")

    alle_meldungen = bvg_meldungen + sbahn_meldungen

    for meldung in alle_meldungen:
        if is_new_message(meldung):
            save_message(meldung)
            tweet = enrich_message(meldung)
            await twitter_login_and_tweet(tweet)

# Wiederholungs-Schleife im Hintergrund
def start_loop():
    async def loop():
        while True:
            try:
                await run_bot()
            except Exception as e:
                print(f"❌ Fehler beim Botlauf: {e}")
            time.sleep(900)  # alle 15 Minuten

    asyncio.run(loop())

# Starte Bot beim Hochfahren
threading.Thread(target=start_loop).start()
