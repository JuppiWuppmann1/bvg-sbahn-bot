import logging
from scraper_bvg import scrape_bvg
from scraper_sbahn import scrape_sbahn
from utils import generate_tweets
from twitter_bot import post_thread

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("📡 Sammle BVG- und S-Bahn-Meldungen...")

    meldungen = []
    meldungen.extend(scrape_bvg(max_pages=3))
    meldungen.extend(scrape_sbahn())

    if not meldungen:
        logger.info("ℹ️ Keine neuen Meldungen gefunden.")
        return

    logger.info(f"✅ {len(meldungen)} Meldungen gesammelt")

    threads = generate_tweets(meldungen)

    for idx, parts in enumerate(threads, start=1):
        logger.info(f"📢 Sende Thread {idx} mit {len(parts)} Tweets...")
        try:
            post_thread(parts)
            logger.info("✅ Thread erfolgreich gepostet")
        except Exception as e:
            logger.error(f"❌ Fehler beim Tweeten: {e}")


if __name__ == "__main__":
    main()
