"""Playback engine running in a separate QThread.

Consumes parsed tokens sequentially.  Plays notes/chords via pynput
keyboard simulation.  Pause/resume/stop responsive within ~10ms.

pynput imported at module level — macOS pyobjc/Quartz MUST load on
the main thread, otherwise Controller() segfaults inside QThread.run().
"""

import random
import time
import threading

from PyQt6.QtCore import QThread, pyqtSignal

from tokens import NoteToken, ChordToken, PauseToken

# Module-level import so pyobjc/Quartz loads on main thread (macOS requirement).
# If this fails, the worker thread will also fail — caught in run().
try:
    from pynput.keyboard import Controller, KeyCode

    _PYNPUT_AVAILABLE = True
except ImportError:
    Controller = None
    KeyCode = None
    _PYNPUT_AVAILABLE = False
except Exception:
    Controller = None
    KeyCode = None
    _PYNPUT_AVAILABLE = False


class PlaybackConfig:
    def __init__(
        self,
        bpm: int = 120,
        speed: float = 1.0,
        hold_duration: float = 0.4,
        pause_base: float = 0.25,
        humanize: bool = False,
        humanize_amount: float = 0.05,
        octave_shift: int = 0,
        semitone_shift: int = 0,
    ):
        self.bpm = bpm
        self.speed = speed
        self.hold_duration = hold_duration
        self.pause_base = pause_base
        self.humanize = humanize
        self.humanize_amount = humanize_amount
        self.octave_shift = octave_shift
        self.semitone_shift = semitone_shift


class PlaybackWorker(QThread):
    progress_updated = pyqtSignal(int, int)
    status_changed = pyqtSignal(str)
    token_changed = pyqtSignal(int, int)
    token_display = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    playback_finished = pyqtSignal()

    def __init__(self, tokens, config: PlaybackConfig, controller, keycode_cls, key_map=None):
        super().__init__()
        self.tokens = tokens
        self.config = config
        self._controller = controller
        self._KeyCode = keycode_cls
        self._key_map = key_map or {}
        self._paused = threading.Event()
        self._paused.set()
        self._stopped = threading.Event()
        self._held_keycodes = set()

    def run(self):

        try:
            try:
                beat_duration = 60.0 / self.config.bpm / self.config.speed
                total = len(self.tokens)

                for idx, token in enumerate(self.tokens):
                    if self._stopped.is_set():
                        break
                    self._paused.wait()
                    if self._stopped.is_set():
                        break

                    self.progress_updated.emit(idx + 1, total)
                    self.token_changed.emit(token.position, token.end_position)

                    if isinstance(token, NoteToken):
                        self.token_display.emit(f"Note({token.key})")
                        self._play_note(token.key, beat_duration)
                    elif isinstance(token, ChordToken):
                        self.token_display.emit(f"Chord({','.join(token.keys)})")
                        self._play_chord(token.keys, beat_duration)
                    elif isinstance(token, PauseToken):
                        self.token_display.emit(f"Pause({token.count})")
                        pause_time = token.count * self.config.pause_base * beat_duration
                        self._sleep(pause_time)

                    if self.config.humanize and not isinstance(token, PauseToken):
                        variation = random.uniform(
                            -self.config.humanize_amount * beat_duration,
                            self.config.humanize_amount * beat_duration,
                        )
                        self._sleep(variation)

                if not self._stopped.is_set():
                    self.playback_finished.emit()
                    self.status_changed.emit("Idle")
            except Exception as e:
                self.error_occurred.emit(f"Playback error: {e}")
                self.status_changed.emit("Error")
        finally:
            self._release_all()
            self._controller = None
            self._KeyCode = None

    def _map_key(self, key: str) -> str:
        """Apply octave/semitone shift to a single key."""
        return self._key_map.get(key, key)

    def _play_note(self, key: str, beat_duration: float):
        physical_key = self._map_key(key)
        try:
            kc = self._KeyCode.from_char(physical_key)
        except Exception:
            self.error_occurred.emit(f"Cannot map key: '{key}'")
            return

        try:
            self._controller.press(kc)
            self._held_keycodes.add(physical_key)
            self._sleep(self.config.hold_duration)
            self._controller.release(kc)
            self._held_keycodes.discard(physical_key)
            remaining = beat_duration - self.config.hold_duration
            if remaining > 0:
                self._sleep(remaining)
        except Exception as e:
            self._held_keycodes.discard(physical_key)
            self.error_occurred.emit(f"Error playing '{key}': {e}")

    def _play_chord(self, keys, beat_duration: float):
        physical_keys = [self._map_key(k) for k in keys]
        keycodes = []
        for k in physical_keys:
            try:
                kc = self._KeyCode.from_char(k)
            except Exception:
                self.error_occurred.emit(f"Cannot map key: '{k}'")
                continue
            keycodes.append((k, kc))

        if not keycodes:
            return

        for k, kc in keycodes:
            try:
                self._controller.press(kc)
                self._held_keycodes.add(k)
            except Exception as e:
                self.error_occurred.emit(f"Error pressing '{k}': {e}")

        self._sleep(self.config.hold_duration)

        for k, kc in keycodes:
            try:
                self._controller.release(kc)
                self._held_keycodes.discard(k)
            except Exception:
                pass

        remaining = beat_duration - self.config.hold_duration
        if remaining > 0:
            self._sleep(remaining)

    def _sleep(self, duration: float):
        if duration <= 0:
            return
        interval = 0.01
        elapsed = 0.0
        while elapsed < duration:
            if self._stopped.is_set():
                break
            self._paused.wait()
            if self._stopped.is_set():
                break
            step = min(interval, duration - elapsed)
            time.sleep(step)
            elapsed += step

    def _release_all(self):
        if not self._controller or not self._KeyCode:
            return
        for key in list(self._held_keycodes):
            try:
                self._controller.release(self._KeyCode.from_char(key))
            except Exception:
                pass
        self._held_keycodes.clear()

    def pause(self):
        self._paused.clear()
        self.status_changed.emit("Paused")

    def resume(self):
        self._paused.set()
        self.status_changed.emit("Playing")

    def stop(self):
        self._stopped.set()
        self._paused.set()
        self.status_changed.emit("Stopped")
