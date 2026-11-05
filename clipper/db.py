"""SQLite storage for the Peezy Report clipper (stdlib only)."""
import json
import sqlite3
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT,
    source_file TEXT,
    rights_confirmed INTEGER NOT NULL DEFAULT 0,
    opus_project_id TEXT,
    opus_mode TEXT NOT NULL,            -- 'live' or 'mock'
    status TEXT NOT NULL,               -- submitted | processing | ready | failed
    error TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS clips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    opus_clip_id TEXT,
    title TEXT,
    start_s REAL, end_s REAL,
    score REAL,
    transcript TEXT,
    file_path TEXT,
    remote_url TEXT,
    selected INTEGER NOT NULL DEFAULT 0,
    is_mock INTEGER NOT NULL DEFAULT 0,
    source_kind TEXT,                   -- raw_cut | opus_render | mock
    subtitles TEXT DEFAULT ''           -- clip-relative SRT from OpusClip word timings
);
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id INTEGER NOT NULL REFERENCES clips(id),
    talking_points TEXT DEFAULT '',
    reaction_file TEXT,
    layout TEXT NOT NULL DEFAULT 'stack',   -- stack | sequence | clip_only
    subtitles TEXT DEFAULT '',
    hook TEXT DEFAULT '', title TEXT DEFAULT '', caption TEXT DEFAULT '',
    hashtags TEXT DEFAULT '',
    drafts_json TEXT DEFAULT '{}',
    output_file TEXT,
    output_sha256 TEXT,
    render_status TEXT NOT NULL DEFAULT 'draft',  -- draft | rendering | rendered | failed
    render_error TEXT,
    approved INTEGER NOT NULL DEFAULT 0,
    approved_fingerprint TEXT,
    approved_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL REFERENCES videos(id),
    platform TEXT NOT NULL,              -- instagram | tiktok | youtube
    content_fingerprint TEXT NOT NULL,
    provider TEXT NOT NULL,
    is_mock INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,                -- submitting | pending | published | failed | needs_action | mock_published
    request_id TEXT,
    provider_post_id TEXT,
    post_url TEXT,
    error TEXT,
    raw_response TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (content_fingerprint, platform, is_mock)
);
"""


class DB:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        for col in ("source_kind TEXT", "subtitles TEXT DEFAULT ''"):  # upgrade older DBs
            try:
                self.conn.execute(f"ALTER TABLE clips ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass
        self.conn.commit()

    def execute(self, sql, params=()):
        with self._lock:
            cur = self.conn.execute(sql, params)
            self.conn.commit()
            return cur.lastrowid

    def one(self, sql, params=()):
        with self._lock:
            row = self.conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def all(self, sql, params=()):
        with self._lock:
            return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def update(self, table, row_id, **fields):
        if not fields:
            return
        cols = ", ".join(f"{k} = ?" for k in fields)
        self.execute(f"UPDATE {table} SET {cols} WHERE id = ?", (*fields.values(), row_id))


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False)
