# tv-box

Modern desktop IPTV and radio player with Hungarian & Slovak channel support, built-in YouTube, and a clean remote-style interface.

Built with **Python + PyQt5 + VLC**.

Version: **1.0.0b1** (modular rewrite of the original single-file v17)

## Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Project structure](#project-structure)
6. [Adding channels](#adding-channels)
7. [Themes](#themes)
8. [Limitations](#limitations)
9. [Roadmap](#roadmap)

## Features

**TV Mode**
- Large collection of Hungarian and Slovak channels
- Local / regional channels (Hír TV, Fix TV, Balaton TV, TV Eger, Miskolc TV, etc.)
- Commercial and news channels
- Direct HLS streams

**Radio Mode**
- Extensive Slovak radio stations (public + commercial)
- Popular Hungarian radios
- Category-based browsing

**YouTube Integration**
- Built-in YouTube experience via QtWebEngine
- Fallback to external browser (Brave)
- Seamless switching between TV / Radio / YouTube

**User Experience**
- Keyboard-friendly navigation (remote-style controls)
- Channel list with categories
- Volume control and info overlay
- Fullscreen support
- Persistent settings
- Two built-in themes (Midnight / Aurora)

## Requirements

- Python 3.9+
- VLC media player installed on the system
- PyQt5 + PyQtWebEngine
- python-vlc

```bash
pip install -r requirements.txt
```

**Raspberry Pi note:**  
```bash
sudo apt install python3-pyqt5.qtwebengine
```

## Installation

```bash
git clone https://github.com/learntodosomething/tv-box.git
cd tv-box
pip install -r requirements.txt
python TV.py
```

## Usage

After launching:

- Use arrow keys / number keys for channel navigation
- Switch between TV / Radio / YouTube modes
- Open settings panel for theme, brightness, etc.
- All settings are saved automatically

## Project structure

```
tv-box/
├── TV.py                  # Entry point
├── requirements.txt
├── tvbox/
│   ├── app.py             # Main window + application logic
│   ├── channels.py        # Channel & radio lists (add new stations here)
│   ├── config.py          # Settings load/save
│   ├── theme.py           # Themes (Midnight / Aurora)
│   ├── player.py          # VLC playback control
│   ├── menus.py           # Channel and source menus
│   ├── webapps.py         # YouTube + external apps
│   ├── panels.py          # Settings, help, exit panels
│   ├── ui_build.py        # UI construction
│   ├── input.py           # Keyboard & mouse wheel handling
│   ├── youtube.py         # YouTube ad blocking helpers
│   ├── external_apps.py   # External application definitions
│   ├── widgets.py         # Custom Qt widgets
│   └── compat.py          # Optional dependencies & logging
└── docs/
    └── ELOZMENYEK_v17.txt # Changelog of the original single-file versions
```

## Adding channels

Open `tvbox/channels.py` and add new entries to the appropriate list.

Example:

```python
{
    "name": "Új Csatorna",
    "url": "https://example.com/stream.m3u8",
    "group": "Magyar",
    "logo": None,          # optional
}
```

Restart the application after changes.

## Themes

Two themes are available out of the box:

- **Midnight** – dark, high-contrast
- **Aurora** – slightly lighter with accent colors

Themes can be switched at runtime from the settings panel.  
Theme colors are defined in `tvbox/theme.py`.

## Limitations

- Streams depend on upstream availability (many free IPTV sources are unstable)
- No EPG (Electronic Program Guide) yet
- YouTube experience is limited by QtWebEngine capabilities
- No automatic channel health checking
- Single-window design (no multi-monitor support planned currently)

## Roadmap

- [ ] Channel health checking / auto-skip broken streams
- [ ] Simple EPG support
- [ ] Favorites / recently watched
- [ ] Better YouTube integration (or switch to a more robust web engine)
- [ ] System tray support
- [ ] Packaging (Windows .exe / Linux AppImage)
- [ ] More themes

## License

No license file yet. Feel free to use and modify for personal purposes.

---

Questions or suggestions? Open an issue.
```