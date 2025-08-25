def enrich_message(text: str) -> str:
    """Ergänzt Meldungen mit passenden Emojis & Hashtags"""

    mapping = {
        "U-Bahn": ("🚇", "#BVG #UBahn"),
        "S-Bahn": ("🚆", "#SBahnBerlin"),
        "Straßenbahn": ("🚋", "#TramBerlin"),
        "Bus": ("🚌", "#BVG #Bus"),
        "Aufzug": ("🛗", "#Barrierefreiheit"),
        "Fahrstuhl": ("🛗", "#Barrierefreiheit"),
        "Störung": ("⚠️", "#Störung"),
        "Baumaßnahme": ("🚧", "#Bauarbeiten"),
        "Verspätung": ("⏱️", "#Verspätung"),
        "Ausfall": ("❌", "#Ausfall"),
        "geschlossen": ("🔒", "#Info"),
        "Schienenersatzverkehr": ("🚍", "#SEV"),
    }

    emojis = []
    hashtags = []

    for key, (emoji, hashtag) in mapping.items():
        if key.lower() in text.lower():
            emojis.append(emoji)
            hashtags.append(hashtag)

    # Nur eindeutige Hashtags + Emojis
    emojis = " ".join(set(emojis))
    hashtags = " ".join(set(hashtags))

    tweet = f"{emojis} {text} {hashtags}".strip()
    return tweet[:280]  # Sicherheitshalber kürzen
