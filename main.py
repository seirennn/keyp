"""Entry point for Virtual Piano Autoplayer."""

import sys

from PyQt6.QtWidgets import QApplication

from gui import MainWindow
from hotkeys import HotkeyManager


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Virtual Piano Autoplayer")
    app.setOrganizationName("VirtualPiano")

    window = MainWindow()

    hotkeys = HotkeyManager(window)
    hotkeys.start_triggered.connect(window._on_start)
    hotkeys.pause_triggered.connect(window._on_pause_resume)
    hotkeys.stop_triggered.connect(window._on_stop)
    hotkeys.error_occurred.connect(window._show_error)
    hotkeys.start()
    window._hotkey_manager = hotkeys

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
