"""SQLite persistence layer."""

from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from .matcher import TrackInfo

SCHEMA = """
CREATE TABLE IF NOT EXISTS tracks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    path         TEXT    NOT NULL UNIQUE,
    mtime        REAL    NOT NULL,
    file_size    INTEGER NOT NULL,
    artist       TEXT,
    title        TEXT,
    bpm          REAL,
    key_name     TEXT,
    camelot_key  TEXT,
    tag_source   TEXT,
    analyzed_at  TEXT    NOT NULL
);
"""


@dataclass
class TrackRow:
    id: int | None
    path: str
    mtime: float
    file_size: int
    artist: str | None
    title: str | None
    bpm: float | None
    key_name: str | None
    camelot_key: str | None
    tag_source: str | None
    analyzed_at: str


class Database:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "Database":
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected; use as context manager or call connect()")
        return self._conn

    def is_cached(self, path: str, mtime: float, file_size: int) -> bool:
        row = self.conn.execute(
            "SELECT mtime, file_size FROM tracks WHERE path = ?", (path,)
        ).fetchone()
        if row is None:
            return False
        return float(row["mtime"]) == mtime and int(row["file_size"]) == file_size

    def upsert(self, row: TrackRow) -> None:
        self.conn.execute(
            """
            INSERT INTO tracks (path, mtime, file_size, artist, title, bpm,
                                key_name, camelot_key, tag_source, analyzed_at)
            VALUES (:path, :mtime, :file_size, :artist, :title, :bpm,
                    :key_name, :camelot_key, :tag_source, :analyzed_at)
            ON CONFLICT(path) DO UPDATE SET
                mtime       = excluded.mtime,
                file_size   = excluded.file_size,
                artist      = excluded.artist,
                title       = excluded.title,
                bpm         = excluded.bpm,
                key_name    = excluded.key_name,
                camelot_key = excluded.camelot_key,
                tag_source  = excluded.tag_source,
                analyzed_at = excluded.analyzed_at
            """,
            {
                "path": row.path,
                "mtime": row.mtime,
                "file_size": row.file_size,
                "artist": row.artist,
                "title": row.title,
                "bpm": row.bpm,
                "key_name": row.key_name,
                "camelot_key": row.camelot_key,
                "tag_source": row.tag_source,
                "analyzed_at": row.analyzed_at,
            },
        )
        self.conn.commit()

    def all_tracks(self) -> list[TrackRow]:
        rows = self.conn.execute("SELECT * FROM tracks ORDER BY artist, title").fetchall()
        return [_row_to_dataclass(r) for r in rows]

    def find_by_path(self, path: str) -> TrackRow | None:
        row = self.conn.execute("SELECT * FROM tracks WHERE path = ?", (path,)).fetchone()
        return _row_to_dataclass(row) if row else None

    def fuzzy_find(self, query: str) -> list[TrackRow]:
        pattern = f"%{query}%"
        rows = self.conn.execute(
            "SELECT * FROM tracks WHERE path LIKE ? OR title LIKE ? OR artist LIKE ?",
            (pattern, pattern, pattern),
        ).fetchall()
        return [_row_to_dataclass(r) for r in rows]

    def stats(self) -> dict[str, object]:
        total = self.conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        bpm_row = self.conn.execute(
            "SELECT MIN(bpm), MAX(bpm) FROM tracks WHERE bpm IS NOT NULL"
        ).fetchone()
        key_rows = self.conn.execute(
            "SELECT camelot_key, COUNT(*) as cnt FROM tracks "
            "WHERE camelot_key IS NOT NULL GROUP BY camelot_key ORDER BY cnt DESC"
        ).fetchall()
        return {
            "total": total,
            "bpm_min": bpm_row[0],
            "bpm_max": bpm_row[1],
            "key_distribution": {r[0]: r[1] for r in key_rows},
        }


def _row_to_dataclass(row: sqlite3.Row) -> TrackRow:
    return TrackRow(
        id=row["id"],
        path=row["path"],
        mtime=row["mtime"],
        file_size=row["file_size"],
        artist=row["artist"],
        title=row["title"],
        bpm=row["bpm"],
        key_name=row["key_name"],
        camelot_key=row["camelot_key"],
        tag_source=row["tag_source"],
        analyzed_at=row["analyzed_at"],
    )


def row_to_track_info(row: TrackRow) -> TrackInfo:
    return TrackInfo(
        path=row.path,
        artist=row.artist,
        title=row.title,
        bpm=row.bpm,
        camelot_key=row.camelot_key,
    )


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
