"""
Audio analysis — pluggable interface behind a Protocol.

The default implementation uses librosa. Swap it out by passing a different
Analyzer instance to the scanner.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

log = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    bpm: float | None
    pitch_class: int | None  # 0-11
    mode: int | None         # 0=major, 1=minor


class Analyzer(Protocol):
    def analyze(self, path: Path) -> AnalysisResult | None:
        """Analyze *path* and return BPM + key, or None on failure."""
        ...


class LibrosaAnalyzer:
    """Default analyzer using librosa beat tracking and chroma key detection."""

    def __init__(self, sr: int = 22050, duration: float | None = 120.0) -> None:
        self.sr = sr
        # Analyse only the first *duration* seconds for speed (None = whole file)
        self.duration = duration

    def analyze(self, path: Path) -> AnalysisResult | None:
        try:
            import librosa
            import numpy as np
            from .camelot import detect_key_from_chroma

            y, sr = librosa.load(str(path), sr=self.sr, mono=True, duration=self.duration)

            # BPM
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            bpm = float(np.atleast_1d(tempo)[0])

            # Key via chroma (use harmonic component to reduce percussion influence)
            y_harm = librosa.effects.harmonic(y)
            chroma = librosa.feature.chroma_cqt(y=y_harm, sr=sr)
            chroma_mean = chroma.mean(axis=1)
            pitch_class, mode = detect_key_from_chroma(chroma_mean)

            return AnalysisResult(bpm=bpm, pitch_class=pitch_class, mode=mode)

        except Exception as exc:
            log.warning("librosa analysis failed for %s: %s", path, exc)
            return None
