import os, json, re, logging
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

from datetime import datetime

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

    # 🔍 Basis-Hashtags & Emojis
    for key, (emoji, hashtag) in mapping.items():
        if re.search(rf"\b{re.escape(key)}\b", text, re.IGNORECASE):
            emojis.append(emoji)
            hashtags.extend(hashtag.split())

    # 📅 Datum & Uhrzeit
    now = datetime.now()
    datum = now.strftime("%d.%m.%Y")
    uhrzeit = now.strftime("%H:%M")
    zeitstempel = f"🕒 {datum} – {uhrzeit}"

    # 🚈 Linienkennung extrahieren
    linien_tags = set()
    for match in re.findall(r"\bS\d{1,2}\b", text):
        linien_tags.add(f"#{match}")
    for match in re.findall(r"\bM\d{1,2}\b|\b\d{2,3}\b", text):
        linien_tags.add(f"#{match}_BVG")

    # 🧹 Duplikate entfernen & sortieren
    emojis = " ".join(OrderedDict.fromkeys(emojis))
    hashtags = " ".join(OrderedDict.fromkeys(list(linien_tags) + hashtags + ["#Berlin"]))

    return f"{emojis} {zeitstempel}\n{hashtags}".strip()

def generate_tweets(meldungen):
    threads = []
    for m in meldungen:
        beschreibung = m.get("beschreibung", "").strip()
        titel = m.get("titel") or "Störung"
        extras = enrich_message(f"{titel} {beschreibung}")
        quelle = m.get("quelle")

        # 🧭 Thread-Kopf mit Quelle und Titel
        prefix = "🚧 BVG-Meldung:" if quelle == "BVG" else "⚠️ S-Bahn-Meldung:"
        header = f"{prefix} {titel}"

        # ✂️ Beschreibung in Absätze aufteilen
        beschreibung_parts = re.split(r'(?<=[.!?])\s+', beschreibung)
        beschreibung_parts = [part.strip() for part in beschreibung_parts if part.strip()]

        # 🧵 Thread zusammenbauen
        thread = [header]
        for i, part in enumerate(beschreibung_parts, start=1):
            tweet = f"📝 ({i}/{len(beschreibung_parts)}) {part}"
            if len(tweet) > 280:
                tweet = tweet[:277] + "…"  # Kürzen, falls nötig
            thread.append(tweet)

        # 🏁 Abschluss-Tweet mit Emojis & Hashtags
        if extras:
            thread.append(f"📌 {extras}")

        threads.append(thread)

    return threads
