# TV Box 1.0.0b1
# HU

IPTV / rádió lejátszó (PyQt5 + VLC, beépített YouTube-nézettel). A v17 egyfájlos változat modulokra bontva – a kód **változatlan**, csak máshol van.

## Indítás
```bash
pip install -r requirements.txt
python TV.py
```
(Raspberry Pi-n a QtWebEngine: `sudo apt install python3-pyqt5.qtwebengine`.)

## Hol mit találsz?

| Fájl | Tartalom |
|---|---|
| `TV.py` | indító |
| `tvbox/app.py` | `TVBox` főablak (`__init__`, bezárás, átméretezés) + `main()` |
| `tvbox/channels.py` | **csatorna- és rádiólisták** (új adó felvétele itt) |
| `tvbox/config.py` | beállítások mentése/betöltése, beállítás-séma |
| `tvbox/theme.py` | témák (Midnight/Aurora), színek, stílusok |
| `tvbox/widgets.py` | saját Qt widgetek |
| `tvbox/player.py` | VLC lejátszás, hangerő, csatornaszám-beírás |
| `tvbox/menus.py` | csatorna- és forrásváltó menü |
| `tvbox/webapps.py` | YouTube webnézet, külső appok, módváltás |
| `tvbox/panels.py` | kilépés, súgó, beállítások, fényerő, témaváltás |
| `tvbox/ui_build.py` | a főablak elemeinek felépítése |
| `tvbox/input.py` | billentyű- és görgő-események |
| `tvbox/youtube.py` | YouTube reklámblokkoló |
| `tvbox/external_apps.py` | külső/web alkalmazások definíciói |
| `tvbox/compat.py` | opcionális függőségek, logger |
| `docs/ELOZMENYEK_v17.txt` | a régi fájl eleji változásnapló (v13–v17) |

**Téma-megjegyzés:** a `THEME`/`ACCENT` futás közben cserélődik, ezért más modulokban `theme.THEME` formában érhető el.


# EN

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

