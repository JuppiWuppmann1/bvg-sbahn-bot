from typing import List, Dict, Tuple
from .storage import get_all_entries, save_entry, mark_resolved

class Entry:
    def __init__(self, id: str, source: str, title: str, detail: str, content_hash: str):
        self.id = id
        self.source = source
        self.title = title
        self.detail = detail
        self.content_hash = content_hash

def diff_and_apply(scraped_items: List[Dict]) -> Tuple[List[Entry], List[Entry], List[Entry]]:
    """
    Vergleicht neue Scraping-Daten mit gespeicherten Einträgen.
    Gibt zurück: (neu, geändert, gelöst).
    """
    stored_entries = {e["id"]: e for e in get_all_entries()}
    scraped_ids = set()
    
    new_entries: List[Entry] = []
    changed_entries: List[Entry] = []
    resolved_entries: List[Entry] = []

    for item in scraped_items:
        entry = Entry(
            id=item["id"],
            source=item["source"],
            title=item["title"],
            detail=item.get("detail", ""),
            content_hash=item["content_hash"],
        )
        scraped_ids.add(entry.id)

        stored = stored_entries.get(entry.id)
        if not stored:
            # Neuer Eintrag
            save_entry(entry)
            new_entries.append(entry)
        elif stored["content_hash"] != entry.content_hash:
            # Geänderter Eintrag
            save_entry(entry)
            changed_entries.append(entry)

    # Aufgelöste Einträge (nicht mehr im aktuellen Lauf vorhanden)
    for stored_id, stored in stored_entries.items():
        if stored_id not in scraped_ids:
            mark_resolved(stored_id)
            resolved_entries.append(
                Entry(
                    id=stored["id"],
                    source=stored["source"],
                    title=stored["title"],
                    detail=stored.get("detail", ""),
                    content_hash=stored["content_hash"],
                )
            )

    return new_entries, changed_entries, resolved_entries
