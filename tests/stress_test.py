#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TV Box stressz-teszt (PyQt5 szükséges; VLC nem, ha --fake-vlc).

    python tests/stress_test.py --seconds 60            # álló (offscreen) UI + hamis VLC
    python tests/stress_test.py --seconds 120 --real-vlc # valódi VLC (kell kijelző)

Mit csinál:
  * ~150-300 véletlen billentyű/mp (nyilak nyomva tartva, számok, M/B/S/H,
    Enter, Backspace, hangerő ...) a főablakra,
  * egy háttérszál a libVLC-t utánozva véletlenszerűen Playing / Buffering /
    Error / EndReached eseményeket lő (valódi VLC-nél is külön szálról jönnek),
  * méri: billentyű-kezelés késése (átlag/p99/max), az eseményhurok
    "fagyásait" (heartbeat), memória-növekedést (RSS), elkapott Python
    kivételeket, és a végén állapot-invariánsokat ellenőriz.
  * EPG: egy hibázó (500 / csepegtető / sérült / üres / jó) helyi HTTP-szerverről töltött, nagy XMLTV
    folyamatos újratöltése, az EPG ki/be kapcsolgatása, 'I' billentyű; --allow-remote esetén
    párhuzamos HTTP-terhelés a telefonos távirányítón (állapot, lista, EPG, parancsok).
  * KÉSZENLÉT / FÉNYERŐ / BEÁLLÍTÁSOK: véletlenszerű ki/bekapcsolás (billentyűzetről és - --allow-remote
    esetén - a telefonos parancsokkal), fényerő-léptetés, beállítások léptetése telefonról;
    a végén: nincs beragadt készenlét, a fedőréteg állapota egyezik a fényerővel.
Kilépési kód: 0 = minden rendben, 1 = hiba/figyelmeztetés.
A tesztek a beállításfájlt ideiglenes helyre írják, a sajátodat nem bántják.
"""
import argparse, faulthandler, os, random, sys, tempfile, threading, time, types

ap = argparse.ArgumentParser()
ap.add_argument("--seconds", type=int, default=60)
ap.add_argument("--real-vlc", action="store_true")
ap.add_argument("--rate", type=int, default=200, help="billentyű/mp")
ap.add_argument("--seed", type=int, default=None)
ap.add_argument("--allow-web", action="store_true", help="a beépített YouTube (QtWebEngine) útvonalat is tesztelje - ÖNÁLLÓ futtatásban érdemes, mert a Chromium ismert összeomlás-forrás (alapból tiltva)")
ap.add_argument("--allow-remote", action="store_true", help="a telefonos távirányító HTTP-szerverét is elindíthatja (tűzfal-kérdést válthat ki)")
ap.add_argument("--no-chaos", action="store_true", help="ne lőjünk szimulált VLC-eseményeket (csak billentyűk)")
ap.add_argument("--fake-block", type=float, default=0.8, help="hamis VLC: set_media max. blokkolása mp-ben")
ap.add_argument("--dump-gap", type=float, default=2.0, help="ennyi mp-es GUI-szál-fagyásnál írja ki az összes szál vermét a naplóba (vadászathoz: 0.4)")
ap.add_argument("--local-streams", action="store_true", help="a csatornák URL-jeit helyi streamekre cseréli (ffmpeg HLS: jó videó/hang, 404, lassú, halott) - valódi VLC-hez (--real-vlc) hasznos, az internetes adások nélkül")
ap.add_argument("--no-epg", action="store_true", help="az EPG-t ne terhelje (alapból egy hibázó helyi EPG-szerverről tölt, folyamatosan újratöltve)")
ap.add_argument("--epg-extra", type=int, default=150, help="az EPG-fájl további (nem használt) csatornáinak száma")
ap.add_argument("--remote-threads", type=int, default=3, help="--allow-remote esetén ennyi szál terheli a telefonos HTTP-szervert")
args = ap.parse_args()

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if not args.real_vlc:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# --- diagnosztika: natív összeomlásnál is marad nyom -------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(HERE, "stress_log.txt")
KEYS_PATH = os.path.join(HERE, "stress_keys.txt")
_log = open(LOG_PATH, "w", buffering=1, encoding="utf-8")
faulthandler.enable(file=_log, all_threads=True)    # access violation => Python-stack a fájlban
_keys = open(KEYS_PATH, "w", buffering=1, encoding="utf-8")
print("napló:", LOG_PATH, "\n      ", KEYS_PATH)

# ---------------------------------------------------------------- hamis VLC
class _U:  # e.u.new_cache
    def __init__(self, pct): self.new_cache = pct
class _Ev:
    def __init__(self, pct=100.0): self.u = _U(pct)

def _install_fake_vlc():
    m = types.ModuleType("vlc")
    class EventType:
        MediaPlayerPlaying, MediaPlayerEncounteredError = 1, 2
        MediaPlayerBuffering, MediaPlayerEndReached = 3, 4
    class Media:
        def __init__(self, url): self.url, self.opts = url, []
        def add_option(self, o): self.opts.append(o)
    class EM:
        def __init__(self): self.cbs = {}
        def event_attach(self, t, cb): self.cbs[t] = cb
    class Player:
        def __init__(self):
            self.em, self.plays, self.stops, self.media = EM(), 0, 0, None
        def event_manager(self): return self.em
        def set_media(self, md):
            time.sleep(random.uniform(0, args.fake_block))   # lassú szerver utánzása
            self.media = md
        def play(self): self.plays += 1
        def stop(self): self.stops += 1
        def release(self): pass
        def audio_set_volume(self, v): pass
        def audio_set_mute(self, v): pass
        def set_xwindow(self, w): pass
        def set_hwnd(self, w): pass
        def set_nsobject(self, w): pass
    class Instance:
        def __init__(self, *a): pass
        def media_new(self, url): return Media(url)
        def media_player_new(self): return Player()
        def release(self): pass
    m.EventType, m.Instance = EventType, Instance
    sys.modules["vlc"] = m

if not args.real_vlc:
    _install_fake_vlc()

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
import tvbox.config as cfg
cfg.CONFIG_PATH = os.path.join(tempfile.mkdtemp(), "stress_settings.json")

# ------------------------------------------------ EPG előkészítés (az app importja ELŐTT)
epg_stats = {"loaded": 0, "failed": 0, "ui_ms": [], "http_hits": 0, "http_modes": {}}
epg_server = None
if not args.no_epg:
    sys.path.insert(0, HERE)
    import http.server
    import tvbox.epg_core as ecore
    from epg_fixture import make_xmltv
    from tvbox.channels import CHANNEL_DATA, RADIO_DATA
    _tmp_epg = tempfile.mkdtemp()
    ecore.EPG_DIR = os.path.join(_tmp_epg, "cache")
    ecore.EPG_DOWNLOAD_TIMEOUT_S, ecore.EPG_DOWNLOAD_TOTAL_S = 2, 4
    ecore.EPG_REFRESH_S, ecore.EPG_TICK_MS = 4, 1000
    _names = [n for _, e in CHANNEL_DATA + RADIO_DATA for n, _u in e]
    _epg_file = os.path.join(_tmp_epg, "src.xml.gz")
    _n = make_xmltv(_epg_file, _names, hours_back=6, hours_fwd=72, step_minutes=15, gz=True,
                    extra_channels=args.epg_extra)
    _good = open(_epg_file, "rb").read()
    print("EPG fixture: %d műsor, %.1f MB (tömörítve)" % (_n, len(_good) / 1048576))

    class _EpgHandler(http.server.BaseHTTPRequestHandler):
        seq = 0
        def log_message(self, *a): pass
        def do_GET(self):
            epg_stats["http_hits"] += 1
            type(self).seq += 1
            mode = ["ok", "ok", "500", "ok", "drip", "corrupt", "empty", "ok", "truncated"][type(self).seq % 9]
            epg_stats["http_modes"][mode] = epg_stats["http_modes"].get(mode, 0) + 1
            try:
                if mode == "500":
                    self.send_response(500); self.end_headers(); return
                if mode == "empty":
                    self.send_response(200); self.send_header("Content-Length", "0"); self.end_headers(); return
                body = _good
                if mode == "corrupt":
                    body = b"\x1f\x8b" + os.urandom(2000)
                if mode == "truncated":
                    body = _good[: len(_good) // 3]
                if mode == "drip":
                    self.send_response(200); self.send_header("Content-Length", str(len(_good))); self.end_headers()
                    for i in range(60):
                        self.wfile.write(_good[i * 10:(i + 1) * 10]); self.wfile.flush(); time.sleep(0.2)
                    return
                self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers()
                self.wfile.write(body)
            except OSError:
                pass

    epg_server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _EpgHandler)
    threading.Thread(target=epg_server.serve_forever, daemon=True).start()
    os.environ["TVBOX_EPG"] = "http://127.0.0.1:%d/epg.xml.gz" % epg_server.server_address[1]
else:
    os.environ.pop("TVBOX_EPG", None)

stream_stats = {"hits": {}}
_ffmpegs = []
if args.local_streams:
    import http.server, shutil, subprocess, socketserver
    import tvbox.channels as chmod
    _hls = tempfile.mkdtemp()
    if not shutil.which("ffmpeg"):
        sys.exit("--local-streams: nincs ffmpeg a PATH-on")
    def _start_ffmpeg(name, with_video):
        out = os.path.join(_hls, name); os.makedirs(out)
        cmd = ["ffmpeg", "-loglevel", "error", "-re"]
        if with_video:
            cmd += ["-f", "lavfi", "-i", "testsrc=size=640x360:rate=25"]
        cmd += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100"]
        if with_video:
            cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency", "-g", "50", "-pix_fmt", "yuv420p"]
        cmd += ["-c:a", "aac", "-b:a", "64k", "-f", "hls", "-hls_time", "2", "-hls_list_size", "6",
                "-hls_flags", "delete_segments+omit_endlist", os.path.join(out, "index.m3u8")]
        _ffmpegs.append(subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    _start_ffmpeg("video", True); _start_ffmpeg("audio", False)

    class _StreamHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k): super().__init__(*a, directory=_hls, **k)
        def log_message(self, *a): pass
        def do_GET(self):
            kind = self.path.split("/")[1] if self.path.count("/") else ""
            stream_stats["hits"][kind] = stream_stats["hits"].get(kind, 0) + 1
            if kind == "dead":
                self.connection.close(); return
            if kind == "missing":
                self.send_response(404); self.end_headers(); return
            if kind == "slow":
                time.sleep(2.5)                      # lassú szerver
                self.send_response(504); self.end_headers(); return
            try:
                super().do_GET()
            except (ConnectionError, BrokenPipeError):
                pass
    class _TS(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
    _stream_srv = _TS(("127.0.0.1", 0), _StreamHandler)
    threading.Thread(target=_stream_srv.serve_forever, daemon=True).start()
    _base = "http://127.0.0.1:%d" % _stream_srv.server_address[1]
    def _pick(i, audio):
        good = "/audio/index.m3u8" if audio else "/video/index.m3u8"
        return {0: good, 1: good, 2: "/missing/x.m3u8", 3: good, 4: "/slow/x.m3u8", 5: "/dead/x.m3u8"}[i % 6]
    for data, audio in ((chmod.CHANNEL_DATA, False), (chmod.RADIO_DATA, True)):
        n = 0
        for ci, (cat, entries) in enumerate(data):
            for ei, (nm, _u) in enumerate(entries):
                entries[ei] = (nm, _base + _pick(n, audio)); n += 1
    time.sleep(6)       # az első HLS-szegmensek elkészültéig
    print("helyi streamek:", _base)

import tvbox.app as appmod
if args.real_vlc and not os.environ.get('DISPLAY') is None:
    import tvbox.config as _c
    _c.VLC_BASE_ARGS[:] = list(_c.VLC_BASE_ARGS) + ['--aout=dummy']      # nincs hangkártya a tesztgépen
    appmod.VLC_BASE_ARGS = _c.VLC_BASE_ARGS
if not args.no_epg:
    import tvbox.epg as epgmod
    epgmod.EPG_REFRESH_S, epgmod.EPG_TICK_MS = 4, 1000

seed = args.seed if args.seed is not None else random.randrange(10**6)
rnd = random.Random(seed)
print("seed:", seed, "| másodperc:", args.seconds, "| ráta:", args.rate, "/s |",
      "VALÓDI VLC" if args.real_vlc else "hamis VLC")

errors, lat_ms, heartbeat_gaps = [], [], []
def _hook(t, v, tb):
    import traceback
    errors.append("".join(traceback.format_exception(t, v, tb)))
sys.excepthook = _hook

def rss_mb():
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes
            class PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            pmc = PMC(); pmc.cb = ctypes.sizeof(PMC)
            h = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb)
            return pmc.WorkingSetSize / 1048576
        except Exception:
            return 0.0
    try:
        for ln in open("/proc/self/status"):
            if ln.startswith("VmRSS"): return int(ln.split()[1]) / 1024
    except OSError:
        pass
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        return 0.0

app = QApplication(sys.argv)
shared = appmod.QSharedMemory("HU.TVBox.StressTest.%d" % os.getpid())
win = appmod.TVBox()
if not args.no_epg:
    def _timed(name):
        orig = getattr(win, name)
        def wrapper(*a, **k):
            t0 = time.perf_counter()
            try:
                return orig(*a, **k)
            finally:
                epg_stats["ui_ms"].append(((time.perf_counter() - t0) * 1000, name))
        setattr(win, name, wrapper)
    for _n in ("_epg_rebuild_remote_map", "_refresh_menu_epg", "_update_epg_info", "_on_epg_loaded"):
        _timed(_n)
    _ol, _of = win._on_epg_loaded, win._on_epg_failed
    win._epg_signals.loaded.disconnect(); win._epg_signals.failed.disconnect()
    def _loaded(d, g): epg_stats["loaded"] += 1; _ol(d, g)
    def _failed(m, g): epg_stats["failed"] += 1; _of(m, g)
    win._epg_signals.loaded.connect(_loaded); win._epg_signals.failed.connect(_failed)
# FONTOS: a teszt SOHA ne indítson külső programot (Brave/YouTube kiosk) -
# az minimalizálná az ablakot és megzavarná a mérést.
launches = [0]
def _no_launch(key):
    launches[0] += 1
win._launch_external_app = _no_launch
if not args.allow_remote:
    # Alapból NEM nyitunk valódi hálózati portot (Windows tűzfal-kérdés, külső elérés).
    win.start_remote = lambda: False
if args.allow_remote:
    if not win.start_remote():
        print("FIGYELEM: a telefonos szerver nem indult el"); args.allow_remote = False
if not args.allow_web:
    win._show_web_app = lambda key: launches.__setitem__(0, launches[0] + 1)
win.show()
QTest.qWait(500)

# ------------------------------------------------ libVLC-szerű háttérszál
stop_flag = threading.Event()
def chaos():
    cbs = win.player.event_manager().cbs if not args.real_vlc else None
    et = appmod.vlc.EventType
    while not stop_flag.is_set():
        time.sleep(rnd.uniform(0.005, 0.06))
        if cbs is None:        # valódi VLC-nél a szimulált események a jelzéseken át mennek
            sig = win.player_signals
            r = rnd.random()
            if r < .45: sig.buffering.emit(rnd.choice([0, 12, 40, 77, 99, 100, 100]))
            elif r < .7: sig.playing.emit()
            elif r < .85: sig.error.emit()
            else: sig.ended.emit()
            continue
        r = rnd.random()
        if r < .45 and et.MediaPlayerBuffering in cbs:
            cbs[et.MediaPlayerBuffering](_Ev(rnd.choice([0, 12, 40, 77, 99, 100, 100])))
        elif r < .7: cbs[et.MediaPlayerPlaying](_Ev())
        elif r < .85: cbs[et.MediaPlayerEncounteredError](_Ev())
        else: cbs[et.MediaPlayerEndReached](_Ev())
t = threading.Thread(target=chaos, daemon=True)
if not args.no_chaos:
    t.start()

# ------------------------------------------------ billentyű-vihar
KEYS = ([Qt.Key_Left] * 12 + [Qt.Key_Right] * 12 + [Qt.Key_Up] * 4 + [Qt.Key_Down] * 4 +
        [Qt.Key_M] * 5 + [Qt.Key_B] * 3 + [Qt.Key_S] * 2 + [Qt.Key_H] + [Qt.Key_R] * 2 + [Qt.Key_N] + [Qt.Key_Return] * 4 +
        [Qt.Key_I] * 4 +
        [Qt.Key_Backspace] * 2 + [Qt.Key_V, Qt.Key_Space] +
        [getattr(Qt, "Key_%d" % d) for d in range(10)] * 2)

def send_key():
    k = rnd.choice(KEYS)
    # Esc/Q-t SZÁNDÉKOSAN nem küldünk (kétszer = kilépés).
    t0 = time.perf_counter()
    _keys.write("%.3f %s\n" % (t0, k))
    QTest.keyClick(win, k)
    lat_ms.append((time.perf_counter() - t0) * 1000)

key_timer = QTimer(); key_timer.timeout.connect(send_key); key_timer.start(max(1, int(1000 / args.rate)))

# ------------------------------------------------ EPG-káosz (GUI-szálon) és HTTP-terhelés
if not args.no_epg:
    def epg_chaos():
        r = rnd.random()
        if r < .45:
            win._epg_start_load(True)
        elif r < .70:
            val = rnd.random() < .5
            win.settings_data["epg"] = val; win._apply_setting("epg", val)
        elif r < .85:
            win._epg_tick()
        else:
            win.show_epg_info()
    epg_timer = QTimer(); epg_timer.timeout.connect(epg_chaos); epg_timer.start(350)

# ------------------------------------------------ készenlét / fényerő káosz (GUI szálon)
win._screen_power = lambda on: None                  # a teszt ne hívjon xset-et
power_stats = {"standby_in": 0, "standby_out": 0}
def power_chaos():
    r = rnd.random()
    if r < .30:
        win.enter_standby(); power_stats["standby_in"] += 1
    elif r < .55:
        win.leave_standby(); power_stats["standby_out"] += 1
    elif r < .85:
        v = rnd.choice([20, 30, 40, 50, 60, 70, 80, 90, 100])
        win.settings_data["brightness"] = v; win._apply_setting("brightness", v)
    else:
        win._remote_step_setting(rnd.choice(["brightness", "theme", "animations", "info_card_ms"]), rnd.choice([-1, 1]))
power_timer = QTimer(); power_timer.timeout.connect(power_chaos); power_timer.start(700)

http_stats = {"n": 0, "err": [], "lat": []}
if args.allow_remote:
    import json, urllib.request, urllib.error
    _srv = win._remote_server
    _port = _srv.port
    http_stats["rotations"] = 0
    _CMDS = [{"cmd": "key", "name": n} for n in ("up", "down", "left", "right", "enter", "menu", "settings", "help", "info", "back", "esc")] + \
            [{"cmd": "digit", "value": str(d)} for d in range(10)] + \
            [{"cmd": "volume", "delta": 5}, {"cmd": "volume", "delta": -5}, {"cmd": "mute"},
             {"cmd": "zap", "dir": 1}, {"cmd": "zap", "dir": -1}, {"cmd": "mode", "mode": "tv"}, {"cmd": "mode", "mode": "radio"},
             {"cmd": "channel", "mode": "tv", "key": "3"}, {"cmd": "channel", "mode": "radio", "key": "2"},
             {"cmd": "power", "state": "off", "held": 2000}, {"cmd": "power", "state": "on", "held": 2000},
             {"cmd": "power", "state": "on", "held": 2000}, {"cmd": "setting", "key": "brightness", "dir": -1},
             {"cmd": "setting", "key": "brightness", "dir": 1}, {"cmd": "setting", "key": "theme", "dir": 1}]
    def _http(path, body=None, tok=None):
        data = json.dumps(body).encode() if body is not None else None
        used = tok or _srv.token             # az élő token (a billentyűvihar 'N'-nel cserélgeti)
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (_port, path), data=data,
                                     method="POST" if data else "GET",
                                     headers={"X-Token": used, "Content-Type": "application/json"})
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw = resp.read(); code = resp.status
            if path.startswith("/api/") and path != "/api/cmd":
                json.loads(raw.decode("utf-8"))        # érvényes JSON-t kell kapnunk
        except urllib.error.HTTPError as e:
            code = e.code
            if code in (401, 429) and not tok and _srv.token != used:
                http_stats["rotations"] += 1         # a kérés közben cserélődött a token: ez rendben van
                return 200
        except Exception as e:
            http_stats["err"].append("%s %s: %r" % ("POST" if data else "GET", path, e)); return None
        http_stats["lat"].append((time.perf_counter() - t0) * 1000); http_stats["n"] += 1
        return code
    def hammer(i):
        rr = random.Random(seed * 100 + i)
        while not stop_flag.is_set():
            time.sleep(rr.uniform(0, 0.02))
            r = rr.random()
            if r < .30: code = _http("/api/state")
            elif r < .40: code = _http("/api/channels")
            elif r < .55: code = _http("/api/epg")
            elif r < .95: code = _http("/api/cmd", rr.choice(_CMDS))
            else: code = _http("/api/cmd", {"cmd": "key", "name": "quit"})           # szándékosan hibás
            if code not in (200, 400, None):
                http_stats["err"].append("váratlan HTTP %s" % code)
    for _i in range(args.remote_threads):
        threading.Thread(target=hammer, args=(_i,), daemon=True).start()

last_beat = [time.perf_counter()]
def gui_watchdog():
    dumped_for = None
    while not stop_flag.is_set():
        time.sleep(min(0.5, args.dump_gap / 4))
        gap = time.perf_counter() - last_beat[0]
        if gap > args.dump_gap and dumped_for != last_beat[0]:
            dumped_for = last_beat[0]
            _log.write("\n===== GUI-szál %.1f mp-e nem válaszol - minden szál veremtartalma =====\n" % gap)
            faulthandler.dump_traceback(file=_log, all_threads=True)
            _log.flush()
threading.Thread(target=gui_watchdog, daemon=True).start()
def beat():
    now = time.perf_counter(); heartbeat_gaps.append((now - last_beat[0]) * 1000); last_beat[0] = now
hb = QTimer(); hb.timeout.connect(beat); hb.start(20)

rss0 = rss_mb(); samples = []
def sample(): samples.append(rss_mb())
st = QTimer(); st.timeout.connect(sample); st.start(2000)

QTimer.singleShot(args.seconds * 1000, app.quit)
t_start = time.time(); app.exec_()
key_timer.stop(); stop_flag.set()

# ------------------------------------------------ lecsengés + invariánsok
# Lecsengés: az animációk/időzítők befejezéséig várunk (max. 6 mp)
power_timer.stop()
if not args.no_epg:
    epg_timer.stop()
stop_flag.set() if args.allow_remote else None
QTest.qWait(300)
win.leave_standby()
QTest.qWait(300)
for _ in range(80):
    QTest.qWait(100)
    if (not any(getattr(getattr(win, n), "_hiding", False) for n in
                ("info_card", "volume_osd", "number_osd", "preview_osd", "remote_panel", "loading_card", "error_card"))
            and getattr(win, "_menu_slide_anim", None) is None
            and not (not args.no_epg and win._epg_loading)):
        break
problems = []
if win.menu_visible != win.menu_panel.isVisible():
    problems.append("menü-állapot eltér: menu_visible=%s, panel látszik=%s" % (win.menu_visible, win.menu_panel.isVisible()))
if (win.video_frame.width(), win.video_frame.height()) != (win.width(), win.height()):
    problems.append("videófelület mérete eltér az ablaktól: %sx%s vs %sx%s" % (
        win.video_frame.width(), win.video_frame.height(), win.width(), win.height()))
stuck = [n for n in ("info_card", "volume_osd", "number_osd", "preview_osd", "remote_panel", "loading_card", "error_card")
         if getattr(win, n).isVisible() and getattr(getattr(win, n), "_hiding", False)]
if stuck:
    problems.append("félbemaradt eltűnés-animáció: %s" % stuck)
if win.remote_panel_visible != win.remote_panel.isVisible() and not getattr(win.remote_panel, "_hiding", False):
    problems.append("QR-panel állapot eltér: remote_panel_visible=%s, látszik=%s" % (win.remote_panel_visible, win.remote_panel.isVisible()))
if win._preview_key is not None and not win.preview_timer.isActive():
    problems.append("az előnézet 'beragadt': kulcs=%s, de nem fut az időzítő" % win._preview_key)
if win._preview_key is None and win.preview_osd.isVisible() and not getattr(win.preview_osd, "_hiding", False):
    problems.append("az előnézeti kártya látszik, pedig nincs aktív előnézet")
if not args.no_epg:
    if win._epg_loading:
        problems.append("az EPG-betöltés jelzője beragadt (_epg_loading=True a leállás után is)")
    if epg_stats["loaded"] == 0:
        problems.append("az EPG egyszer sem töltődött be")
    if win.epg_data is None and win.epg_enabled():
        problems.append("az EPG engedélyezett, de nincs adat")
    if win.epg_data is not None:
        nm = win.channels[win.current_key][0] if win.current_key in win.channels else None
        if nm and win.settings_data.get("epg", True) and win.mode == "tv" and win.epg_data.has_channel(nm) \
                and win.epg_now_next(nm) == (None, None):
            problems.append("a csatornához van EPG-csatorna, de se most, se következő műsor")
    ui_slow = [x for x in epg_stats["ui_ms"] if x[0] > 120]
    if ui_slow:
        problems.append("lassú EPG-művelet a GUI-szálon: %s" % sorted(ui_slow, reverse=True)[:3])
if win.standby:
    problems.append("beragadt készenlét a teszt végén")
_ov = getattr(win, "_dim_overlay", None)
_want = win._current_dim_alpha()
_vis = bool(_ov is not None and _ov.isVisible())
if win._dim_supported() or _want >= 255:
    if (_want > 0) != _vis or (_vis and _ov.alpha != _want):
        problems.append("a fedőréteg állapota nem egyezik a fényerővel (várt alfa %s, látszik %s, alfa %s)"
                        % (_want, _vis, _ov.alpha if _ov else None))
if args.allow_remote:
    if http_stats["err"]:
        problems.append("%d HTTP-hiba a telefonos szerveren (első: %s)" % (len(http_stats["err"]), http_stats["err"][0]))
    if http_stats["lat"] and sorted(http_stats["lat"])[int(len(http_stats["lat"]) * .99)] > 800:
        problems.append("lassú telefonos szerver: p99 = %.0f ms" % sorted(http_stats["lat"])[int(len(http_stats["lat"]) * .99)])
if errors:
    problems.append("%d elkapott Python kivétel (első: lásd lent)" % len(errors))

def pct(a, p):
    a = sorted(a); return a[min(len(a) - 1, int(len(a) * p))] if a else 0
growth = (samples[-1] - rss0) if samples else 0
half = len(samples) // 2
late_growth = (samples[-1] - samples[half]) if len(samples) > 4 else 0
if heartbeat_gaps and max(heartbeat_gaps) > 750:
    problems.append("az eseményhurok %.0f ms-ra befagyott" % max(heartbeat_gaps))
if pct(lat_ms, .99) > 120:
    problems.append("lassú billentyű-kezelés: p99 = %.0f ms" % pct(lat_ms, .99))
if late_growth > 40:
    problems.append("memória nőtt a teszt 2. felében: +%.0f MB (szivárgás gyanú)" % late_growth)

print("\n===== EREDMÉNY =====")
print("billentyűk: %d | késés ms: átlag %.1f, p99 %.1f, max %.1f" % (
    len(lat_ms), sum(lat_ms) / max(1, len(lat_ms)), pct(lat_ms, .99), max(lat_ms or [0])))
print("heartbeat-rés ms: p99 %.0f, max %.0f (20 ms az ideális)" % (pct(heartbeat_gaps, .99), max(heartbeat_gaps or [0])))
print("memória: indulás %.0f MB -> vég %.0f MB (teljes +%.0f, 2. félidő +%.0f)" % (rss0, samples[-1] if samples else 0, growth, late_growth))
if not args.real_vlc:
    print("VLC play() hívások: %d (debounce nélkül ennyi lenne a billentyűk száma)" % win.player.plays)
print("kitiltott külső-app indítási kísérletek: %d | VLC munkaszál él: %s" % (launches[0], win.worker.is_alive()))
if not args.no_epg:
    ui = epg_stats["ui_ms"]
    by = {}
    for ms, n in ui: by.setdefault(n, []).append(ms)
    print("EPG: betöltés ok %d / hiba %d | szerver-kérések %d %s" % (
        epg_stats["loaded"], epg_stats["failed"], epg_stats["http_hits"], epg_stats["http_modes"]))
    for n, v in sorted(by.items()):
        print("   GUI-szál: %-26s hívás %5d | átlag %.2f ms | max %.1f ms" % (n, len(v), sum(v) / len(v), max(v)))
if args.allow_remote:
    lat = sorted(http_stats["lat"])
    print("telefonos szerver: %d kérés | késés ms: átlag %.1f, p99 %.1f, max %.1f | hiba: %d" % (
        http_stats["n"], sum(lat) / max(1, len(lat)), lat[int(len(lat) * .99)] if lat else 0, lat[-1] if lat else 0,
        len(http_stats["err"])))
if args.allow_remote:
    print("token-csere kérés közben (tolerálva): %d" % http_stats["rotations"])
if args.local_streams:
    print("helyi stream-kérések: %s" % stream_stats["hits"])
    for pr in _ffmpegs:
        try: pr.terminate()
        except Exception: pass
print("készenlét: be %d / ki %d | fényerő a végén: %s%%" % (power_stats["standby_in"], power_stats["standby_out"], win._brightness))
print("szálak a végén: %d" % threading.active_count())
print("kimenet: %s" % ("HIBA" if problems else "RENDBEN"))
if problems:
    print("részletek a naplóban (GUI-fagyás esetén a szálak verme is): " + LOG_PATH)
for p in problems: print(" -", p)
for e in errors[:3]: print("\n--- kivétel ---\n" + e)
sys.exit(1 if problems else 0)
