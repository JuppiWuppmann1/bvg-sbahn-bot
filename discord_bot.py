import os
import logging
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    logging.info(f"🤖 Eingeloggt als {client.user} (ID: {client.user.id})")

async def send_discord_message(message: str):
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        logging.error("❌ Discord Channel konnte nicht gefunden werden! CHANNEL_ID prüfen.")
        return
    await channel.send(message)
    logging.info(f"✅ Nachricht an Discord gesendet: {message}")
