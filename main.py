from fastapi import FastAPI
from scraper import scrape_bvg, scrape_sbahn
from poster import post_message
from logger import logger

app = FastAPI(title="BVG & S-Bahn Bot")

@app.get("/")
def home():
    return {"status": "running"}

@app.get("/update")
def update():
    logger.info("Update gestartet")

    bvg_msgs = scrape_bvg()
    sbahn_msgs = scrape_sbahn()

    all_msgs = bvg_msgs + sbahn_msgs

    for msg in all_msgs:
        post_message(msg)

    return {"posted": len(all_msgs)}
