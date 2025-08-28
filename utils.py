import os
import json
import re
import logging
from collections import OrderedDict
from datetime import datetime

SEEN_FILE = "seen.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)

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
        if re.search(rf"\b{re.escape(key)}\b", text, re.IGNORECASE):
            emojis.append(emoji)
            hashtags.extend(hashtag.split())

    now = datetime.now()
    datum = now.strftime("%d.%m.%Y")
    uhrzeit = now.strftime("%H:%M")
    zeitstempel = f"🕒 {datum} – {uhrzeit}"

    linien_tags = set()
    for match in re.findall(r"\bS\d{1,2}\b", text):
        linien_tags.add(f"#{match}")
    for match in re.findall(r"\bM\d{1,2}\b|\b\d{2,3}\b", text):
        linien_tags.add(f"#{match}_BVG")

    emojis = " ".join(OrderedDict.fromkeys(emojis))
    hashtags = " ".join(OrderedDict.fromkeys(list(linien_tags) + hashtags + ["#Berlin"]))

    return f"{emojis} {zeitstempel}\n{hashtags}".strip()

def extract_zeit(text: str) -> str:
    match = re.search(r"Von\s+\d{2}\.\d{2}\.\d{4}\s+\d{1,2}:\d{2}", text)
    return match.group(0) if match else ""

def generate_tweets(meldungen):
    threads = []
    for m in meldungen:
        beschreibung = m.get("beschreibung", "").strip()
        titel = m.get("titel", "").strip()
        zeit = extract_zeit(titel)
        extras = enrich_message(beschreibung)

        header = zeit if zeit else "🕒 Neue Meldung"
        beschreibung_parts = re.split(r'(?<=[.!?])\s+', beschreibung)
        beschreibung_parts = [part.strip() for part in beschreibung_parts if part.strip()]

        thread = [header]
        for i, part in enumerate(beschreibung_parts, start=1):
            tweet = f"📝 ({i}/{len(beschreibung_parts)}) {part}"
            if len(tweet) > 280:
                tweet = tweet[:277] + "…"
            thread.append(tweet)

        if extras:
            thread.append(f"📌 {extras}")

        threads.append(thread)

    return threads
