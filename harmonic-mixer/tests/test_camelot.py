"""Tests for Camelot wheel pure logic."""

import pytest
from harmonic_mixer.camelot import (
    pitch_mode_to_camelot,
    camelot_to_pitch_mode,
    compatible_keys,
    detect_key_from_chroma,
    key_name,
)


class TestPitchModeToCalmelot:
    @pytest.mark.parametrize("pc,mode,expected", [
        (0, 0, "5B"),   # C major
        (9, 1, "5A"),   # A minor (relative of C major)
        (5, 1, "1A"),   # F minor
        (8, 0, "1B"),   # Ab major
        (1, 0, "12B"),  # Db major
        (10, 1, "12A"), # Bb minor
        (11, 0, "10B"), # B major
        (11, 1, "7A"),  # B minor
    ])
    def test_known_keys(self, pc, mode, expected):
        assert pitch_mode_to_camelot(pc, mode) == expected

    def test_all_24_keys_round_trip(self):
        for pc in range(12):
            for mode in range(2):
                code = pitch_mode_to_camelot(pc, mode)
                back_pc, back_mode = camelot_to_pitch_mode(code)
                assert (back_pc, back_mode) == (pc, mode)


class TestCompatibleKeys:
    def test_same_key_included(self):
        assert "5B" in compatible_keys("5B")

    def test_relative_major_minor(self):
        # 5B = C major, 5A = A minor — relative pair
        assert "5A" in compatible_keys("5B")
        assert "5B" in compatible_keys("5A")

    def test_adjacent_numbers(self):
        # ±1 on the wheel, same letter
        result = compatible_keys("5B")
        assert "6B" in result  # +1
        assert "4B" in result  # -1

    def test_wrap_around_at_12(self):
        result = compatible_keys("12B")
        assert "1B" in result   # wraps to 1
        assert "11B" in result  # -1

    def test_wrap_around_at_1(self):
        result = compatible_keys("1A")
        assert "12A" in result  # wraps back
        assert "2A" in result

    def test_returns_four_keys(self):
        # Always 4 unique valid codes (same, relative, +1, -1)
        result = compatible_keys("8A")
        assert len(result) == 4

    def test_no_duplicates(self):
        for code in ["1A", "6B", "12A", "11B"]:
            result = compatible_keys(code)
            assert len(result) == len(set(result))


class TestKeyName:
    def test_major(self):
        assert key_name(0, 0) == "C major"

    def test_minor(self):
        assert key_name(9, 1) == "A minor"

    def test_sharp(self):
        assert key_name(1, 0) == "C# major"


class TestDetectKeyFromChroma:
    def test_c_major_profile(self):
        # C major chroma: C and E and G are prominent (indices 0, 4, 7)
        chroma = [0.0] * 12
        chroma[0] = 1.0   # C
        chroma[4] = 0.7   # E
        chroma[7] = 0.8   # G
        pc, mode = detect_key_from_chroma(chroma)
        assert pc == 0 and mode == 0, f"Expected C major, got {key_name(pc, mode)}"

    def test_a_minor_profile(self):
        # A minor: A, C, E prominent
        chroma = [0.0] * 12
        chroma[9] = 1.0   # A
        chroma[0] = 0.7   # C
        chroma[4] = 0.6   # E
        pc, mode = detect_key_from_chroma(chroma)
        assert pc == 9 and mode == 1, f"Expected A minor, got {key_name(pc, mode)}"
