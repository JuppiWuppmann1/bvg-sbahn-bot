import os
import logging
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

intents = discord.Intents.default()
intents.message_content = True  # Für spätere Befehle, falls gebraucht
client = commands.Bot(command_prefix="!", intents=intents)


async def send_discord_message(message: str):
    """Sendet eine Nachricht an den definierten Discord-Kanal"""
    try:
        channel = client.get_channel(int(CHANNEL_ID))
        if channel is None:
            logging.error("❌ Discord Channel konnte nicht gefunden werden! CHANNEL_ID prüfen.")
            return
        await channel.send(message)
        logging.info(f"✅ Nachricht an Discord gesendet: {message}")
    except Exception as e:
        logging.error(f"❌ Fehler beim Senden an Discord: {e}")


@client.event
async def on_ready():
    logging.info(f"🤖 Eingeloggt als {client.user} (ID: {client.user.id})")
