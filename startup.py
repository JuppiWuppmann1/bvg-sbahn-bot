from playwright.__main__ import main as playwright_main

def install_playwright():
    playwright_main(["install", "chromium"])
