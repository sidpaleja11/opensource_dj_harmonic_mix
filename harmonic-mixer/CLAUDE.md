# Harmonic Mixing Assistant

Python CLI tool that scans local audio files, extracts BPM and musical key,
stores results in SQLite, and suggests harmonically compatible DJ transitions
using the Camelot wheel system.

## Project state
- All core modules implemented and working
- 38/38 tests passing (`pytest`)
- Installed in editable mode (`pip install -e ".[dev]"`)
- CLI entry point: `harmonic-mixer` (or `python -m harmonic_mixer.cli`)

## Architecture
| Module | Role |
|---|---|
| `camelot.py` | Camelot wheel mapping + Krumhansl-Schmuckler key detection — pure functions |
| `matcher.py` | Harmonic matching engine — pure functions |
| `database.py` | SQLite layer; cache keyed on path + mtime + file_size |
| `tagger.py` | mutagen tag reading; parses Camelot / Open Key / standard notation |
| `analyzer.py` | LibrosaAnalyzer behind a `Protocol` (pluggable) |
| `scanner.py` | Orchestrates file scan → tag → analyze → cache |
| `cli.py` | Click commands: scan, list, suggest, stats |

## Key decisions
- Cache invalidation: mtime + file_size change triggers re-analysis (no full content hash for speed)
- Analyzer is a Protocol so the librosa implementation can be swapped without touching the scan loop
- Audio analysis only runs on first 120s of each track (configurable via `LibrosaAnalyzer(duration=...)`)
- BPM tolerance default is 6% (roughly the range a DJ can pitch-shift)
- Compatible keys: same Camelot code, ±1 number (same letter), same number A↔B (relative major/minor)

## CLI usage
```bash
harmonic-mixer scan ~/Music/DJ-Sets
harmonic-mixer list
harmonic-mixer suggest "track name or /path/to/file.mp3"
harmonic-mixer suggest "track" --bpm-tol 0.10
harmonic-mixer stats
harmonic-mixer --db custom.db scan ~/Music
```

## Running tests
```bash
pytest
pytest -v tests/test_camelot.py   # pure logic only (no librosa needed)
```

## Tech stack
Python 3.11+, librosa, mutagen, click, rich, sqlite3, pytest
