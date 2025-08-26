import logging
from fastapi import FastAPI
from scraper import scrape_bvg
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
    return {"status": "ok", "message": "BVG/S-Bahn Bot läuft 🚇"}

@app.get("/update")
def update():
    try:
        messages = scrape_bvg()
        logger.info(f"🔍 {len(messages)} BVG-Meldungen gefunden")

        for msg in messages:
            post_update(msg)
        return {"status": "ok", "count": len(messages)}

    except Exception as e:
        logger.error(f"❌ Fehler beim Update: {e}")
        return {"status": "error", "error": str(e)}
