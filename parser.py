"""Character-by-character Virtual Piano notation parser.

States: NORMAL, IN_CHORD.  Single-pass O(n) with no regex.
"""

from dataclasses import dataclass, field
from typing import List, Union

from tokens import NoteToken, ChordToken, PauseToken


@dataclass
class ParseResult:
    tokens: List[Union[NoteToken, ChordToken, PauseToken]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def parse(text: str) -> ParseResult:
    """Parse Virtual Piano notation into structured tokens.

    Returns ParseResult with tokens and any errors encountered.
    Errors are non-fatal — the parser recovers and continues.
    """
    tokens: List[Union[NoteToken, ChordToken, PauseToken]] = []
    errors: List[str] = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        if ch == "[":
            tokens, errors, i = _parse_chord(text, i, n, tokens, errors)

        elif ch == "|":
            tokens, i = _parse_pause(text, i, n, tokens)

        elif ch.isspace():
            i += 1

        else:
            tokens.append(NoteToken(key=ch, position=i, end_position=i + 1))
            i += 1

    return ParseResult(tokens=tokens, errors=errors)


def _parse_chord(text: str, i: int, n: int, tokens: list, errors: list):
    start = i
    i += 1  # skip opening [
    chord_keys: List[str] = []
    saw_nested = False

    while i < n and text[i] != "]":
        c = text[i]
        if c == "[":
            if not saw_nested:
                errors.append(f"Nested '[' inside chord at position {i}")
                saw_nested = True
            i += 1
            continue
        if not c.isspace():
            chord_keys.append(c)
        i += 1

    if i >= n:
        errors.append(f"Unclosed bracket at position {start}")
        for key in chord_keys:
            tokens.append(NoteToken(key=key, position=start, end_position=start + 1))
        return tokens, errors, i

    i += 1  # skip closing ]
    end = i

    if not chord_keys:
        errors.append(f"Empty chord at position {start}")
    else:
        tokens.append(ChordToken(keys=tuple(chord_keys), position=start, end_position=end))

    return tokens, errors, i


def _parse_pause(text: str, i: int, n: int, tokens: list):
    start = i
    count = 0
    while i < n and text[i] == "|":
        count += 1
        i += 1
    tokens.append(PauseToken(count=count, position=start, end_position=i))
    return tokens, i
