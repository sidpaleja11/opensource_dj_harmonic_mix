from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Callable

from .analyzer import Analyzer, LibrosaAnalyzer, AnalysisResult
from .camelot import pitch_mode_to_camelot, key_name as make_key_name
from .database import Database, TrackRow, now_utc
from .tagger import SUPPORTED_EXTENSIONS, TagData, read_tags, parse_key_tag

log = logging.getLogger(__name__)


def find_audio_files(root: Path) -> list[Path]:
    """Recursively find all supported audio files under *root*."""
    files = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(p)
    return sorted(files)


def scan_folder(
    root: Path,
    db: Database,
    *,
    analyzer: Analyzer | None = None,
    progress: Callable[[str], None] | None = None,
) -> tuple[int, int, int]:
    """
    Scan *root*, populate *db*, and return (total, cached, analyzed).

    Args:
        root: Directory to scan recursively.
        db: Connected Database instance.
        analyzer: Audio analysis implementation. Defaults to LibrosaAnalyzer.
        progress: Optional callback receiving the current file path string.

    Returns:
        (total, cached, analyzed) counts.
    """
    if analyzer is None:
        analyzer = LibrosaAnalyzer()

    files = find_audio_files(root)
    total = len(files)
    cached = 0
    analyzed = 0

    for path in files:
        if progress:
            progress(str(path))

        try:
            stat = path.stat()
        except OSError as exc:
            log.warning("Cannot stat %s: %s", path, exc)
            continue

        mtime = stat.st_mtime
        file_size = stat.st_size

        if db.is_cached(str(path), mtime, file_size):
            cached += 1
            continue

        row = _process_file(path, mtime, file_size, analyzer)
        if row:
            db.upsert(row)
            analyzed += 1

    return total, cached, analyzed


def _process_file(
    path: Path,
    mtime: float,
    file_size: int,
    analyzer: Analyzer,
) -> TrackRow | None:
    tags: TagData = read_tags(path) or TagData()

    bpm: float | None = tags.bpm
    pitch_class: int | None = None
    mode: int | None = None
    tag_source = "tag"

    # Try to parse key from tag
    if tags.key_name:
        parsed = parse_key_tag(tags.key_name)
        if parsed:
            pitch_class, mode = parsed

    # Fall back to audio analysis for missing BPM or key
    if bpm is None or pitch_class is None:
        result: AnalysisResult | None = None
        try:
            result = analyzer.analyze(path)
        except Exception as exc:
            log.warning("Analysis failed for %s: %s", path, exc)

        if result:
            if bpm is None and result.bpm is not None:
                bpm = result.bpm
                tag_source = "analyzed"
            if pitch_class is None and result.pitch_class is not None:
                pitch_class = result.pitch_class
                mode = result.mode
                tag_source = "analyzed"

    camelot_key: str | None = None
    key_name_str: str | None = None
    if pitch_class is not None and mode is not None:
        camelot_key = pitch_mode_to_camelot(pitch_class, mode)
        key_name_str = make_key_name(pitch_class, mode)

    return TrackRow(
        id=None,
        path=str(path),
        mtime=mtime,
        file_size=file_size,
        artist=tags.artist,
        title=tags.title or path.stem,
        bpm=bpm,
        key_name=key_name_str,
        camelot_key=camelot_key,
        tag_source=tag_source,
        analyzed_at=now_utc(),
    )
