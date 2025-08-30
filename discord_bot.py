import os
import discord
from discord.ext import commands

# Discord Token und Channel-ID aus Umgebungsvariablen lesen
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

client = commands.Bot(command_prefix="!", intents=intents)

async def send_discord_message(message: str):
    """Sendet eine Nachricht an den konfigurierten Discord-Kanal"""
    if not TOKEN or CHANNEL_ID == 0:
        print("⚠️ Discord-Umgebungsvariablen fehlen!")
        return

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(message)
    else:
        print("⚠️ Konnte Discord-Kanal nicht finden!")
