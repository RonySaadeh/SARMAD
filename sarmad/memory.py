import sqlite3
import time
from contextlib import contextmanager

from sarmad import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS facts (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at REAL NOT NULL
);
"""


@contextmanager
def _connect():
    conn = sqlite3.connect(config.MEMORY_DB_PATH)
    try:
        conn.executescript(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def save_message(role: str, content: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
            (role, content, time.time()),
        )


def recent_history(limit: int = 20) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [{"role": role, "content": content} for role, content in reversed(rows)]


def remember_fact(key: str, value: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO facts (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, value, time.time()),
        )


def recall_fact(key: str) -> str | None:
    with _connect() as conn:
        row = conn.execute("SELECT value FROM facts WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def all_facts() -> dict[str, str]:
    with _connect() as conn:
        rows = conn.execute("SELECT key, value FROM facts ORDER BY key").fetchall()
    return dict(rows)
