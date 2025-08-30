def build_threads(meldungen):
    threads = []
    for meldung in meldungen:
        parts = [
            f"**{meldung['quelle']}**\n{meldung['titel']}",
            meldung["beschreibung"]
        ]
        threads.append(parts)
    return threads
