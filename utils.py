import re
from collections import OrderedDict

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
        if re.search(rf"\b{re.escape(key)}\b", text, re.IGNORECASE):
            emojis.append(emoji)
            hashtags.extend(hashtag.split())

    emojis = " ".join(OrderedDict.fromkeys(emojis))
    hashtags = " ".join(OrderedDict.fromkeys(hashtags + ["#Berlin"]))

    return f"{emojis} {hashtags}".strip()


def generate_tweets(meldungen):
    """Erzeugt formatierte Tweets oder Threads aus vollständigen Meldungen"""
    threads = []

    for m in meldungen:
        beschreibung = m.get("beschreibung", "").strip()
        von = m.get("von")
        bis = m.get("bis")
        zeitraum = m.get("zeitraum") or (f"{von} → {bis}" if von and bis else None)
        titel = m.get("titel") or m.get("art") or "Störung"

        if not beschreibung or not zeitraum:
            continue

        linien = ", ".join(m.get("linien", []))
        linien_str = f" ({linien})" if linien else ""

        beschreibung = re.sub(r"\s+", " ", beschreibung)
        extras = enrich_message(f"{titel} {beschreibung}")
        prefix = "🚧 BVG:" if "art" in m else "⚠️ S-Bahn:"
        header = f"{prefix} {titel}{linien_str}\n🕒 {zeitraum}"

        full_text = f"{header}\n📝 {beschreibung}\n{extras}"

        if len(full_text) <= 280:
            threads.append([full_text])
        else:
            # Thread aufteilen
            parts = [header]
            beschreibung_chunks = [beschreibung[i:i+240] for i in range(0, len(beschreibung), 240)]
            for chunk in beschreibung_chunks:
                parts.append(f"📝 {chunk.strip()}")
            if extras:
                parts.append(extras)
            threads.append(parts)

    return threads
