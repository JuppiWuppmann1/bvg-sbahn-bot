import asyncio
import threading
import subprocess
import os
from fastapi import FastAPI

from scraper import scrape_bvg, scrape_sbahn
from db import init_db, is_new_message, save_message, reset_db_if_monday
from nebenbot import twitter_login_and_tweet
from utils import enrich_message

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/tmp/playwright"

try:
    subprocess.run(["playwright", "install", "chromium"], check=True)
    print("✅ Chromium erfolgreich installiert.")
except Exception as e:
    print(f"❌ Fehler bei der Playwright-Installation: {e}")

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Bot läuft", "info": "Tweets werden regelmäßig gesendet"}

async def run_bot():
    print("🚀 Starte Verarbeitung...")
    init_db()
    reset_db_if_monday()  # 🧹 NEU: Datenbank zu Wochenbeginn leeren

    print("📡 Lade Daten von BVG...")
    bvg_meldungen = await scrape_bvg()
    print(f"✅ {len(bvg_meldungen)} Meldungen von BVG")

    print("📡 Lade Daten von S-Bahn...")
    sbahn_meldungen = await scrape_sbahn()
    print(f"✅ {len(sbahn_meldungen)} Meldungen von S-Bahn")

    alle_meldungen = bvg_meldungen + sbahn_meldungen

    for meldung in alle_meldungen:
        # Nur vollständige Meldungen verarbeiten
        beschreibung = meldung.get("beschreibung", "")
        zeitraum = meldung.get("zeitraum") or meldung.get("von")
        if beschreibung and zeitraum:
            # Tweet generieren
            raw_text = f"{meldung.get('titel') or meldung.get('art')} – {beschreibung}"
            tweet = enrich_message(raw_text)

            if is_new_message(tweet):
                save_message(tweet)
                await twitter_login_and_tweet(tweet)
                print(f"🐦 Neuer Tweet gesendet:\n{tweet}\n")
            else:
                print("🔁 Tweet bereits bekannt, wird übersprungen.")
        else:
            print("⚠️ Unvollständige Meldung, wird ignoriert.")

def start_loop():
    async def loop():
        while True:
            try:
                await run_bot()
            except Exception as e:
                print(f"❌ Fehler beim Botlauf: {e}")
            await asyncio.sleep(900)

    asyncio.run(loop())

threading.Thread(target=start_loop).start()

