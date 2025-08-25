import os
import subprocess
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# Chromium installieren, falls nicht vorhanden
chromium_path = "/opt/render/.cache/ms-playwright/chromium_headless_shell-1181/chrome-linux/headless_shell"
if not os.path.exists(chromium_path):
    print("🔧 Installiere Chromium für Playwright...")
    subprocess.run(["playwright", "install", "chromium"], check=True)
    print("✅ Chromium installiert.")

from .settings import settings
from .storage import init_db
from .scraper_bvg import fetch_all_items as fetch_bvg_items
from .scraper_sbahn import fetch_all_items as fetch_sbahn_items
from .diff import diff_and_apply
from .poster import post_to_x

app = FastAPI(title="BVG & S-Bahn Bot", version="1.0.0")

@app.on_event("startup")
async def startup():
    print("🔧 Initialisiere Datenbank...")
    init_db()
    print("✅ Datenbank bereit.")

    async def delayed_start():
        await asyncio.sleep(10)
        asyncio.create_task(loop_scraper())

    asyncio.create_task(delayed_start())

@app.api_route("/health", methods=["GET", "HEAD"])
def health(_: Request):
    return JSONResponse(content={"ok": True}, status_code=200)

@app.api_route("/", methods=["GET", "HEAD"])
async def root(_: Request):
    return JSONResponse(
        content={"message": "🚆 BVG und S-Bahn Bot läuft!", "status": "ok"},
        status_code=200,
    )

# Kategorisierung bleibt wie gehabt
KEYWORDS = {
    "störung": ["störung", "unterbrechung", "ausfall", "defekt", "problem"],
    "baustelle": ["baustelle", "bauarbeiten", "bau", "arbeiten"],
    # ... (weitere Kategorien)
}

def detect_category(title: str) -> tuple[str, str, str]:
    title_lower = title.lower()
    for category, synonyms in KEYWORDS.items():
        if any(word in title_lower for word in synonyms):
            # Emoji und Label je nach Kategorie
            mapping = {
                "störung": ("🚨", "Störung", "#Störung"),
                "baustelle": ("🛠️", "Baustelle", "#Baustelle"),
                "verspätung": ("⏱️", "Verspätung", "#Verspätung"),
                "ersatzverkehr": ("🚌", "Ersatzverkehr", "#Ersatzverkehr"),
                "signal": ("🚦", "Signalstörung", "#Signal"),
                "wetter": ("🌧️", "Wetterbedingung", "#Wetter"),
                "streik": ("✊", "Streik", "#Streik"),
                "polizei": ("🚓", "Polizeieinsatz", "#Polizei"),
            }
            return mapping.get(category, ("ℹ️", "Info", "#Info"))
    return ("ℹ️", "Info", "#Info")

def format_message(name: str, title: str, status: str, timestamp: datetime | None = None, detail: str | None = None) -> str:
    emoji, label, tag = detect_category(title)
    prefix = {
        "new": f"{emoji} [{name}] NEU ({label}):",
        "resolved": f"✅ [{name}] ENDE ({label}):",
    }.get(status, f"🔔 [{name}] UPDATE ({label}):")

    source_tag = "#BVG" if name.upper() == "BVG" else "#SBAHN"
    timestamp = timestamp or datetime.now()
    time_str = timestamp.strftime("%d.%m.%Y, %H:%M Uhr")
    detail_text = f"\n📝 {detail}" if detail else ""
    return f"{prefix} {title}{detail_text}\n📅 {time_str}\n{source_tag} {tag}"

async def process_run(token: str | None):
    if not token:
        raise HTTPException(status_code=400, detail="token required")
    if settings.RUN_TOKEN and token != settings.RUN_TOKEN:
        print("❌ Ungültiger Token:", token)
        raise HTTPException(status_code=401, detail="bad token")

    print("🚀 Starte Verarbeitung...")
    results = {}

    for name, fetch_items in [("BVG", fetch_bvg_items), ("SBAHN", fetch_sbahn_items)]:
        print(f"📡 Lade Daten von {name}...")
        items = await fetch_items()
        print(f"✅ {len(items)} Einträge geladen von {name}")

        new, changed, resolved = diff_and_apply(items)
        print(f"🆕 Neue: {len(new)}, 🔄 Geändert: {len(changed)}, ✅ Gelöst: {len(resolved)}")

        for entry in new:
            msg = format_message(entry.source, entry.title, "new", detail=entry.detail)
            print("📤 Sende Tweet:", msg)
            await post_to_x(msg)

        for entry in resolved:
            msg = format_message(entry.source, entry.title, "resolved", detail=entry.detail)
            print("📤 Sende Tweet:", msg)
            await post_to_x(msg)

        results[name] = {"new": len(new), "changed": len(changed), "resolved": len(resolved)}

    print("🏁 Verarbeitung abgeschlossen:", results)
    return results

async def loop_scraper():
    while True:
        try:
            if settings.RUN_TOKEN:
                await process_run(settings.RUN_TOKEN)
            else:
                print("⚠️ Kein RUN_TOKEN gesetzt – überspringe Auto-Run")
        except Exception as e:
            print("❌ Fehler im Auto-Run:", e)
        await asyncio.sleep(300)

@app.post("/run")
async def run_post(request: Request):
    token = request.query_params.get("token")
    return await process_run(token)

@app.get("/run")
async def run_get(request: Request):
    token = request.query_params.get("token")
    return await process_run(token)
