import logging
import os
import aiohttp
import asyncio

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

async def post_to_discord(threads):
    if not WEBHOOK_URL:
        logging.error("❌ Kein DISCORD_WEBHOOK gesetzt!")
        return

    async with aiohttp.ClientSession() as session:
        for i, thread in enumerate(threads, 1):
            content = "\n\n".join(thread)
            try:
                payload = {"content": content}
                async with session.post(WEBHOOK_URL, json=payload) as resp:
                    if resp.status == 204:
                        logging.info(f"✅ Thread {i} an Discord gesendet.")
                    else:
                        text = await resp.text()
                        logging.error(f"❌ Fehler bei Thread {i}: {resp.status} {text}")
                await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"❌ Exception beim Senden an Discord: {e}")
