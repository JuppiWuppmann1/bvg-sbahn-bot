import asyncio
import logging
from scraper_bvg import fetch_bvg
from scraper_sbahn import fetch_sbahn
from utils import is_new, mark_as_posted, generate_tweets, post_threads

async def run_every_5_minutes():
    while True:
        logging.info("⏱️ Starte neuen Durchlauf...")
        meldungen = []

        try:
            bvg = await fetch_bvg()
            meldungen.extend([m for m in bvg if is_new(m)])
        except Exception as e:
            logging.error(f"❌ Fehler bei BVG: {e}")

        try:
            sbahn = await fetch_sbahn()
            meldungen.extend([m for m in sbahn if is_new(m)])
        except Exception as e:
            logging.error(f"❌ Fehler bei S-Bahn: {e}")

        if meldungen:
            threads = generate_tweets(meldungen)
            await post_threads(threads)
            for m in meldungen:
                mark_as_posted(m)
        else:
            logging.info("📭 Keine neuen Meldungen.")

        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(run_every_5_minutes())
