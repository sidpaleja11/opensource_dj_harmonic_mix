from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from harmonic_mixer.camelot import compatible_keys
from harmonic_mixer.database import Database, TrackRow
from ..deps import get_db
from ..schemas import ExportRequest, PlaylistItemOut, TrackOut

router = APIRouter(prefix="/api/playlist", tags=["playlist"])


def _row_to_out(row: TrackRow) -> TrackOut:
    assert row.id is not None
    return TrackOut(
        id=row.id,
        path=row.path,
        artist=row.artist,
        title=row.title,
        bpm=row.bpm,
        key_name=row.key_name,
        camelot_key=row.camelot_key,
        tag_source=row.tag_source,
        analyzed_at=row.analyzed_at,
    )


# ── Scoring ───────────────────────────────────────────────────────────────────

@lru_cache(maxsize=24)
def _compat_set(camelot_key: str) -> frozenset[str]:
    """Cached set of Camelot keys compatible with the given key."""
    return frozenset(compatible_keys(camelot_key))


def _key_score(a: TrackRow, b: TrackRow) -> float:
    """
    Continuous key compatibility score [0, 1].

    1.0 = same key
    0.9 = relative major/minor (same number, A↔B)
    0.8 = adjacent ±1 step on the wheel (same letter)
    0.05 = no Camelot relationship
    0.3 = one or both keys unknown
    """
    if not a.camelot_key or not b.camelot_key:
        return 0.3
    if a.camelot_key == b.camelot_key:
        return 1.0
    if b.camelot_key in _compat_set(a.camelot_key):
        num_a = int(a.camelot_key[:-1])
        num_b = int(b.camelot_key[:-1])
        return 0.9 if num_a == num_b else 0.8
    return 0.05


def _bpm_score(a: TrackRow, b: TrackRow) -> float:
    """
    Continuous BPM compatibility score [0, 1].

    Smooth piecewise decay:
      0–6%  difference → 1.0 down to 0.7  (DJ-pitch range, ideal)
      6–15% difference → 0.7 down to 0.2  (noticeable but workable energy shift)
      15%+  difference → 0.2 down to 0.0  (hard jump, should be last resort)
    """
    if not a.bpm or not b.bpm:
        return 0.5
    ratio = abs(a.bpm - b.bpm) / max(a.bpm, b.bpm)
    if ratio <= 0.06:
        return 1.0 - ratio * 5.0
    if ratio <= 0.15:
        return 0.7 - (ratio - 0.06) * (0.5 / 0.09)
    return max(0.0, 0.2 - (ratio - 0.15) * 2.0)


def _pair_score(a: TrackRow, b: TrackRow) -> float:
    """Combined score: 65% key, 35% BPM."""
    return _key_score(a, b) * 0.65 + _bpm_score(a, b) * 0.35


def _chain_score(chain: list[TrackRow]) -> float:
    return sum(_pair_score(chain[i], chain[i + 1]) for i in range(len(chain) - 1))


# ── Chain building ─────────────────────────────────────────────────────────────

def _greedy_from(start: TrackRow, rest: list[TrackRow]) -> list[TrackRow]:
    remaining = list(rest)
    chain = [start]
    while remaining:
        current = chain[-1]
        nxt = max(remaining, key=lambda r: _pair_score(current, r))
        chain.append(nxt)
        remaining.remove(nxt)
    return chain


def _two_opt(chain: list[TrackRow]) -> list[TrackRow]:
    """
    2-opt local search: try reversing every contiguous segment and keep any
    improvement. Restarts on each improvement. O(n²) per pass, fast for n ≤ 80.
    """
    n = len(chain)
    improved = True
    while improved:
        improved = False
        current_score = _chain_score(chain)
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                candidate = chain[:i] + chain[i:j + 1][::-1] + chain[j + 1:]
                if _chain_score(candidate) > current_score + 1e-9:
                    chain = candidate
                    improved = True
                    break
            if improved:
                break
    return chain


def _harmonic_chain(tracks: list[TrackRow]) -> list[TrackRow]:
    """
    Build the best harmonic ordering for a set of tracks.

    Strategy:
      1. Try every track as a starting point using a greedy nearest-neighbour
         approach with continuous key+BPM scoring (no hard filters).
      2. Keep the highest-scoring greedy result.
      3. Apply 2-opt segment-reversal to escape local optima (capped at 80
         tracks to keep latency negligible).
    """
    if len(tracks) <= 1:
        return list(tracks)

    best_chain: list[TrackRow] = []
    best_score = -1.0

    for i, start in enumerate(tracks):
        rest = tracks[:i] + tracks[i + 1:]
        candidate = _greedy_from(start, rest)
        s = _chain_score(candidate)
        if s > best_score:
            best_score = s
            best_chain = candidate

    if len(tracks) <= 80:
        best_chain = _two_opt(best_chain)

    return best_chain


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/suggest", response_model=list[PlaylistItemOut])
async def suggest_playlist(
    folder: Annotated[str, Query(max_length=1024)],
    bpm_tol: Annotated[float, Query(ge=0.01, le=0.5)] = 0.06,  # kept for API compat
    db: Database = Depends(get_db),
) -> list[PlaylistItemOut]:
    folder_path = Path(folder).resolve()
    folder_tracks = [
        t for t in db.all_tracks()
        if Path(t.path).is_relative_to(folder_path)
    ]

    if not folder_tracks:
        raise HTTPException(status_code=404, detail="No scanned tracks found in this folder")

    ordered = _harmonic_chain(folder_tracks)

    items: list[PlaylistItemOut] = []
    for i, track in enumerate(ordered):
        compatible = False
        if i > 0 and ordered[i - 1].camelot_key and track.camelot_key:
            compatible = track.camelot_key in _compat_set(ordered[i - 1].camelot_key)
        items.append(PlaylistItemOut(position=i + 1, track=_row_to_out(track), compatible=compatible))

    return items


@router.post("/export")
async def export_playlist(
    body: ExportRequest,
    db: Database = Depends(get_db),
) -> StreamingResponse:
    tracks = [r for tid in body.track_ids if (r := db.find_by_id(tid)) is not None]

    lines = ["#EXTM3U", ""]
    for row in tracks:
        if row.artist and row.title:
            label = f"{row.artist} - {row.title}"
        else:
            label = row.title or Path(row.path).stem
        lines.append(f"#EXTINF:0,{label}")
        lines.append(row.path)

    content = "\n".join(lines) + "\n"
    name = (body.name or "harmonizer-set").strip() or "harmonizer-set"

    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="audio/x-mpegurl",
        headers={"Content-Disposition": f'attachment; filename="{name}.m3u8"'},
    )
