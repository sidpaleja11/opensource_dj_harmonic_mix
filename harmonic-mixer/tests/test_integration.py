"""
Integration test: scan → database → suggest flow using stub analyzer.

No real audio files needed — the stub analyzer returns fixed results.
"""

from __future__ import annotations
import tempfile
from pathlib import Path

import pytest

from harmonic_mixer.analyzer import Analyzer, AnalysisResult
from harmonic_mixer.database import Database, row_to_track_info
from harmonic_mixer.matcher import find_matches
from harmonic_mixer.scanner import scan_folder


class StubAnalyzer:
    """Returns a deterministic result based on the file name."""

    _MAP = {
        "track_a.mp3": AnalysisResult(bpm=128.0, pitch_class=0, mode=0),   # C major, 5B
        "track_b.mp3": AnalysisResult(bpm=130.0, pitch_class=9, mode=1),   # A minor, 5A (compat)
        "track_c.mp3": AnalysisResult(bpm=127.0, pitch_class=7, mode=0),   # G major, 6B (compat)
        "track_d.mp3": AnalysisResult(bpm=128.0, pitch_class=3, mode=0),   # Eb major, 2B (not compat)
    }

    def analyze(self, path: Path) -> AnalysisResult | None:
        return self._MAP.get(path.name)


@pytest.fixture()
def temp_library(tmp_path: Path) -> Path:
    """Create fake audio files (empty, just for path-based lookup)."""
    for name in StubAnalyzer._MAP:
        (tmp_path / name).touch()
    return tmp_path


@pytest.fixture()
def populated_db(tmp_path: Path, temp_library: Path) -> Database:
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    scan_folder(temp_library, db, analyzer=StubAnalyzer())
    return db


def test_scan_populates_all_tracks(populated_db: Database) -> None:
    rows = populated_db.all_tracks()
    assert len(rows) == 4


def test_camelot_keys_stored_correctly(populated_db: Database) -> None:
    rows = {r.title: r for r in populated_db.all_tracks()}
    assert rows["track_a"].camelot_key == "5B"
    assert rows["track_b"].camelot_key == "5A"
    assert rows["track_c"].camelot_key == "6B"
    assert rows["track_d"].camelot_key == "2B"


def test_suggest_returns_compatible_tracks(populated_db: Database) -> None:
    rows = populated_db.all_tracks()
    source = next(r for r in rows if r.title == "track_a")
    candidates = [row_to_track_info(r) for r in rows]
    source_info = row_to_track_info(source)

    results = find_matches(source_info, candidates, bpm_tolerance=0.06)
    result_titles = {m.track.title for m in results}

    # track_b (5A) and track_c (6B) are compatible; track_d (2B) is not
    assert "track_b" in result_titles
    assert "track_c" in result_titles
    assert "track_d" not in result_titles


def test_rescanning_uses_cache(populated_db: Database, temp_library: Path) -> None:
    total, cached, analyzed = scan_folder(
        temp_library, populated_db, analyzer=StubAnalyzer()
    )
    assert cached == 4
    assert analyzed == 0


def test_fuzzy_find(populated_db: Database) -> None:
    results = populated_db.fuzzy_find("track_b")
    assert len(results) == 1
    assert results[0].camelot_key == "5A"


def test_stats(populated_db: Database) -> None:
    s = populated_db.stats()
    assert s["total"] == 4
    assert s["bpm_min"] == pytest.approx(127.0)
    assert s["bpm_max"] == pytest.approx(130.0)
    assert "5B" in s["key_distribution"]
