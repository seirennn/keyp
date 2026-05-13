"""Main GUI window — PyQt6 dark-themed interface."""

import os
from typing import Optional

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QUrl,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAction,
    QColor,
    QDesktopServices,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QKeySequence,
    QShortcut,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from keymap import build_key_map
from parser import parse
from player import PlaybackConfig, PlaybackWorker
from settings import AppSettings

DARK_STYLE = """
QMainWindow { background-color: #1a1a2e; }
QTextEdit {
    background-color: #16213e; color: #d0d0d0;
    border: 1px solid #0f3460; border-radius: 6px;
    font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
    font-size: 14px; padding: 10px;
    selection-background-color: #533483;
}
QPushButton {
    background-color: #0f3460; color: #d0d0d0;
    border: none; border-radius: 5px;
    padding: 8px 18px; font-size: 13px; font-weight: 600;
    min-width: 80px;
}
QPushButton:hover { background-color: #1a5080; }
QPushButton:pressed { background-color: #0a2540; }
QPushButton:disabled { background-color: #1a1a2e; color: #555; }
QPushButton#startButton { background-color: #1b5e20; }
QPushButton#startButton:hover { background-color: #2e7d32; }
QPushButton#stopButton { background-color: #7f1d1d; }
QPushButton#stopButton:hover { background-color: #991b1b; }
QPushButton#pauseButton { background-color: #92400e; }
QPushButton#pauseButton:hover { background-color: #b45309; }
QSlider::groove:horizontal {
    height: 6px; background: #0f3460; border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #7c3aed; width: 16px; height: 16px;
    margin: -5px 0; border-radius: 8px;
}
QSlider::sub-page:horizontal { background: #7c3aed; border-radius: 3px; }
QLabel { color: #b0b0b0; font-size: 13px; }
QGroupBox {
    color: #d0d0d0; border: 1px solid #0f3460; border-radius: 6px;
    margin-top: 12px; padding-top: 18px; font-size: 13px; font-weight: 600;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QProgressBar {
    background-color: #16213e; border: 1px solid #0f3460; border-radius: 3px;
    text-align: center; color: #d0d0d0; font-size: 11px; height: 18px;
}
QProgressBar::chunk { background-color: #7c3aed; border-radius: 2px; }
QCheckBox { color: #d0d0d0; spacing: 8px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border: 2px solid #0f3460; border-radius: 3px;
    background-color: #16213e;
}
QCheckBox::indicator:checked { background-color: #7c3aed; border-color: #7c3aed; }
QSpinBox {
    background-color: #16213e; color: #d0d0d0;
    border: 1px solid #0f3460; border-radius: 4px;
    padding: 5px 8px; font-size: 13px;
}
QSpinBox:focus { border-color: #7c3aed; }
QMenuBar { background-color: #16213e; color: #d0d0d0; padding: 2px; }
QMenuBar::item:selected { background-color: #0f3460; border-radius: 3px; }
QMenu {
    background-color: #16213e; color: #d0d0d0;
    border: 1px solid #0f3460; border-radius: 4px; padding: 4px;
}
QMenu::item:selected { background-color: #0f3460; border-radius: 3px; }
QMenu::separator { height: 1px; background: #0f3460; margin: 4px 8px; }
"""


class MainWindow(QMainWindow):
    _worker: Optional[PlaybackWorker] = None

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Virtual Piano Autoplayer")
        self.setMinimumSize(820, 720)
        self.resize(920, 820)
        self.setAcceptDrops(True)

        self.settings = AppSettings()
        self._tokens = []
        self._countdown_timer: Optional[QTimer] = None
        self._countdown_remaining = 0
        self._playing = False
        self._paused = False

        self._init_ui()
        self._create_menu_bar()
        self.setStyleSheet(DARK_STYLE)
        self._connect_signals()
        self._load_settings()

    # ── UI construction ─────────────────────────────────────────────

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 6, 14, 14)

        title = QLabel("Virtual Piano Autoplayer")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #e8e8e8;")
        layout.addWidget(title)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "Enter Virtual Piano notation here...\n\n"
            "Examples:\n"
            "[lzxb] || [kzv]\n"
            "0[sf][rsf]\n"
            "as[dyj]\n"
            "jCZkbcljCZk\n"
            "6 0 [rj] [tx] Z G z g"
        )
        self.editor.setTabChangesFocus(True)
        layout.addWidget(self.editor, stretch=1)

        # Status row
        status_row = QHBoxLayout()
        self.status_label = QLabel("● Idle")
        self.status_label.setStyleSheet("font-weight: 700; color: #666; font-size: 13px;")
        status_row.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_row.addWidget(self.progress_bar, stretch=1)

        self.token_label = QLabel("")
        self.token_label.setStyleSheet("color: #7c3aed; font-family: monospace; font-size: 13px;")
        status_row.addWidget(self.token_label)
        layout.addLayout(status_row)

        # Control buttons
        btn_row = QHBoxLayout()

        self.load_btn = QPushButton("Load")
        self.save_btn = QPushButton("Save")
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setObjectName("startButton")
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setObjectName("pauseButton")
        self.pause_btn.setEnabled(False)
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.setEnabled(False)
        self.clear_btn = QPushButton("Clear")

        for btn in [self.load_btn, self.save_btn, self.start_btn, self.pause_btn, self.stop_btn, self.clear_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

        # Settings
        config = QGroupBox("Playback Settings")
        cg = QGridLayout(config)
        cg.setVerticalSpacing(10)
        cg.setHorizontalSpacing(14)

        cg.addWidget(QLabel("BPM:"), 0, 0)
        self.bpm_slider = QSlider(Qt.Orientation.Horizontal)
        self.bpm_slider.setRange(10, 500)
        self.bpm_slider.setValue(120)
        self.bpm_label = QLabel("120")
        self.bpm_label.setMinimumWidth(36)
        self.bpm_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        cg.addWidget(self.bpm_slider, 0, 1)
        cg.addWidget(self.bpm_label, 0, 2)

        cg.addWidget(QLabel("Speed:"), 1, 0)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(5, 500)
        self.speed_slider.setValue(100)
        self.speed_label = QLabel("1.00x")
        self.speed_label.setMinimumWidth(36)
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        cg.addWidget(self.speed_slider, 1, 1)
        cg.addWidget(self.speed_label, 1, 2)

        cg.addWidget(QLabel("Note Duration:"), 2, 0)
        self.duration_slider = QSlider(Qt.Orientation.Horizontal)
        self.duration_slider.setRange(5, 100)
        self.duration_slider.setValue(40)
        self.duration_label = QLabel("0.40s")
        self.duration_label.setMinimumWidth(36)
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        cg.addWidget(self.duration_slider, 2, 1)
        cg.addWidget(self.duration_label, 2, 2)

        cg.addWidget(QLabel("Start Delay:"), 3, 0)
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 30)
        self.delay_spin.setValue(3)
        self.delay_spin.setSuffix(" sec")
        cg.addWidget(self.delay_spin, 3, 1)

        cg.addWidget(QLabel("Octave Shift:"), 4, 0)
        self.octave_spin = QSpinBox()
        self.octave_spin.setRange(-3, 3)
        self.octave_spin.setValue(0)
        self.octave_spin.setToolTip("Shift all keys up/down by octaves (row-based)")
        cg.addWidget(self.octave_spin, 4, 1)

        cg.addWidget(QLabel("Semitone Shift:"), 5, 0)
        self.semitone_spin = QSpinBox()
        self.semitone_spin.setRange(-12, 12)
        self.semitone_spin.setValue(0)
        self.semitone_spin.setToolTip("Shift all keys up/down by semitones")
        cg.addWidget(self.semitone_spin, 5, 1)

        self.loop_check = QCheckBox("Loop Playback")
        cg.addWidget(self.loop_check, 6, 0)

        self.humanize_check = QCheckBox("Humanize (random timing)")
        cg.addWidget(self.humanize_check, 6, 1)

        layout.addWidget(config)

        # Error display
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(
            "color: #f87171; font-size: 12px; padding: 6px; "
            "background-color: #2d1f1f; border-radius: 4px;"
        )
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        # Footer
        footer = QLabel("Hotkeys (global):  F6 = Start  |  F7 = Pause/Resume  |  F8 = Stop")
        footer.setStyleSheet("color: #444; font-size: 11px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

    def _create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        load_action = QAction("Load Song...", self)
        load_action.setShortcut(QKeySequence.StandardKey.Open)
        load_action.triggered.connect(self._on_load)
        file_menu.addAction(load_action)

        save_action = QAction("Save Song...", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        self.recent_menu = QMenu("Recent Songs", self)
        file_menu.addMenu(self.recent_menu)
        self._refresh_recent_menu()

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("Setup Instructions", self)
        about_action.triggered.connect(self._show_setup_help)
        help_menu.addAction(about_action)

    def _refresh_recent_menu(self):
        self.recent_menu.clear()
        recent = self.settings.recent_files
        if not recent:
            empty = QAction("(empty)", self)
            empty.setEnabled(False)
            self.recent_menu.addAction(empty)
        for path in recent:
            action = QAction(os.path.basename(path), self)
            action.setToolTip(path)
            action.triggered.connect(lambda checked, p=path: self._load_file(p))
            self.recent_menu.addAction(action)

    # ── Signal setup ────────────────────────────────────────────────

    def _connect_signals(self):
        self.load_btn.clicked.connect(self._on_load)
        self.save_btn.clicked.connect(self._on_save)
        self.start_btn.clicked.connect(self._on_start)
        self.pause_btn.clicked.connect(self._on_pause_resume)
        self.stop_btn.clicked.connect(self._on_stop)
        self.clear_btn.clicked.connect(self._on_clear)

        self.bpm_slider.valueChanged.connect(self._on_bpm_changed)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        self.duration_slider.valueChanged.connect(self._on_duration_changed)

    def _on_bpm_changed(self, val):
        self.bpm_label.setText(str(val))

    def _on_speed_changed(self, val):
        self.speed_label.setText(f"{val / 100:.2f}x")

    def _on_duration_changed(self, val):
        self.duration_label.setText(f"{val / 100:.2f}s")

    # ── Settings persistence ────────────────────────────────────────

    def _load_settings(self):
        self.bpm_slider.setValue(self.settings.bpm)
        self.speed_slider.setValue(self.settings.speed)
        self.duration_slider.setValue(self.settings.hold_duration)
        self.delay_spin.setValue(self.settings.start_delay)
        self.octave_spin.setValue(self.settings.octave_shift)
        self.semitone_spin.setValue(self.settings.semitone_shift)
        self.loop_check.setChecked(self.settings.loop)
        self.humanize_check.setChecked(self.settings.humanize)

        geo = self.settings.load_window_geometry()
        if geo:
            self.restoreGeometry(geo)

    def _save_settings(self):
        self.settings.bpm = self.bpm_slider.value()
        self.settings.speed = self.speed_slider.value()
        self.settings.hold_duration = self.duration_slider.value()
        self.settings.start_delay = self.delay_spin.value()
        self.settings.octave_shift = self.octave_spin.value()
        self.settings.semitone_shift = self.semitone_spin.value()
        self.settings.loop = self.loop_check.isChecked()
        self.settings.humanize = self.humanize_check.isChecked()
        self.settings.save_window_geometry(self.saveGeometry())

    def closeEvent(self, event):
        self._on_stop()
        self._save_settings()
        super().closeEvent(event)

    # ── File operations ─────────────────────────────────────────────

    def _on_load(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Song", "", "Text Files (*.txt);;All Files (*)"
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            self.editor.setPlainText(text)
            self.settings.add_recent_file(path)
            self._refresh_recent_menu()
            self._update_status("Idle", "#666")
            self._clear_error()
        except Exception as e:
            self._show_error(f"Failed to load file: {e}")

    def _on_save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Song", "", "Text Files (*.txt);;All Files (*)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
                self.settings.add_recent_file(path)
                self._refresh_recent_menu()
            except Exception as e:
                self._show_error(f"Failed to save file: {e}")

    # ── Drag and drop ───────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.endswith(".txt"):
                self._load_file(path)

    # ── Playback control ────────────────────────────────────────────

    def _on_start(self):
        text = self.editor.toPlainText().strip()
        if not text:
            self._show_error("Enter song notation first.")
            return

        result = parse(text)
        if result.errors:
            self._show_error("Parser errors:\n" + "\n".join(result.errors))
        else:
            self._clear_error()

        if not result.tokens:
            self._show_error("No playable tokens found in input.")
            return

        self._tokens = result.tokens
        delay = self.delay_spin.value()

        if delay > 0:
            self._start_countdown(delay)
        else:
            self._start_playback()

    def _start_countdown(self, seconds: int):
        self._playing = True
        self._countdown_remaining = seconds
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.editor.setReadOnly(True)

        self._update_countdown_label()

        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._countdown_tick)
        self._countdown_timer.start(1000)

    def _countdown_tick(self):
        self._countdown_remaining -= 1
        if self._countdown_remaining <= 0:
            self._countdown_timer.stop()
            self._countdown_timer = None
            self._start_playback()
        else:
            self._update_countdown_label()

    def _update_countdown_label(self):
        self._update_status(f"Starting in {self._countdown_remaining}...", "#f59e0b")

    def _start_playback(self):
        # Create keyboard controller on the main thread.
        # On macOS, CGEventCreateKeyboardEvent MUST be called from the main
        # thread or the process gets SIGTRAP (trace trap).
        try:
            from pynput.keyboard import Controller as PynputController, KeyCode
        except ImportError:
            self._show_error("pynput is not installed. Run: pip install pynput")
            self._on_stop()
            return

        try:
            controller = PynputController()
        except Exception as e:
            self._show_error(
                f"Cannot access keyboard: {e}\n\n"
                "Grant Accessibility permission to Terminal/Python:\n"
                "System Settings → Privacy & Security → Accessibility"
            )
            self._on_stop()
            return

        config = PlaybackConfig(
            bpm=self.bpm_slider.value(),
            speed=self.speed_slider.value() / 100.0,
            hold_duration=self.duration_slider.value() / 100.0,
            pause_base=self.settings.pause_base,
            humanize=self.humanize_check.isChecked(),
            humanize_amount=self.settings.humanize_amount / 100.0,
            octave_shift=self.octave_spin.value(),
            semitone_shift=self.semitone_spin.value(),
        )

        key_map = build_key_map(config.octave_shift, config.semitone_shift)

        self._worker = PlaybackWorker(self._tokens, config, controller, KeyCode, key_map)
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.status_changed.connect(self._on_worker_status)
        self._worker.token_changed.connect(self._highlight_token)
        self._worker.token_display.connect(self.token_label.setText)
        self._worker.error_occurred.connect(self._on_worker_error)
        self._worker.playback_finished.connect(self._on_playback_finished)
        self._worker.finished.connect(self._on_worker_done)
        self._worker.start()

        self._playing = True
        self._paused = False
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.pause_btn.setText("⏸ Pause")
        self.stop_btn.setEnabled(True)
        self.clear_btn.setEnabled(False)
        self.editor.setReadOnly(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self._tokens))
        self.progress_bar.setValue(0)
        self._update_status("Playing", "#22c55e")

    def _on_pause_resume(self):
        if not self._worker:
            return
        if self._paused:
            self._worker.resume()
            self._paused = False
            self.pause_btn.setText("⏸ Pause")
            self._update_status("Playing", "#22c55e")
        else:
            self._worker.pause()
            self._paused = True
            self.pause_btn.setText("▶ Resume")
            self._update_status("Paused", "#f59e0b")

    def _on_stop(self):
        if self._countdown_timer:
            self._countdown_timer.stop()
            self._countdown_timer = None

        was_playing = self._playing
        self._playing = False
        self._paused = False

        if self._worker:
            self._worker.stop()
            self._worker.wait(500)
            self._worker = None

        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("⏸ Pause")
        self.stop_btn.setEnabled(False)
        self.clear_btn.setEnabled(True)
        self.editor.setReadOnly(False)
        self.progress_bar.setVisible(False)
        self.token_label.setText("")
        self._clear_highlight()

        if was_playing:
            self._update_status("Stopped", "#ef4444")
        else:
            self._update_status("Idle", "#666")

    def _on_clear(self):
        self.editor.clear()
        self._clear_error()
        self._update_status("Idle", "#666")

    def _on_progress(self, current: int, total: int):
        self.progress_bar.setValue(current)

    def _on_worker_status(self, status: str):
        pass  # status handled via dedicated state changes

    def _on_worker_error(self, msg: str):
        self._show_error(msg)
        self._on_stop()

    def _on_playback_finished(self):
        if self._playing and self.loop_check.isChecked():
            self._start_playback()
        else:
            self._on_stop()

    def _on_worker_done(self):
        self._worker = None

    # ── Token highlighting ──────────────────────────────────────────

    def _highlight_token(self, position: int, end_position: int):
        cursor = self.editor.textCursor()
        cursor.setPosition(position)
        block = cursor.block()
        line_cursor = QTextCursor(block)

        line_sel = QTextEdit.ExtraSelection()
        line_sel.format.setBackground(QColor(26, 26, 62))
        line_sel.cursor = line_cursor

        cursor.setPosition(end_position, QTextCursor.MoveMode.KeepAnchor)
        token_sel = QTextEdit.ExtraSelection()
        token_sel.format.setBackground(QColor("#7c3aed"))
        token_sel.format.setForeground(QColor("#ffffff"))
        token_sel.cursor = cursor

        self.editor.setExtraSelections([line_sel, token_sel])
        self.editor.setTextCursor(cursor)
        self.editor.ensureCursorVisible()

    def _clear_highlight(self):
        self.editor.setExtraSelections([])

    # ── Status helpers ──────────────────────────────────────────────

    def _update_status(self, text: str, color: str):
        self.status_label.setText(f"● {text}")
        self.status_label.setStyleSheet(f"font-weight: 700; color: {color}; font-size: 13px;")

    def _show_error(self, msg: str):
        self.error_label.setText(msg)
        self.error_label.setVisible(True)

    def _clear_error(self):
        self.error_label.setText("")
        self.error_label.setVisible(False)

    def _show_setup_help(self):
        QMessageBox.information(
            self,
            "Setup Instructions",
            "macOS Accessibility Permission Required\n\n"
            "1. Open System Settings\n"
            "2. Go to Privacy & Security\n"
            "3. Select Accessibility\n"
            "4. Add and enable:\n"
            "   • Terminal (or your terminal app)\n"
            "   • Python launcher\n\n"
            "If running as .app bundle, add the .app as well.\n\n"
            "Without this, keyboard simulation and global hotkeys will not work.\n\n"
            "Hotkeys:\n"
            "  F6 — Start playback\n"
            "  F7 — Pause / Resume\n"
            "  F8 — Stop immediately",
        )
