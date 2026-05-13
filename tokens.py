"""Token dataclasses for the Virtual Piano parser."""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class NoteToken:
    key: str
    position: int
    end_position: int


@dataclass
class ChordToken:
    keys: Tuple[str, ...]
    position: int
    end_position: int


@dataclass
class PauseToken:
    count: int
    position: int
    end_position: int
