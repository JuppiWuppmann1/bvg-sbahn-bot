from datetime import datetime
from sqlalchemy import select
from .storage import SessionLocal, Incident

def diff_and_apply(current_items):
    new, changed, resolved = [], [], []

    # Duplikate entfernen
    seen_ids = set()
    deduped_items = []
    for item in current_items:
        if item["id"] not in seen_ids:
            deduped_items.append(item)
            seen_ids.add(item["id"])

    with SessionLocal() as db:
        existing = {i.id: i for i in db.execute(select(Incident)).scalars()}
        current_ids = set()

        for it in deduped_items:
            current_ids.add(it["id"])
            lines_str = ", ".join(it["lines"]) if isinstance(it["lines"], list) else (it["lines"] or "")

            if it["id"] not in existing:
                i = Incident(
                    id=it["id"],
                    source=it["source"],
                    title=it["title"],
                    lines=lines_str,
                    url=it["url"],
                    content_hash=it["content_hash"],
                    detail=it.get("detail", "")
                )
                db.merge(i)
                new.append(i)
            else:
                i = existing[it["id"]]
                if i.content_hash != it["content_hash"]:
                    i.title = it["title"]
                    i.lines = lines_str
                    i.url = it["url"]
                    i.content_hash = it["content_hash"]
                    i.detail = it.get("detail", i.detail)
                    changed.append(i)
                i.status = "active"
                i.last_seen = datetime.utcnow()

        for _id, i in existing.items():
            if _id not in current_ids and i.status != "resolved":
                i.status = "resolved"
                i.last_seen = datetime.utcnow()
                resolved.append(i)

        db.commit()

    return new, changed, resolved
