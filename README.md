# tv-box

Modern desktop IPTV and radio player with Hungarian & Slovak channel support, built-in YouTube, and a clean remote-style interface that behaves like a real TV.

Built with **Python + PyQt5 + VLC**.

Version: **1.3.0b1** (v20 – simple EPG, brightness overlay, standby from the phone, settings on the phone, YouTube volume; on top of the v19 phone remote, the v18 stability and buffering work and the modular rewrite of the original single-file v17)

## Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Controls](#controls)
5. [Settings](#settings)
6. [TV-style channel switching](#tv-style-channel-switching)
7. [Playback reliability and buffering](#playback-reliability-and-buffering)
8. [YouTube](#youtube)
9. [Phone remote](#phone-remote)
10. [Standby (power) and brightness](#standby-power-and-brightness)
11. [EPG (programme guide)](#epg-programme-guide)
12. [Project structure](#project-structure)
13. [Adding channels](#adding-channels)
14. [Themes](#themes)
15. [Diagnostics and testing](#diagnostics-and-testing)
16. [Troubleshooting](#troubleshooting)
17. [Limitations](#limitations)
18. [Roadmap](#roadmap)

## Features

**TV Mode**
- 83 Hungarian, Slovak and international channels in 12 categories
- Local / regional channels (e.g. Balaton TV, TV7 Békéscsaba)
- Public, commercial, kids, movie, documentary, music, sports and 24/7 channels
- Direct HLS streams

**Radio Mode**
- 21 stations: popular Hungarian radios plus Slovak public and commercial stations
- Category-based browsing

**TV-style channel switching**
- Arrow keys *preview* the next channel in a corner card while the current channel keeps playing
- The switch happens after a short wait (3 s by default) or instantly on Enter
- Typing a channel number works as on a real remote

**EPG (programme guide)**
- Shows what is on now and what comes next, from any XMLTV file or URL (see [EPG](#epg-programme-guide))
- Info card with progress bar, programme title under every channel in the list and in the channel preview, `I` for the programme info

**Phone remote**
- Always on: scan a QR code on the TV and control the box from your phone's browser – no app to install
- D-pad, volume, channel list with search, number pad, and switching between TV / Radio / YouTube
- Full **Settings** tab: change every setting from the phone, the TV follows instantly
- **Power button**: hold 2 seconds to switch the TV Box off (standby), hold 2 seconds to switch it back on
- Real volume percentage, also inside YouTube; now / next programme
- YouTube search typed on the phone (see [Phone remote](#phone-remote))

**Reliable playback**
- Adaptive buffering: a stream that stalls is reconnected automatically with a larger buffer, and the app remembers which streams need one
- Automatic reconnect when a live stream drops, with back-off between attempts
- All blocking VLC calls run on a background thread, so the interface never freezes on a slow or dead server

**YouTube Integration**
- Built-in, full-screen YouTube (TV interface) via QtWebEngine, controlled with the same keys
- Optional fallback to a separate Brave kiosk window
- Seamless switching between TV / Radio / YouTube

**User Experience**
- Keyboard-friendly navigation (remote-style controls)
- Channel list with categories
- Volume control and info overlay
- Fullscreen support
- Persistent settings, saved automatically
- Two built-in themes (Midnight / Aurora)

## Requirements

- Python 3.9+ (tested on 3.12 and 3.13)
- VLC media player installed on the system (on Windows its bitness must match your Python, normally 64-bit)
- PyQt5 + PyQtWebEngine
- python-vlc

```bash
pip install -r requirements.txt
```

`requirements.txt`:

```
PyQt5
PyQtWebEngine
python-vlc
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

Only one instance can run at a time.

## Controls

**Watching TV / Radio**

| Key | Action |
|---|---|
| `←` / `→` | Preview previous / next channel (see [below](#tv-style-channel-switching)) |
| `Enter` | Switch to the previewed channel immediately (or confirm a typed number) |
| `Esc` | Cancel the preview; with no preview active: quit (asks for confirmation) |
| `0`–`9` | Type a channel number (up to 3 digits) |
| `↑` / `↓` | Volume up / down (mouse wheel works too) |
| `Space` or `V` | Mute |
| `Backspace` | Previous channel |
| `M` | Channel list |
| `B` | Source menu (TV / Radio / YouTube / Settings) |
| `S` | Settings |
| `R` | Phone remote: show the QR code |
| `I` | Programme info (EPG): shows the info card with the current and the next programme |
| any key | While in standby: wake up |
| `H` or `?` | Key help (any key closes it) |
| `Q` | Quit (asks for confirmation, if enabled) |

**Menus**

| Menu | Keys |
|---|---|
| Channel list | `↑` `↓` move, `Enter` play, `Esc` / `M` close |
| Source menu | `←` `→` (or `↑` `↓`) move, `Enter` select, `B` / `Esc` close |
| Settings | `↑` `↓` select row, `←` `→` (or `Enter`) change value, `Esc` / `S` close |

**Inside YouTube:** the arrow keys and `Enter` control YouTube itself. `Esc` returns to TV / Radio, `B` opens the source menu, `S` opens the settings.

## Settings

Open with `S`, from the source menu, or from the **Settings tab of the phone remote** (the TV and the phone show the same values, and a change on either one appears on both). The panel is large so it can be read from the sofa. Changes apply immediately and are saved to `~/.tvbox_settings.json`.

The phone remote and the YouTube ad blocker have no setting any more: they are **always on**. (The ad blocker only affects the built-in YouTube view; the separate Brave window is protected by Brave's own Shields.)

| Setting | Options | Default |
|---|---|---|
| Brightness | 20–100 %: a black, see-through layer in front of the whole screen (100 % = no dimming, lower = darker). See [Standby and brightness](#standby-power-and-brightness) | 100 % |
| Theme | Midnight Blue / Aurora Amber | Midnight Blue |
| Confirm exit | On / Off | On |
| Menu auto-close | 3 s / 6 s / 10 s / Never | 6 s |
| Animations | On / Off | On |
| Switch patience | 2 s / 3 s / 5 s | 3 s |
| Info card duration | 3 s / 5 s / 8 s / Always visible | 5 s |
| Programme info (EPG) | On / Off (only does something if an [EPG source](#epg-programme-guide) is set) | On |

*Switch patience* is how long the app waits before switching to a previewed channel, and also how long it waits for the next digit of a typed number.

## TV-style channel switching

On a real TV the picture does not jump the moment you press the channel button, and neither does tv-box:

1. Press `→` (or `←`). A card appears in the top-right corner with the channel number, its name and a shrinking timer bar. **The current channel keeps playing.**
2. Press the arrow again to move further – the timer restarts on every press.
3. When the timer runs out, the app switches to the channel shown in the card. Press `Enter` to switch right away, or `Esc` to discard the preview.

If you step back to the channel that is already playing, nothing is restarted. Opening any menu, changing the source or typing a number cancels a pending preview. A typed number that matches exactly one channel still switches instantly.

## Playback reliability and buffering

Free IPTV streams are often slow or flaky, so playback is supervised:

- **Per-stream buffer.** Playback starts with a 2 s network buffer for TV and 3 s for radio.
- **Stall detection.** If buffering lasts longer than 12 s, or a channel does not start within 18 s, the app reconnects with a larger buffer (TV: 2 → 3.5 → 6 → 9 s, radio: 3 → 5 → 8 → 12 s).
- **Remembered per stream.** The buffer level that worked is stored (in `~/.tvbox_settings.json`, keyed by a hash of the stream URL), so problem channels start with a larger buffer next time.
- **Auto-reconnect.** Errors and dropped live streams trigger up to 4 automatic retries (1, 2, 4, 8 s apart) before the error card appears; `Enter` retries manually.
- **No spinner flicker.** The buffering card only appears if buffering lasts longer than about 0.8 s.
- **Zapping is debounced.** Rapid channel changes are merged, so holding a key does not hammer VLC.
- **Background VLC thread.** `set_media`, `play`, `stop` and volume calls run on a worker thread (`tvbox/vlcworker.py`); a slow server can delay a channel, but never freezes the UI.

The ladders and timeouts are constants at the top of `tvbox/buffering.py`; the VLC start-up arguments are in `tvbox/config.py` (`VLC_BASE_ARGS`, `VLC_OPTIONAL_ARGS`).

If one channel buffers constantly even at the largest buffer, the server is most likely slower than the stream itself. Find such channels with [`tools/stream_probe.py`](#diagnostics-and-testing).

## YouTube

YouTube runs inside the app window using the TV ("Leanback") interface, so it can be navigated with the arrow keys and `Enter` like the rest of the app. Switching to it stops the TV / Radio playback; `Esc` brings you back.

The embedded view is controlled by one switch in `tvbox/external_apps.py`:

```python
YOUTUBE_EMBEDDED = True    # built-in view (default)
# YOUTUBE_EMBEDDED = False # separate Brave kiosk window
```

If QtWebEngine is not installed, the app automatically falls back to the Brave mode. In that mode Brave is looked up on the `PATH` and in the usual install locations; if it is not found, add your path to `extra_paths` in `tvbox/external_apps.py`. `Alt+F4` closes the Brave window and returns to tv-box.

> **Known risk:** the embedded Chromium and VLC's native video surface share one window and each use their own GPU compositor. On some machines this can cause crashes. tv-box mitigates it (the web view is pre-warmed shortly after start-up, VLC is stopped before the web view is shown, the video surface is repainted after overlays). If YouTube crashes on your machine, set `YOUTUBE_EMBEDDED = False`.

## Phone remote

Control tv-box from your phone's browser – nothing to install on the phone.

**Set up**

1. The phone remote starts together with the TV Box. Press `R` on the keyboard to show the QR code.
2. Scan it with your phone camera. The phone must be on the **same Wi-Fi / network** as the TV Box.
3. The remote page opens and the QR code closes by itself. Add the page to your home screen if you like.

On Windows the first start triggers a firewall prompt – allow Python on *private* networks. The prompt can hide behind the full-screen window; if the phone cannot load the page, run `tools/remote_firewall_windows.bat` (as administrator) instead, and see [Troubleshooting](#troubleshooting).

**What the remote can do**

| Tab | Features |
|---|---|
| Remote | D-pad and OK, Back, Close, channel list / source menu / settings, volume and mute (hold to repeat), CH ▲/▼ (uses the same preview as the arrow keys), number pad |
| Channels | The full TV and radio list with a search box (it also searches the programme titles); tap a channel to play it |
| Settings | Every setting with ◀ ▶ buttons (hold to repeat); the ⚙ button on the Remote tab opens this tab and the settings panel on the TV |
| Power ⏻ | Top right: hold for 2 seconds to switch off. In standby the page shows a big ⏻ button: hold for 2 seconds to switch on |
| YouTube | Search box: type a query (or paste a YouTube link), and the result opens on the TV |
| Top bar | Now playing, current / next programme with a progress bar (if EPG is set), the volume percentage, status (buffering / error), pending channel preview, and one-tap switching between **TV**, **Radio** and **YouTube** |

Inside YouTube the D-pad buttons are forwarded to YouTube itself, the volume buttons change the video volume (the phone and the TV show the real percentage, read back from the video every second, so a change made inside YouTube shows up too; in the separate Brave window the volume buttons change the computer's master volume instead, via `wpctl` / `pactl` / `amixer` on Linux, `pycaw` on Windows, `osascript` on macOS), and *Close* returns to TV / Radio. The remote never quits the program – `Esc` from the phone only closes menus, panels and previews.

**YouTube search** works in the embedded mode (`YOUTUBE_EMBEDDED = True`). The search link format of YouTube's TV interface is not documented, so the templates are constants at the top of `tvbox/remote.py` (`YOUTUBE_SEARCH_URL`, `YOUTUBE_WATCH_URL`). If a search does not land on the results page, change `YOUTUBE_SEARCH_URL` to `https://www.youtube.com/results?search_query={q}` (or another format) – no other change is needed. Typing on the phone also avoids a limitation of the physical keyboard: while YouTube is open, tv-box reserves `B`, `S`, `H` and `M` for its own shortcuts.

**Security**

- The server runs while the TV Box runs (it has to, so the phone can switch the TV Box back on from standby) and uses the first free port from 8765 up.
- Every request needs a secret token, which is part of the QR code and stored in `~/.tvbox_settings.json`. Press `N` on the QR screen to generate a new token and lock out every phone that scanned the old one.
- Wrong tokens are rate-limited (10 attempts per minute per address), commands are whitelisted and validated, and request bodies are limited to 2 KB.
- The connection is plain HTTP on your local network, so use it on a network you trust. Do not forward the port to the internet.

The QR code is generated by the built-in encoder `tvbox/qrcode_min.py`, so no extra package is needed.

## Standby (power) and brightness

**Standby – "off" and "on" from the phone.** Hold the ⏻ button on the phone for **2 seconds** and the TV Box goes into standby: playback stops (the separate YouTube window is closed too), the whole screen turns black, and on X11 the monitor goes to sleep (`xset dpms force off`). The program keeps running – that is what lets the phone switch it back on: hold the big ⏻ button on the phone for 2 seconds, or press any key on the keyboard. In standby every other phone command is ignored. The server also rejects a power command that does not carry a hold time of at least 1.8 s, so a stray request cannot switch the box off. Standby does **not** shut the computer down: after that the phone could not reach it any more.

**Brightness** is a black, see-through window in front of the whole screen. 100 % = no window at all (no dimming); the lower the value, the darker the picture (the layer's opacity is 100 % minus the brightness). It lies above the VLC video and the TV Box's own cards.

- Windows, macOS, X11 with a compositing window manager: a transparent top-level window. On X11 it bypasses the window manager, because window managers put full-screen windows above "always on top" windows.
- X11 *without* a compositor (older Raspberry Pi OS, plain openbox): see-through windows cannot be blended there, so the app switches to VLC's own brightness filter. That darkens only the video picture (a bit more strongly than the overlay), not the cards. Force a mode with the environment variable `TVBOX_DIM=overlay` or `TVBOX_DIM=vlc`.
- Wayland: a client cannot place itself above other programs. If Qt runs in `xcb` (XWayland) mode, which is the PyQt5 default, the X11 behaviour applies.
- The old `/sys/class/backlight` code is gone (on an HDMI monitor it did nothing). A Raspberry Pi touch display's hardware backlight can still be used separately.

## EPG (programme guide)

tv-box reads an **XMLTV** file (`.xml` or `.xml.gz`) and shows what is on now and next. No programme source is bundled: XMLTV is a standard format with many free and paid providers and grabbers, so use whichever covers your channels.

**Set it up** – pick one (the first that exists wins):

1. Environment variable: `TVBOX_EPG=https://example.com/epg.xml.gz` (or a file path)
2. `~/.tvbox_settings.json`: inside the `"settings"` block add `"_epg_source": "https://example.com/epg.xml.gz"`
3. Put the file at `~/.tvbox/epg.xml` (or `epg.xml.gz`) – handy if a cron job refreshes it with a grabber such as `tv_grab_huro`, WebGrab+ or iptv-org/epg

Then run `python tools/epg_check.py` to see which of your channels were matched.

| Where | What |
|---|---|
| Info card | Current programme with time span and progress bar, plus the next programme |
| Channel list (`M`) | The current programme's title under each channel name |
| Channel preview (`←` `→`) | The current programme of the channel you are stepping to |
| `I` | Shows the info card again (also says if there is no EPG source or no data) |
| Phone remote | Now / next in the top bar, the programme under each channel in the *Channels* tab |

- The file is downloaded and parsed on a background thread, cached in `~/.tvbox/epg_<hash>.xml` and refreshed every 12 hours; at the next start the cache is used immediately, and if a download fails the cache is the fallback.
- Only the channels in your list and programmes from 6 hours ago to 72 hours ahead are kept in memory.
- Channels are matched by **name** (ignoring case, accents and a trailing "HD"), using the `display-name` and `id` of the XMLTV channels. If one is not matched, add its XMLTV name to `EPG_ALIASES` in `tvbox/epg_core.py`.
- Safety limits: 80 MB download, 400 MB unpacked, 25 s per read / 180 s in total, 400 000 programmes. A broken or malicious file cannot hang or crash the app; at worst there is no programme info.
- Switch it off with *Settings → Programme info (EPG)*. Without an EPG source the app looks and behaves as before.

## Project structure

```
tv-box/
├── TV.py                  # Entry point
├── requirements.txt
├── tvbox/
│   ├── app.py             # Main window + application logic
│   ├── channels.py        # Channel & radio lists (add new stations here)
│   ├── config.py          # Settings load/save, settings schema, VLC arguments
│   ├── theme.py           # Themes (Midnight / Aurora)
│   ├── player.py          # Playback control, channel preview, digit entry
│   ├── buffering.py       # Stall detection and adaptive buffer logic (Qt-free)
│   ├── vlcworker.py       # Background thread for blocking VLC calls (Qt-free)
│   ├── menus.py           # Channel and source menus
│   ├── webapps.py         # Embedded YouTube + external apps
│   ├── panels.py          # Settings, help, exit panels, fade animations
│   ├── ui_build.py        # UI construction
│   ├── input.py           # Keyboard & mouse wheel handling
│   ├── youtube.py         # YouTube ad blocking helpers
│   ├── external_apps.py   # Embedded/external app definitions, YOUTUBE_EMBEDDED
│   ├── widgets.py         # Custom Qt widgets
│   ├── remote.py          # Phone remote: HTTP server, token auth, command validation (Qt-free)
│   ├── remote_page.py     # The web page that opens on the phone
│   ├── remote_ui.py       # Phone remote: QR panel, command handling on the GUI thread
│   ├── sysvol.py          # System master volume (separate YouTube window): wpctl / pactl / amixer / pycaw / osascript
│   ├── dimmer.py          # Brightness: black see-through overlay (+ VLC filter fallback)
│   ├── power.py           # Standby ("off" / "on") mode
│   ├── epg.py             # EPG: background loading, timers, info card / list / preview / phone updates
│   ├── epg_core.py        # EPG: XMLTV parser, name matching, download + cache (Qt-free)
│   ├── qrcode_min.py      # Dependency-free QR code generator (Qt-free)
│   └── compat.py          # Optional dependencies & logging
├── tools/
│   ├── stream_probe.py    # Measures which streams are too slow for real-time playback
│   ├── remote_check.py    # Network diagnosis for the phone remote (+ --serve test server)
│   ├── epg_check.py       # Shows which channels an XMLTV source matches, and which are missing
│   ├── remote_firewall_windows.bat      # Opens the remote's ports for the local subnet (Windows)
│   ├── remote_firewall_fix_blocks.bat   # Lists/removes Block rules for python.exe (Windows)
│   └── remote_firewall_fix_blocks.ps1
├── tests/
│   ├── stress_test.py     # Keyboard storm + VLC events + flaky EPG server + standby/brightness + phone-remote load
│   ├── epg_fixture.py     # Generates synthetic XMLTV files for the EPG tests
│   ├── test_epg.py, test_sysvol.py, test_power_dim_settings.py   # EPG core, system volume, full-app test of standby / brightness / phone settings
│   └── test_*.py          # Unit tests (run without PyQt5 or VLC)
└── docs/
    ├── ELOZMENYEK_v17.txt # Changelog of the original single-file versions
    └── VALTOZASOK_v18.txt # Changelog of the v18 line
```

## Adding channels

Open `tvbox/channels.py` and add a `(name, url)` tuple to a category in `CHANNEL_DATA` (TV) or `RADIO_DATA` (radio). Categories are `(category name, [entries])` pairs, and new categories can be added the same way.

```python
("Film", [
    ("Film+", "http://example.com/film_plus/index.m3u8"),
    ("Új Csatorna", "https://example.com/stream.m3u8"),   # <- new entry
]),
```

Channel numbers are assigned automatically in list order, so inserting a channel in the middle shifts the numbers after it. Learned buffer levels are keyed by URL and are not affected.

A completely new source type (a third tab next to TV and Radio) only needs a new row in the `SOURCES` list in the same file.

Restart the application after changes. Then run `python tools/stream_probe.py` to check the new stream.

## Themes

Two themes are available out of the box:

- **Midnight** – dark, high-contrast
- **Aurora** – slightly lighter with warm accent colors

Themes can be switched at runtime from the settings panel.
Theme colors are defined in `tvbox/theme.py`.

## Diagnostics and testing

**Find the streams that buffer** – needs only Python, not VLC or Qt:

```bash
python tools/stream_probe.py                # all channels and stations
python tools/stream_probe.py --only radio   # radio only
python tools/stream_probe.py --workers 1    # most accurate bandwidth measurement
python tools/stream_probe.py --json out.json
```

For HLS streams it downloads the latest segments and reports the *real-time factor* (segment duration ÷ download time). Below 1.0 the server is slower than playback and the channel **will** buffer; values up to about 1.5 are borderline. Dead and stuck live playlists are reported too.

**Unit tests** – these run without PyQt5 and VLC:

```bash
python tests/test_buffering.py     # stall detection and buffer ladder
python tests/test_vlcworker.py     # non-blocking worker thread
python tests/test_chain_nogui.py   # stale events from the previous stream are ignored
python tests/test_preview.py       # channel preview state machine
python tests/test_routing.py       # source tiles: embedded YouTube vs Brave fallback
python tests/test_probe_local.py   # stream_probe against a local throttled server
python tests/test_qrcode.py        # QR encoder (decoded with OpenCV if installed)
python tests/test_remote_server.py # remote HTTP server: auth, validation, rate limit
python tests/test_remote_commands.py # phone commands -> app actions, end-to-end over HTTP
```

**Stress test** – needs PyQt5; fires ~200 random key presses per second plus simulated VLC events from a background thread and checks for freezes, exceptions, memory growth and inconsistent UI state:

```bash
python tests/stress_test.py --seconds 60                 # offscreen UI, fake VLC
python tests/stress_test.py --real-vlc                   # real VLC (needs a display)
python tests/stress_test.py --real-vlc --no-chaos        # key storm only
python tests/stress_test.py --real-vlc --allow-web       # also exercise embedded YouTube
python tests/stress_test.py --allow-remote               # also hammer the phone-remote server over HTTP (state, lists, EPG, commands incl. power and settings)
python tests/stress_test.py --real-vlc --local-streams   # real VLC against local ffmpeg HLS streams (good / 404 / slow / dead); needs ffmpeg
python tests/stress_test.py --no-epg                     # without the EPG load
```

The test never launches external programs and uses a temporary settings file. It writes `tests/stress_log.txt` (Python stacks of all threads when the UI freezes, and of the crashing thread on a native crash) and `tests/stress_keys.txt` (the key sequence), so a crash can be traced back. Do not commit these two files. Exit code `0` means everything is fine.

## Troubleshooting

| Problem | What to try |
|---|---|
| Program does not start / "libVLC cannot start" | Install VLC and make sure its bitness matches Python (64-bit with 64-bit) |
| One channel buffers constantly | Run `tools/stream_probe.py`; a real-time factor below 1.0 means the server is too slow |
| "Channel cannot be reached" card | `Enter` retries; the stream URL may be dead – check it with `tools/stream_probe.py` |
| YouTube opens in a separate window | QtWebEngine is missing (`pip install PyQtWebEngine`) or `YOUTUBE_EMBEDDED = False` |
| YouTube crashes the app | Set `YOUTUBE_EMBEDDED = False` (see [known risk](#youtube)) |
| Brave not found | Add its path to `extra_paths` in `tvbox/external_apps.py` |
| Phone cannot open the remote page (works on the PC itself) | 1) Run `python tools/remote_check.py --serve` and open the printed address on the phone: if even that fails, it is the network/firewall, not tv-box. 2) Run `tools/remote_firewall_windows.bat` (allows TCP 8765–8784 for the local subnet). 3) If a *Block* rule for `python.exe` exists – Windows creates one when the firewall prompt is cancelled, and it overrides allow rules – remove it with `tools/remote_firewall_fix_blocks.bat`. 4) Check: same Wi-Fi (guest networks / client isolation), phone mobile data off, third-party antivirus firewalls. `python tools/remote_check.py` lists network profile, firewall state, block rules and antivirus products |
| Remote says the permission is invalid | The token was changed (`N`); scan the new QR code |
| YouTube search does nothing useful | See [Phone remote](#phone-remote): adjust `YOUTUBE_SEARCH_URL` in `tvbox/remote.py` |
| Program says it is already running after a crash | Start it again; a stale lock is cleaned up automatically |
| Brightness does not dim the cards / the YouTube window | On X11 without a compositor only the VLC picture is dimmed; see [Standby and brightness](#standby-power-and-brightness). Force `TVBOX_DIM=overlay` to try the overlay |
| No programme info | Run `python tools/epg_check.py`; check that a source is set, that *Settings → Programme info (EPG)* is on, and add missing channel names to `EPG_ALIASES`. Press `I` on the TV: the card says whether there is no source, the file is still loading, or it could not be loaded |
| YouTube volume percentage is `–` | Nothing to read yet (no video on the page). In the separate Brave window the master volume is used: it needs `wpctl`, `pactl` or `amixer` (Linux) or `pip install pycaw` (Windows) |

## Limitations

- Streams depend on upstream availability (many free IPTV sources are unstable)
- EPG needs an XMLTV source of your own; channels are matched by name, so some may need an alias; no programme descriptions or full-day guide screen yet
- Standby switches the screen off but does not power the computer down; waking it needs the phone or a key
- Brightness over a separate Brave window and on Wayland-native Qt depends on the window system (see [Standby and brightness](#standby-power-and-brightness))
- No channel health check on start-up (broken streams are retried automatically and can be found with `tools/stream_probe.py`, but are not skipped)
- Embedded YouTube is limited by QtWebEngine and shares a window with VLC (see [known risk](#youtube))
- The phone remote works on the local network only, over plain HTTP
- YouTube search relies on a link format that YouTube does not document and may change
- Single-window design (no multi-monitor support planned currently)

## Roadmap

- [ ] Auto-skip channels that the health check marks as dead
- [x] Phone remote control (QR code)
- [x] Simple EPG support
- [x] Brightness overlay, standby from the phone, settings on the phone, YouTube volume display
- [ ] Favorites / recently watched
- [ ] Better YouTube integration (or switch to a more robust web engine)
- [ ] System tray support
- [ ] Packaging (Windows .exe / Linux AppImage)
- [ ] More themes

## License

No license file yet. Feel free to use and modify for personal purposes.

---

Questions or suggestions? Open an issue.
