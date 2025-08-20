from datetime import datetime
from sqlalchemy import select
from .storage import SessionLocal, Incident

def diff_and_apply(current_items):
    new, changed, resolved = [], [], []
    with SessionLocal() as db:
        existing = {i.id: i for i in db.execute(select(Incident)).scalars()}
        current_ids = set()
        for it in current_items:
            current_ids.add(it["id"])
            if it["id"] not in existing:
                i = Incident(
                    id=it["id"], source=it["source"],
                    title=it["title"], lines=it["lines"],
                    url=it["url"], content_hash=it["content_hash"]
                )
                db.add(i); new.append(i)
            else:
                i = existing[it["id"]]
                if i.content_hash != it["content_hash"]:
                    i.title = it["title"]; i.lines = it["lines"]; i.url = it["url"]
                    i.content_hash = it["content_hash"]; changed.append(i)
                i.status = "active"; i.last_seen = datetime.utcnow()
        for _id, i in existing.items():
            if _id not in current_ids and i.status != "resolved":
                i.status = "resolved"; i.last_seen = datetime.utcnow(); resolved.append(i)
        db.commit()
    return new, changed, resolved
