from fastapi import FastAPI
from scraper import scrape_bvg, scrape_sbahn
from nebenbot import twitter_login_and_tweet
from utils import generate_tweets
from db import is_new_message, save_message, init_db, reset_db_if_monday
import logging
import asyncio

# Logger Setup
logger = logging.getLogger("bvg-sbahn-bot")
logging.basicConfig(level=logging.INFO)

# Datenbank initialisieren
init_db()
reset_db_if_monday()

app = FastAPI(title="BVG & S-Bahn Bot")

@app.get("/")
def home():
    return {"status": "running"}

@app.get("/update")
async def update():
    logger.info("Update gestartet")

    # Asynchrone Scraper ausführen
    bvg_msgs = await scrape_bvg()
    sbahn_msgs = await scrape_sbahn()

    all_msgs = bvg_msgs + sbahn_msgs
    tweets = generate_tweets(all_msgs)

    posted = 0
    for tweet in tweets:
        if is_new_message(tweet):
            save_message(tweet)
            await twitter_login_and_tweet(tweet)
            posted += 1
        else:
            logger.info("⏭️ Tweet bereits bekannt, wird übersprungen.")

    return {"posted": posted, "total_scraped": len(all_msgs)}
