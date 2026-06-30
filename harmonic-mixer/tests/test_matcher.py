"""Tests for the matching engine."""

import pytest
from harmonic_mixer.matcher import TrackInfo, find_matches


def _track(path: str, bpm: float | None, camelot: str | None) -> TrackInfo:
    return TrackInfo(path=path, artist=None, title=path, bpm=bpm, camelot_key=camelot)


SOURCE = _track("source.mp3", 128.0, "5B")  # C major, 128 BPM


class TestFindMatches:
    def test_same_key_included(self):
        candidate = _track("a.mp3", 128.0, "5B")
        results = find_matches(SOURCE, [candidate])
        assert len(results) == 1

    def test_relative_minor_included(self):
        candidate = _track("a.mp3", 128.0, "5A")  # A minor
        results = find_matches(SOURCE, [candidate])
        assert len(results) == 1

    def test_adjacent_key_included(self):
        candidate = _track("a.mp3", 128.0, "6B")  # G major
        results = find_matches(SOURCE, [candidate])
        assert len(results) == 1

    def test_incompatible_key_excluded(self):
        candidate = _track("a.mp3", 128.0, "1B")  # Ab major — not compatible with 5B
        results = find_matches(SOURCE, [candidate])
        assert len(results) == 0

    def test_bpm_outside_tolerance_excluded(self):
        candidate = _track("a.mp3", 140.0, "5B")  # 140 BPM is >6% away from 128
        results = find_matches(SOURCE, [candidate], bpm_tolerance=0.06)
        assert len(results) == 0

    def test_bpm_within_tolerance_included(self):
        candidate = _track("a.mp3", 130.0, "5B")  # ~1.5% away
        results = find_matches(SOURCE, [candidate], bpm_tolerance=0.06)
        assert len(results) == 1

    def test_source_excluded_from_results(self):
        results = find_matches(SOURCE, [SOURCE])
        assert len(results) == 0

    def test_sorted_by_score_descending(self):
        same_key = _track("same.mp3", 128.0, "5B")
        adjacent = _track("adj.mp3", 128.0, "6B")
        results = find_matches(SOURCE, [adjacent, same_key])
        assert results[0].track.path == "same.mp3"

    def test_no_key_on_source_returns_empty(self):
        source = _track("src.mp3", 128.0, None)
        candidate = _track("a.mp3", 128.0, "5B")
        results = find_matches(source, [candidate])
        assert results == []

    def test_custom_bpm_tolerance(self):
        candidate = _track("a.mp3", 135.0, "5B")  # ~5.5% from 128
        assert len(find_matches(SOURCE, [candidate], bpm_tolerance=0.06)) == 1
        assert len(find_matches(SOURCE, [candidate], bpm_tolerance=0.04)) == 0

    def test_multiple_results_ranked(self):
        tracks = [
            _track("adj.mp3", 127.0, "4B"),
            _track("same.mp3", 128.5, "5B"),
            _track("rel.mp3", 126.0, "5A"),
            _track("bad_key.mp3", 128.0, "9B"),  # incompatible
        ]
        results = find_matches(SOURCE, tracks)
        assert len(results) == 3
        assert all(r.compatibility_score >= 0 for r in results)
