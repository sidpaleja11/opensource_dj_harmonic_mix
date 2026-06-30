# harmonic-mixer

A Python CLI tool that scans your local music library, extracts BPM and musical key from each track, and suggests harmonically compatible tracks for DJ transitions using the **Camelot Wheel** system.

Works entirely offline on audio files you already own. No streaming, no downloads.

---

## What it does

1. **Scans** a folder of audio files (`.mp3`, `.flac`, `.wav`, `.aiff`, `.m4a`) recursively.
2. **Reads embedded tags** first — tracks already tagged by Rekordbox, Serato, or Mixed In Key are used as-is.
3. **Analyzes** untagged tracks with [librosa](https://librosa.org/) to estimate BPM and musical key.
4. **Caches** results in a local SQLite database so re-scanning is fast.
5. **Suggests** harmonically compatible tracks for any given track, ranked by key compatibility and BPM closeness.

---

## The Camelot Wheel

The Camelot Easymix system maps all 24 musical keys onto a clock face numbered 1–12:

- **B keys** (e.g. `5B`) = **major** keys
- **A keys** (e.g. `5A`) = **minor** keys

Compatible transitions are:
| Relationship | Example | Effect |
|---|---|---|
| Same key | `5B` → `5B` | Perfect match |
| Relative major/minor | `5B` → `5A` | Same notes, different feel |
| Adjacent number | `5B` → `6B` or `4B` | One step on the circle of fifths |

```
         12B (Db)
    11B ─────── 1B (Ab)
   (F#)           
  10B              2B (Eb)
  (B)               
   9B               3B (Bb)
   (E)              
    8B ─────── 4B (F)
         7B (D)
             5B (C)  6B (G)
```

---

## Install

Requires Python 3.11+.

```bash
cd harmonic-mixer
pip install -e ".[dev]"
```

For audio analysis, librosa requires `ffmpeg` or `soundfile` for non-WAV formats:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

---

## Usage

All commands accept `--db <path>` to specify a custom database location (default: `harmonic_mixer.db` in the current directory), or set the `HARMONIC_MIXER_DB` environment variable.

### Scan a folder

```bash
harmonic-mixer scan ~/Music/DJ-Sets
```

Shows a progress bar. Tracks are only re-analyzed if the file changes.

### List all tracks

```bash
harmonic-mixer list
```

Output:

```
 #   Artist          Title              BPM    Key           Camelot  Source
 1   Bicep           Glue              128.0   A minor       5A       tag
 2   Four Tet        Baby              120.0   C major       5B       analyzed
 ...
```

### Get suggestions for a track

```bash
harmonic-mixer suggest "Glue"
# or by path:
harmonic-mixer suggest ~/Music/DJ-Sets/bicep-glue.mp3
```

Output:

```
Suggestions for: Bicep — Glue
Key: 5A  BPM: 128.0

 Score  Artist      Title        BPM    Camelot  ΔBPM
 0.97   Four Tet    Baby        120.0   5B       ±8.0
 0.91   Caribou     Can't Do    126.0   4A       ±2.0
 ...
```

Use `--bpm-tol` to widen or narrow the BPM window (default 6%):

```bash
harmonic-mixer suggest "Glue" --bpm-tol 0.10
```

### Library stats

```bash
harmonic-mixer stats
```

---

## Running tests

```bash
pytest
# with coverage:
pytest --cov=harmonic_mixer --cov-report=term-missing
```

---

## Architecture

| Module | Responsibility |
|---|---|
| `camelot.py` | Camelot wheel constants and key detection — pure functions, no I/O |
| `matcher.py` | Harmonic matching engine — pure functions, no I/O |
| `database.py` | SQLite read/write layer |
| `tagger.py` | mutagen tag reading and key-tag parsing |
| `analyzer.py` | librosa audio analysis behind a `Protocol` (swappable) |
| `scanner.py` | Orchestrates file scanning, tagging, analysis, and caching |
| `cli.py` | Click CLI commands |

The audio analyzer is pluggable: pass any object implementing `analyze(path) -> AnalysisResult | None` to `scan_folder`. This makes it easy to swap in a higher-quality key detection algorithm later without touching the rest of the pipeline.

---

## License

MIT
