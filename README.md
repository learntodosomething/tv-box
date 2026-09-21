# TV Box – IPTV & Radio Player

**Modern desktop IPTV and Radio player** with Hungarian & Slovak channel support, built-in YouTube, and a clean remote-like interface.

Version: **v17** (HU/SK expansion)

## Features

- **TV Mode**
  - Large collection of Hungarian and Slovak channels
  - Local/regional channels (Hír TV, Fix TV, Balaton TV, TV Eger, Miskolc TV, etc.)
  - Commercial and news channels
  - Direct HLS streams + community proxies

- **Radio Mode**
  - Extensive Slovak radio stations (public + commercial)
  - Popular Hungarian radios
  - Easy category-based browsing

- **YouTube Integration**
  - Built-in YouTube (TV interface) via QtWebEngine
  - Fallback to external Brave browser
  - Seamless switching between TV / Radio / YouTube

- **User Experience**
  - Keyboard-friendly navigation (remote-style controls)
  - Channel list with categories
  - Volume control, info overlay
  - Fullscreen support
  - Persistent settings

## Tech Stack

- **Python**
- **PyQt5 / QtWebEngine** – GUI + embedded browser
- **python-vlc** – Video/audio playback
- HLS streams

## Requirements

- Python 3.9+
- VLC media player installed on the system
- PyQt5 + PyQtWebEngine
- python-vlc

```bash
pip install PyQt5 PyQtWebEngine python-vlc
```

## How to Run

```bash
git clone https://github.com/learntodosomething/tv-box.git
cd tv-box
python TV_v17.py
```
