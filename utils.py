import os
import json
import logging
import re
from collections import OrderedDict

SEEN_FILE = "seen.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)

def enrich_message(text: str) -> str:
    mapping = {
        "U-Bahn": ("🚇", "#BVG #UBahn"),
        "S-Bahn": ("🚆", "#SBahnBerlin"),
        "Straßenbahn": ("🚋", "#TramBerlin"),
        "Bus": ("🚌", "#BVG #Bus"),
        "Aufzug": ("🛗", "#Barrierefreiheit"),
        "Störung": ("⚠️", "#Störung"),
        "Baumaßnahme": ("🚧", "#Bauarbeiten"),
        "Verspätung": ("⏱️", "#Verspätung"),
        "Ausfall": ("❌", "#Ausfall"),
        "Schienenersatzverkehr": ("🚍", "#SEV"),
    }

    emojis, hashtags = [], []
    for key, (emoji, hashtag) in mapping.items():
        # Wortgrenzen beachten → keine Dopplungen wie "Bus M37 Bus"
        if re.search(rf"\b{re.escape(key)}\b", text, re.IGNORECASE):
            emojis.append(emoji)
            hashtags.extend(hashtag.split())

    # Dopplungen raus (OrderedDict trick)
    emojis = " ".join(OrderedDict.fromkeys(emojis))
    hashtags = " ".join(OrderedDict.fromkeys(hashtags + ["#Berlin"]))

    return f"{emojis} {hashtags}".strip()

def generate_tweets(meldungen):
    threads = []
    for m in meldungen:
        beschreibung = m.get("beschreibung", "").strip()
        titel = m.get("titel") or "Störung"
        extras = enrich_message(f"{titel} {beschreibung}")
        prefix = "🚧 BVG:" if m.get("quelle") == "BVG" else "⚠️ S-Bahn:"
        header = f"{prefix} {titel}"

        full_text = f"{header}\n📝 {beschreibung}\n{extras}".strip()

        if len(full_text) <= 280:
            threads.append([full_text])
        else:
            # Text in Stücke <280 Zeichen
            parts = [header]
            beschreibung_chunks = [
                beschreibung[i:i+240] for i in range(0, len(beschreibung), 240)
            ]
            for chunk in beschreibung_chunks:
                parts.append(f"📝 {chunk.strip()}")
            if extras:
                parts.append(extras)
            threads.append(parts)

    return threads
