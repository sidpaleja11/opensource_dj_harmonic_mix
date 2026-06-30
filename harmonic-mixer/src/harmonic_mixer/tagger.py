"""Read embedded metadata tags from audio files using mutagen."""

from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".wav", ".aiff", ".aif", ".m4a"}


@dataclass
class TagData:
    artist: str | None = None
    title: str | None = None
    bpm: float | None = None
    key_name: str | None = None  # raw tag value, e.g. "8A", "Cm", "C minor"


def read_tags(path: Path) -> TagData | None:
    """
    Read metadata tags from *path*.

    Returns None if the file cannot be read or is an unsupported format.
    BPM and key are returned only when present and parseable.
    """
    try:
        from mutagen import File as MutagenFile

        f = MutagenFile(path, easy=True)
        if f is None:
            return TagData()

        def _first(key: str) -> str | None:
            val = f.get(key)
            return val[0].strip() if val else None

        artist = _first("artist") or _first("albumartist")
        title = _first("title")

        bpm: float | None = None
        raw_bpm = _first("bpm")
        if raw_bpm:
            try:
                bpm = float(raw_bpm)
            except ValueError:
                log.debug("Unparseable BPM tag %r in %s", raw_bpm, path)

        # Key tags vary by tagger: Rekordbox uses "initialkey", easy mode maps it;
        # mutagen's Easy API exposes it as "initialkey" for MP3s.
        key_name = _first("initialkey") or _first("key")

        return TagData(artist=artist, title=title, bpm=bpm, key_name=key_name)

    except Exception as exc:
        log.warning("Could not read tags from %s: %s", path, exc)
        return None


def parse_key_tag(raw: str) -> tuple[int, int] | None:
    """
    Parse a raw key tag into (pitch_class, mode).

    Handles common formats:
      - Camelot: "8A", "5B", "12A"
      - Open Key: "4d", "9m"
      - Standard: "Am", "C#m", "Db", "F# minor", "A major"

    Returns None if the format is unrecognised.
    """
    from .camelot import _FROM_CAMELOT, PITCH_CLASS_NAMES

    raw = raw.strip()

    # Camelot notation (e.g. "8A", "12B")
    upper = raw.upper()
    if upper in _FROM_CAMELOT:
        return _FROM_CAMELOT[upper]

    # Open Key notation (e.g. "4d" major, "9m" minor) — map to Camelot first
    # Open Key 1d=1B, 1m=1A ... 12d=12B, 12m=12A
    import re
    ok_match = re.fullmatch(r"(\d{1,2})([dDmM])", raw)
    if ok_match:
        num = int(ok_match.group(1))
        letter = "B" if ok_match.group(2).lower() == "d" else "A"
        camelot = f"{num}{letter}"
        if camelot in _FROM_CAMELOT:
            return _FROM_CAMELOT[camelot]

    # Standard notation e.g. "Am", "C#m", "Db", "F# major", "A minor"
    std_match = re.match(
        r"^([A-Ga-g][#b♭♯]?)\s*(m(?:in(?:or)?)?|maj(?:or)?)?$", raw
    )
    if std_match:
        note_str = std_match.group(1).capitalize().replace("♯", "#").replace("♭", "b")
        quality = (std_match.group(2) or "").lower()
        mode = 1 if quality.startswith("m") and not quality.startswith("maj") else 0

        # Normalise enharmonics
        note_str = note_str.replace("Db", "C#").replace("Eb", "D#").replace("Gb", "F#") \
                           .replace("Ab", "G#").replace("Bb", "A#")

        if note_str in PITCH_CLASS_NAMES:
            pc = PITCH_CLASS_NAMES.index(note_str)
            return pc, mode

    return None
