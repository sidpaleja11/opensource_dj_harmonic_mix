from __future__ import annotations

PITCH_CLASS_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

_TO_CAMELOT: dict[tuple[int, int], str] = {
    (0, 0): "5B",
    (1, 0): "12B",
    (2, 0): "7B",
    (3, 0): "2B",
    (4, 0): "9B",
    (5, 0): "4B",
    (6, 0): "11B",
    (7, 0): "6B",
    (8, 0): "1B",
    (9, 0): "8B",
    (10, 0): "3B",
    (11, 0): "10B",
    (0, 1): "2A",
    (1, 1): "9A",
    (2, 1): "4A",
    (3, 1): "11A",
    (4, 1): "6A",
    (5, 1): "1A",
    (6, 1): "8A",
    (7, 1): "3A",
    (8, 1): "10A",
    (9, 1): "5A",
    (10, 1): "12A",
    (11, 1): "7A",
}

_FROM_CAMELOT: dict[str, tuple[int, int]] = {v: k for k, v in _TO_CAMELOT.items()}

# Krumhansl-Schmuckler key profiles (correlation with chroma)
_MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
_MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]


def pitch_mode_to_camelot(pitch_class: int, mode: int) -> str:
    """Convert librosa-style (pitch_class 0-11, mode 0=major 1=minor) to Camelot code."""
    return _TO_CAMELOT[(pitch_class % 12, mode)]


def camelot_to_pitch_mode(camelot_key: str) -> tuple[int, int]:
    return _FROM_CAMELOT[camelot_key]


def key_name(pitch_class: int, mode: int) -> str:
    note = PITCH_CLASS_NAMES[pitch_class % 12]
    quality = "major" if mode == 0 else "minor"
    return f"{note} {quality}"


def detect_key_from_chroma(chroma_mean: list[float] | "np.ndarray") -> tuple[int, int]:
    import numpy as np

    chroma = np.array(chroma_mean, dtype=float)
    chroma = chroma - chroma.mean()

    best_score = -float("inf")
    best_pc = 0
    best_mode = 0

    for pc in range(12):
        # weight[i] = template[(i-pc)%12] so pitch class pc gets root weight
        major_rot = np.roll(_MAJOR_PROFILE, pc)
        minor_rot = np.roll(_MINOR_PROFILE, pc)

        major_profile = np.array(major_rot) - np.mean(major_rot)
        minor_profile = np.array(minor_rot) - np.mean(minor_rot)

        major_score = float(np.dot(chroma, major_profile))
        minor_score = float(np.dot(chroma, minor_profile))

        if major_score > best_score:
            best_score = major_score
            best_pc = pc
            best_mode = 0
        if minor_score > best_score:
            best_score = minor_score
            best_pc = pc
            best_mode = 1

    return best_pc, best_mode


def compatible_keys(camelot_key: str) -> list[str]:
    """
    Return all Camelot keys compatible for harmonic mixing with the given key.

    Compatible keys: same code, ±1 number (wrap around 12), same number A↔B.
    """
    number_str, letter = camelot_key[:-1], camelot_key[-1]
    number = int(number_str)
    opposite = "A" if letter == "B" else "B"

    candidates = [
        camelot_key,
        f"{number}{opposite}",
        f"{(number % 12) + 1}{letter}",
        f"{((number - 2) % 12) + 1}{letter}",
    ]
    seen: set[str] = set()
    result = []
    for k in candidates:
        if k not in seen and k in _FROM_CAMELOT:
            seen.add(k)
            result.append(k)
    return result
