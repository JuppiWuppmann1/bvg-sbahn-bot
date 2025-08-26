import logging
from fastapi import FastAPI
from scraper_bvg import scrape_bvg
from scraper_sbahn import scrape_sbahn
from twitter_bot import post_update

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok", "message": "BVG & S-Bahn Bot läuft 🚇"}

@app.get("/update")
def update():
    try:
        messages = []

        # BVG Scraping
        bvg_msgs = scrape_bvg()
        logger.info(f"🔍 {len(bvg_msgs)} BVG-Meldungen gefunden")
        messages.extend(bvg_msgs)

        # S-Bahn Scraping
        sbahn_msgs = scrape_sbahn()
        logger.info(f"🔍 {len(sbahn_msgs)} S-Bahn-Meldungen gefunden")
        messages.extend(sbahn_msgs)

        # Posten
        for msg in messages:
            post_update(msg)

        return {"status": "ok", "count": len(messages)}

    except Exception as e:
        logger.error(f"❌ Fehler beim Update: {e}")
        return {"status": "error", "error": str(e)}
