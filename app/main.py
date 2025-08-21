from fastapi import FastAPI, Request, HTTPException
from .settings import settings
from .storage import init_db
from .scraper_bvg import fetch_all_items
from .import scraper_sbahn
from .diff import diff_and_apply
from .poster import post_to_x

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

def format_message(name: str, title: str, status: str) -> str:
    title_lower = title.lower()

    # Emoji + Label basierend auf Schlüsselwörtern
    if "störung" in title_lower:
        emoji = "🚨"
        label = "Störung"
        tag = "#Störung"
    elif "baustelle" in title_lower:
        emoji = "🛠️"
        label = "Baustelle"
        tag = "#Baustelle"
    elif "verspätung" in title_lower:
        emoji = "⏱️"
        label = "Verspätung"
        tag = "#Verspätung"
    elif "ersatzverkehr" in title_lower:
        emoji = "🚌"
        label = "Ersatzverkehr"
        tag = "#Ersatzverkehr"
    elif "signal" in title_lower:
        emoji = "🚦"
        label = "Signalstörung"
        tag = "#Signal"
    else:
        emoji = "ℹ️"
        label = "Info"
        tag = "#Info"

    # Status-Text
    if status == "new":
        prefix = f"{emoji} [{name}] NEU ({label}):"
    elif status == "resolved":
        prefix = f"✅ [{name}] ENDE ({label}):"
    else:
        prefix = f"🔔 [{name}] UPDATE ({label}):"

    # Hashtags
    source_tag = "#BVG" if name == "BVG" else "#SBAHN"
    hashtags = f"{source_tag} {tag}"

    return f"{prefix} {title}\n{hashtags}"

def process_run(token: str):
    if settings.RUN_TOKEN and token != settings.RUN_TOKEN:
        raise HTTPException(status_code=401, detail="bad token")

    results = {}
    for name, fetch_items in [
        ("BVG", fetch_all_items),
        ("SBAHN", fetch_sbahn_items),  # Falls du das dort auch ergänzt
    ]:
        items = fetch_items()
        new, changed, resolved = diff_and_apply(items)
        for i in new:
            message = format_message(name, i.title, "new")
            post_to_x(message)
        for i in resolved:
            message = format_message(name, i.title, "resolved")
            post_to_x(message)
        results[name] = {"new": len(new), "changed": len(changed), "resolved": len(resolved)}

    return results

@app.post("/run")
async def run_post(request: Request):
    token = request.query_params.get("token")
    return process_run(token)

@app.get("/run")
async def run_get(request: Request):
    token = request.query_params.get("token")
    return process_run(token)

