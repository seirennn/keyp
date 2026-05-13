"""Global hotkey listener using pynput.

Listens for F6 (Start), F7 (Pause/Resume), F8 (Stop) globally.
Requires macOS Accessibility permissions.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class HotkeyManager(QObject):
    start_triggered = pyqtSignal()
    pause_triggered = pyqtSignal()
    stop_triggered = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._listener = None
        self._running = False

    def start(self):
        if self._running:
            return
        try:
            from pynput.keyboard import Key, Listener

            self._listener = Listener(on_press=self._on_press, suppress=False)
            self._listener.start()
            self._running = True
        except Exception as e:
            self.error_occurred.emit(
                f"Failed to start global hotkey listener: {e}\n\n"
                "Ensure Terminal/Python has Accessibility permission:\n"
                "System Settings → Privacy & Security → Accessibility"
            )

    def stop(self):
        self._running = False
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def _on_press(self, key):
        try:
            from pynput.keyboard import Key

            if key == Key.f6:
                self.start_triggered.emit()
            elif key == Key.f7:
                self.pause_triggered.emit()
            elif key == Key.f8:
                self.stop_triggered.emit()
        except Exception:
            pass
