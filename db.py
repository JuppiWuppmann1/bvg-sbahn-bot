import sqlite3
import datetime

DB_FILE = "meldungen.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS meldungen (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT UNIQUE)")
    conn.commit()
    conn.close()

def is_new_message(text: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM meldungen WHERE text = ?", (text,))
    exists = c.fetchone()
    conn.close()
    return exists is None

def save_message(text: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO meldungen (text) VALUES (?)", (text,))
    conn.commit()
    conn.close()

def reset_db_if_monday():
    if datetime.datetime.today().weekday() == 0:  # Montag = 0
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM meldungen")
        conn.commit()
        conn.close()
        print("🧹 Datenbank wurde zurückgesetzt (Wochenstart)")
