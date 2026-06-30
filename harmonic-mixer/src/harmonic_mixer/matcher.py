from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from .camelot import compatible_keys


@dataclass(frozen=True)
class TrackInfo:
    path: str
    artist: str | None
    title: str | None
    bpm: float | None
    camelot_key: str | None


@dataclass(frozen=True)
class Match:
    track: TrackInfo
    key_compatible: bool
    bpm_distance: float  # absolute difference in BPM
    compatibility_score: float  # higher is better


def _bpm_ratio(bpm_a: float, bpm_b: float) -> float:
    """Return the percentage difference between two BPMs (as a fraction 0-1)."""
    if bpm_a <= 0 or bpm_b <= 0:
        return 1.0
    lo, hi = sorted([bpm_a, bpm_b])
    return (hi - lo) / lo


def find_matches(
    source: TrackInfo,
    candidates: list[TrackInfo],
    bpm_tolerance: float = 0.06,
) -> list[Match]:
    """
    Return candidates that are harmonically compatible with *source*.

    Args:
        source: The reference track.
        candidates: Pool of tracks to search (source itself is excluded).
        bpm_tolerance: Maximum BPM deviation as a fraction (default 0.06 = 6%).

    Returns:
        List of Match objects sorted by compatibility_score descending.
    """
    if source.camelot_key is None:
        return []

    compat_keys = set(compatible_keys(source.camelot_key))
    results: list[Match] = []

    for track in candidates:
        if track.path == source.path:
            continue

        key_ok = track.camelot_key in compat_keys if track.camelot_key else False

        bpm_dist = 0.0
        bpm_ok = True
        if source.bpm and track.bpm:
            ratio = _bpm_ratio(source.bpm, track.bpm)
            bpm_dist = abs(source.bpm - track.bpm)
            bpm_ok = ratio <= bpm_tolerance
        elif source.bpm or track.bpm:
            # one side has BPM, other doesn't — can't filter, penalize nothing
            bpm_dist = 0.0
            bpm_ok = True

        if not (key_ok and bpm_ok):
            continue

        if track.camelot_key == source.camelot_key:
            key_score = 1.0
        elif track.camelot_key and track.camelot_key[-1] != source.camelot_key[-1]:
            # relative major/minor (same number, different letter) — very harmonic
            key_score = 0.9
        else:
            key_score = 0.7  # adjacent number

        bpm_score = 1.0 - (bpm_dist / (source.bpm * bpm_tolerance) if source.bpm else 0.0)
        score = key_score * 0.7 + max(0.0, bpm_score) * 0.3

        results.append(Match(track=track, key_compatible=True, bpm_distance=bpm_dist, compatibility_score=score))

    results.sort(key=lambda m: m.compatibility_score, reverse=True)
    return results
