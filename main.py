import asyncio
from scraper import scrape_bvg, scrape_sbahn
from db import init_db, is_new_message, save_message
from nebenbot import twitter_login_and_tweet

async def main():
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
            await twitter_login_and_tweet(f"🚧 Neue Meldung:\n{meldung}")

if __name__ == "__main__":
    asyncio.run(main())
