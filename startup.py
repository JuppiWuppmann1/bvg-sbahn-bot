import asyncio
from playwright.__main__ import main as playwright_main

async def install_playwright():
    await asyncio.to_thread(playwright_main, ["install", "chromium"])
