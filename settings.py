"""Application settings backed by QSettings."""

from typing import List

from PyQt6.QtCore import QSettings


class AppSettings:
    DEFAULTS = {
        "bpm": 120,
        "speed": 100,
        "hold_duration": 40,
        "start_delay": 3,
        "octave_shift": 0,
        "semitone_shift": 0,
        "loop": False,
        "humanize": False,
        "humanize_amount": 15,
        "pause_base": 0.25,
        "recent_files": [],
        "window_geometry": None,
    }

    MAX_RECENT = 10

    def __init__(self):
        self._settings = QSettings("VirtualPiano", "Autoplayer")

    def get(self, key):
        return self._settings.value(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        self._settings.setValue(key, value)

    @property
    def bpm(self) -> int:
        val = self.get("bpm")
        return int(val) if val else 120

    @bpm.setter
    def bpm(self, value: int):
        self.set("bpm", value)

    @property
    def speed(self) -> int:
        val = self.get("speed")
        return int(val) if val else 100

    @speed.setter
    def speed(self, value: int):
        self.set("speed", value)

    @property
    def hold_duration(self) -> int:
        val = self.get("hold_duration")
        return int(val) if val else 40

    @hold_duration.setter
    def hold_duration(self, value: int):
        self.set("hold_duration", value)

    @property
    def start_delay(self) -> int:
        val = self.get("start_delay")
        return int(val) if val else 3

    @start_delay.setter
    def start_delay(self, value: int):
        self.set("start_delay", value)

    @property
    def loop(self) -> bool:
        val = self.get("loop")
        return val.lower() == "true" if isinstance(val, str) else bool(val)

    @loop.setter
    def loop(self, value: bool):
        self.set("loop", value)

    @property
    def humanize(self) -> bool:
        val = self.get("humanize")
        return val.lower() == "true" if isinstance(val, str) else bool(val)

    @humanize.setter
    def humanize(self, value: bool):
        self.set("humanize", value)

    @property
    def humanize_amount(self) -> int:
        val = self.get("humanize_amount")
        return int(val) if val else 15

    @property
    def octave_shift(self) -> int:
        val = self.get("octave_shift")
        return int(val) if val else 0

    @octave_shift.setter
    def octave_shift(self, value: int):
        self.set("octave_shift", value)

    @property
    def semitone_shift(self) -> int:
        val = self.get("semitone_shift")
        return int(val) if val else 0

    @semitone_shift.setter
    def semitone_shift(self, value: int):
        self.set("semitone_shift", value)

    @property
    def pause_base(self) -> float:
        val = self.get("pause_base")
        return float(val) if val else 0.25

    @property
    def recent_files(self) -> List[str]:
        val = self.get("recent_files")
        if isinstance(val, list):
            return [str(f) for f in val]
        if isinstance(val, str) and val:
            return [val]
        return []

    def add_recent_file(self, path: str):
        files = self.recent_files
        if path in files:
            files.remove(path)
        files.insert(0, path)
        self.set("recent_files", files[: self.MAX_RECENT])

    def save_window_geometry(self, geometry_bytes: bytes):
        self.set("window_geometry", geometry_bytes)

    def load_window_geometry(self):
        return self.get("window_geometry")
