import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

DB_PATH = Path("data.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id TEXT PRIMARY KEY,
            source TEXT,
            title TEXT,
            detail TEXT,
            content_hash TEXT,
            resolved INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_all_entries() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM entries")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_entry(entry) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()

    cur.execute("""
        INSERT INTO entries (id, source, title, detail, content_hash, resolved, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 0, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            source=excluded.source,
            title=excluded.title,
            detail=excluded.detail,
            content_hash=excluded.content_hash,
            resolved=0,
            updated_at=excluded.updated_at
    """, (entry.id, entry.source, entry.title, entry.detail, entry.content_hash, now, now))

    conn.commit()
    conn.close()

def mark_resolved(entry_id: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("""
        UPDATE entries
        SET resolved = 1,
            updated_at = ?
        WHERE id = ?
    """, (now, entry_id))
    conn.commit()
    conn.close()
