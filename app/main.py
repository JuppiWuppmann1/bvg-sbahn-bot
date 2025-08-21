from fastapi.responses import JSONResponse
from datetime import datetime
from .settings import settings
from .storage import init_db
from .scraper_bvg import fetch_all_items as fetch_bvg_items
from .scraper_sbahn import fetch_all_items as fetch_sbahn_items
from .diff import diff_and_apply
from .poster import post_to_x  # post_to_x muss async sein!

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return JSONResponse(content={"ok": True}, status_code=200)

# Schlüsselwörter pro Kategorie
KEYWORDS = {
    "störung": ["störung", "unterbrechung", "ausfall", "defekt", "problem"],
    "baustelle": ["baustelle", "bauarbeiten", "bau", "arbeiten"],
    "verspätung": ["verspätung", "verzögerung", "wartezeit", "verzögert"],
    "ersatzverkehr": ["ersatzverkehr", "schienenersatz", "busverkehr", "umleitung"],
    "signal": ["signal", "ampel", "signalstörung", "signalproblem"],
    "wetter": ["regen", "schnee", "unwetter", "sturm", "hitze", "glätte"],
    "streik": ["streik", "arbeitskampf", "tarifverhandlung", "gewerkschaft"],
    "polizei": ["polizei", "einsatz", "kripo", "ermittlung", "sicherheitslage"]
}

# Kategorie-Erkennung
def detect_category(title: str) -> tuple[str, str, str]:
    title_lower = title.lower()
    for category, synonyms in KEYWORDS.items():
        if any(word in title_lower for word in synonyms):
            if category == "störung":
                return "🚨", "Störung", "#Störung"
            elif category == "baustelle":
                return "🛠️", "Baustelle", "#Baustelle"
            elif category == "verspätung":
                return "⏱️", "Verspätung", "#Verspätung"
            elif category == "ersatzverkehr":
                return "🚌", "Ersatzverkehr", "#Ersatzverkehr"
            elif category == "signal":
                return "🚦", "Signalstörung", "#Signal"
            elif category == "wetter":
                return "🌧️", "Wetterbedingung", "#Wetter"
            elif category == "streik":
                return "✊", "Streik", "#Streik"
            elif category == "polizei":
                return "🚓", "Polizeieinsatz", "#Polizei"
    return "ℹ️", "Info", "#Info"

# Formatierte Nachricht mit Zeitstempel
def format_message(name: str, title: str, status: str, timestamp: datetime = None) -> str:
    emoji, label, tag = detect_category(title)

    if status == "new":
        prefix = f"{emoji} [{name}] NEU ({label}):"
    elif status == "resolved":
        prefix = f"✅ [{name}] ENDE ({label}):"
    else:
        prefix = f"🔔 [{name}] UPDATE ({label}):"

    source_tag = "#BVG" if name.upper() == "BVG" else "#SBAHN"
    hashtags = f"{source_tag} {tag}"

    if timestamp is None:
        timestamp = datetime.now()
    time_str = timestamp.strftime("%d.%m.%Y, %H:%M Uhr")

    return f"{prefix} {title}\n📅 {time_str}\n{hashtags}"

# Hauptprozess
async def process_run(token: str):
    if settings.RUN_TOKEN and token != settings.RUN_TOKEN:
        raise HTTPException(status_code=401, detail="bad token")

    results = {}
    for name, fetch_items in [
        ("BVG", fetch_bvg_items),
        ("SBAHN", fetch_sbahn_items),
    ]:
        items = fetch_items()
        new, changed, resolved = diff_and_apply(items)

        for i in new:
            title = i.title  # Zugriff innerhalb aktiver Session
            message = format_message(name, title, "new")
            await post_to_x(message)

        for i in resolved:
            title = i.title
            message = format_message(name, title, "resolved")
            await post_to_x(message)

        results[name] = {
            "new": len(new),
            "changed": len(changed),
            "resolved": len(resolved)
        }

    return results

@app.post("/run")
async def run_post(request: Request):
    token = request.query_params.get("token")
    return await process_run(token)

@app.get("/run")
async def run_get(request: Request):
    token = request.query_params.get("token")
    return await process_run(token)
