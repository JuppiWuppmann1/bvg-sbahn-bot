import re

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

    emojis = " ".join(set(emojis))
    hashtags = " ".join(set(hashtags))

    return f"{emojis} {hashtags}".strip()


def generate_tweets(meldungen):
    """Erzeugt formatierte Tweets aus vollständigen Meldungen"""
    tweets = []

    for m in meldungen:
        # Nur vollständige Meldungen verarbeiten
        beschreibung = m.get("beschreibung", "").strip()
        zeitraum = m.get("zeitraum") or f"{m.get('von')} → {m.get('bis')}"
        titel = m.get("titel") or m.get("art") or "Störung"

        if not beschreibung or not zeitraum:
            continue  # Unvollständig, überspringen

        # Linien
        linien = ", ".join(m.get("linien", []))
        linien_str = f" ({linien})" if linien else ""

        # Beschreibung kürzen
        beschreibung = re.sub(r"\s+", " ", beschreibung)
        beschreibung = beschreibung[:180] + "..." if len(beschreibung) > 200 else beschreibung

        # Emojis & Hashtags ergänzen
        extras = enrich_message(f"{titel} {beschreibung}")

        # Tweet zusammenbauen
        prefix = "🚧 BVG:" if "art" in m else "⚠️ S-Bahn:"
        tweet = f"{prefix} {titel}{linien_str}\n🕒 {zeitraum}\n📝 {beschreibung}\n{extras}"
        tweets.append(tweet[:280])  # Sicherheitshalber kürzen

    return tweets

