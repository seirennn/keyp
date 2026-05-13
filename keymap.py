"""Key transposition — octave shift (row-based) and semitone shift.

Maps input notation characters to different physical keyboard keys
based on shift settings.  Works with any virtual piano that follows
standard QWERTY-row octave layout.
"""

from typing import Dict

# QWERTY rows from lowest to highest pitch on a virtual piano.
# Each row is one "octave".  Columns align roughly by finger position.
_OCTAVE_ROWS = [
    list("zxcvbnm,./"),       # row 0 — bottom (lowest octave)
    list("asdfghjkl;'"),      # row 1 — home
    list("qwertyuiop[]"),     # row 2 — top
    list("1234567890-="),     # row 3 — numbers (highest octave)
]

# Full ordered key list (all rows flattened, including in-between keys
# for semitone shifts).  Aligned to match typical virtual piano layout.
# Each entry is a keyboard key; stepping by 1 = one semitone up.
_PIANO_KEYS = [
    # Octave 0 (bottom row + sharps)
    "z",  # C
    "s",  # C#
    "x",  # D
    "d",  # D#
    "c",  # E
    "v",  # F
    "g",  # F#
    "b",  # G
    "h",  # G#
    "n",  # A
    "j",  # A#
    "m",  # B
    # Octave 1 (home row + sharps)
    "q",  # C
    "2",  # C#
    "w",  # D
    "3",  # D#
    "e",  # E
    "4",  # F
    "r",  # F#
    "5",  # G
    "t",  # G#
    "6",  # A
    "y",  # A#
    "7",  # B
    # Octave 2 (top row + sharps)
    "i",  # C
    "9",  # C#
    "o",  # D
    "0",  # D#
    "p",  # E
    "[",  # F
    "=",  # F#
    "]",  # G
    "\\", # G#
    # No more keys on standard QWERTY
]


def build_key_map(octave_shift: int, semitone_shift: int) -> Dict[str, str]:
    """Return dict mapping every known key → transposed key.

    Keys not found in the layout are passed through unchanged.
    An empty dict return means no mapping is needed (no-op).
    """
    if octave_shift == 0 and semitone_shift == 0:
        return {}

    mapping: Dict[str, str] = {}

    # Semitone shift: shift within the full ordered list
    if semitone_shift != 0:
        for idx, key in enumerate(_PIANO_KEYS):
            dst = idx + semitone_shift
            if 0 <= dst < len(_PIANO_KEYS):
                mapping[key] = _PIANO_KEYS[dst]
            else:
                mapping[key] = key  # out of range, keep original
    else:
        for key in _PIANO_KEYS:
            mapping[key] = key

    # Octave shift: shift between rows (overrides semitone mapping
    # where both apply — octave shift is the larger movement)
    if octave_shift != 0:
        num_rows = len(_OCTAVE_ROWS)
        for src_row_idx, src_row in enumerate(_OCTAVE_ROWS):
            dst_row_idx = src_row_idx + octave_shift
            if 0 <= dst_row_idx < num_rows:
                dst_row = _OCTAVE_ROWS[dst_row_idx]
                for col, key in enumerate(src_row):
                    if col < len(dst_row):
                        mapping[key] = dst_row[col]
                    else:
                        mapping[key] = key
            else:
                for key in src_row:
                    mapping[key] = key

    # Remove identity mappings (no need to translate)
    return {k: v for k, v in mapping.items() if k != v}


def apply_map(keys: tuple, mapping: Dict[str, str]) -> tuple:
    """Apply key mapping to a tuple of keys (for chords)."""
    if not mapping:
        return keys
    return tuple(mapping.get(k, k) for k in keys)
