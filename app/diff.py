from .storage import save_entry, get_active_incidents, mark_resolved

def diff_and_apply(scraped_items):
    """Vergleicht Scraper-Ergebnisse mit der DB und liefert neue / geänderte / gelöste Incidents zurück."""
    new_entries = []
    changed_entries = []
    resolved_entries = []

    # DB: alle aktiven holen
    active = {inc.id: inc for inc in get_active_incidents()}

    # Neue & geänderte Incidents
    for item in scraped_items:
        db_item = active.pop(item.id, None)

        if not db_item:
            new_entries.append(item)
            save_entry(item)
        elif db_item.content_hash != item.content_hash:
            changed_entries.append(item)
            save_entry(item)
        else:
            # Falls gleich → trotzdem updaten, um last_seen aktuell zu halten
            save_entry(item)

    # Alles, was übrig ist, wurde nicht mehr gemeldet → resolved
    for inc in active.values():
        resolved_entries.append(inc)
        mark_resolved(inc.id)

    return new_entries, changed_entries, resolved_entries
