from fastapi import FastAPI, Request, HTTPException
from .settings import settings
from .storage import init_db
from . import scraper_bvg, scraper_sbahn
from .diff import diff_and_apply
from .poster import post_to_x

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/run")
async def run(request: Request):
    token = request.query_params.get("token")
    if settings.RUN_TOKEN and token != settings.RUN_TOKEN:
        raise HTTPException(status_code=401, detail="bad token")

    results = {}
    for name, fetch, parse in [
        ("BVG", scraper_bvg.fetch_html, scraper_bvg.parse_items),
        ("SBAHN", scraper_sbahn.fetch_html, scraper_sbahn.parse_items),
    ]:
        html = fetch()
        items = parse(html)
        new, changed, resolved = diff_and_apply(items)
        for i in new:
            post_to_x(f"[{name}] Neue Meldung: {i.title}\n{i.url or ''}")
        for i in resolved:
            post_to_x(f"[{name}] Beendet: {i.title}\n{i.url or ''}")
        results[name] = {"new": len(new), "changed": len(changed), "resolved": len(resolved)}

    return results
