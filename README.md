# Virtual Piano Autoplayer

Automatically plays virtual piano songs by simulating keyboard input on macOS. Works with Virtual Piano websites, Roblox piano games, and any app that uses keyboard keys as piano notes.

## Installation

```bash
cd virtual_piano
pip install -r requirements.txt
```

If you get a "externally-managed-environment" error (common on macOS Homebrew Python):

```bash
pip install --break-system-packages -r requirements.txt
```

Or use a venv:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## macOS Accessibility Permission

**Required.** Without this, the app cannot simulate key presses and global hotkeys will not work.

1. Open **System Settings**
2. Go to **Privacy & Security → Accessibility**
3. Click the **+** button and add:
   - Your terminal app (Terminal.app, iTerm2, etc.)
   - The Python executable (find it with `which python3`)
4. Toggle the switch **ON** for each entry

If running from an IDE (VS Code, PyCharm), add the IDE as well.

## Run

```bash
python main.py
```

## Hotkeys (Global)

Work even when Roblox, browser, or any other app is focused.

| Key | Action |
|-----|--------|
| **F6** | Start playback |
| **F7** | Pause / Resume |
| **F8** | Stop immediately |

## Notation Guide

Enter Virtual Piano notation in the text editor.

### Single Notes

Each character outside brackets is one note. Spaces and newlines are ignored.

```
a s d f g h j k l
```

### Chords

Keys inside `[ ]` are played simultaneously:

```
[lzxb]        → press l, z, x, b together
[sf]          → press s, f together
```

### Pauses

Pipe characters add silence. More pipes = longer pause.

```
|             → short pause
||            → medium pause
||||          → long pause
```

### Complete Examples

```
[lzxb]||[lzxb]||[kzv]
0[sf][rsf]
as[dyj]
jCZkbcljCZk
6 0 [rj] [tx] Z G z g
[6ej]
```

## Playback Controls

### Settings Panel

| Control | Range | Default | Description |
|---------|-------|---------|-------------|
| **BPM** | 10–500 | 120 | Base tempo (beats per minute) |
| **Speed** | 0.05x–5.00x | 1.00x | Playback speed multiplier |
| **Note Duration** | 0.05s–1.00s | 0.40s | How long each key stays pressed |
| **Start Delay** | 0–30 sec | 3 sec | Countdown before playback begins |
| **Octave Shift** | -3 to +3 | 0 | Transpose all keys up/down by octaves |
| **Semitone Shift** | -12 to +12 | 0 | Transpose all keys up/down by semitones |
| **Loop** | on/off | off | Restart song automatically when finished |
| **Humanize** | on/off | off | Add subtle random timing variation |

### Octave / Semitone Shift

Transposes all notes to different octaves or keys.

**Octave shift** moves keys between QWERTY keyboard rows:

```
+1 octave:  z→a  x→s  c→d  v→f  b→g  n→h  m→j
-1 octave:  a→z  s→x  d→c  f→v  g→b  h→n  j→m
```

**Semitone shift** moves keys within the full chromatic layout:

```
+1 semitone:  z→s  x→d  c→v  v→g  b→h  n→j  m→,
-1 semitone:  s→z  d→x  v→c  g→v  h→b  j→n
```

When both are set, octave shift takes priority over semitone shift for overlapping keys.

## File Support

- **Load**: `.txt` files via File → Load Song, or drag and drop a `.txt` file onto the window
- **Save**: File → Save Song (writes `.txt`)
- **Recent Songs**: File → Recent Songs (stores last 10 files)
- Keyboard shortcuts: Cmd+O (open), Cmd+S (save), Cmd+Q (quit)

## Project Structure

```
virtual_piano/
├── main.py          # Entry point, wires GUI + hotkeys
├── gui.py           # PyQt6 dark-theme GUI (all widgets, signals)
├── parser.py        # Character-by-character tokenizer — O(n), no regex
├── player.py        # QThread playback engine (10ms stop/pause response)
├── keymap.py        # Octave/semitone key transposition mapping
├── hotkeys.py       # Global F6/F7/F8 hotkey listener (pynput)
├── tokens.py        # NoteToken, ChordToken, PauseToken dataclasses
├── settings.py      # QSettings persistence (BPM, recent files, geometry)
└── requirements.txt # PyQt6 + pynput
```

## Troubleshooting

**App crashes when clicking Start.**

Grant Accessibility permission (see above). On macOS, keyboard simulation requires this permission — without it the process will crash with a trace trap.

**Nothing happens during playback.**

Make sure the target window (browser, Roblox) is focused before playback starts. Use the **Start Delay** setting to give yourself time to switch windows after clicking Start.

**Hotkeys don't work.**

Same cause — grant Accessibility permission. Both keyboard simulation and global hotkey listening require it.

**"pynput not installed" error.**

```bash
pip install pynput
```

**Font warnings on startup.**

Harmless. The app uses SF Mono → Menlo → Monaco → monospace fallback chain. If you see a warning about "Monospace", install a monospace font or ignore it — the app will still render correctly.
