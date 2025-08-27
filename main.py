import logging
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from scraper_bvg import scrape_bvg
from scraper_sbahn import scrape_sbahn
from utils import generate_tweets
from x_poster import post_thread

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = FastAPI()

# damit wir nicht doppelt posten
posted_ids = set()

def job_run():
    logging.info("🔄 Starte automatischen Scrape-Job...")

    # BVG + S-Bahn Scrapen
    bvg_meldungen = scrape_bvg()
    sbahn_meldungen = scrape_sbahn()

    logging.info(f"✅ {len(bvg_meldungen)} BVG-Meldungen gefunden")
    logging.info(f"✅ {len(sbahn_meldungen)} S-Bahn-Meldungen gefunden")

    # Tweets generieren
    threads = generate_tweets(bvg_meldungen + sbahn_meldungen)

    for thread in threads:
        # ID bauen (damit keine Dopplungen gepostet werden)
        thread_id = hash(" ".join(thread))
        if thread_id in posted_ids:
            logging.info("⏭️ Meldung schon gepostet, überspringe...")
            continue

        try:
            post_thread(thread)
            posted_ids.add(thread_id)
            logging.info(f"🐦 Erfolgreich gepostet: {thread[0][:50]}...")
        except Exception as e:
            logging.error(f"❌ Fehler beim Posten: {e}")


@app.on_event("startup")
async def startup_event():
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_run, "interval", minutes=5)
    scheduler.start()
    logging.info("⏰ Scheduler gestartet: alle 5 Minuten Scraping + Posting")
