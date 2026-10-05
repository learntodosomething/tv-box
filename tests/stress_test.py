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
import tvbox.app as appmod

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
# FONTOS: a teszt SOHA ne indítson külső programot (Brave/YouTube kiosk) -
# az minimalizálná az ablakot és megzavarná a mérést.
launches = [0]
def _no_launch(key):
    launches[0] += 1
win._launch_external_app = _no_launch
if not args.allow_remote:
    # Alapból NEM nyitunk valódi hálózati portot (Windows tűzfal-kérdés, külső elérés).
    win.start_remote = lambda: False
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

last_beat = [time.perf_counter()]
def gui_watchdog():
    dumped_for = None
    while not stop_flag.is_set():
        time.sleep(0.5)
        gap = time.perf_counter() - last_beat[0]
        if gap > 2.0 and dumped_for != last_beat[0]:
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
for _ in range(60):
    QTest.qWait(100)
    if not any(getattr(getattr(win, n), "_hiding", False) for n in
               ("info_card", "volume_osd", "number_osd", "preview_osd", "remote_panel", "loading_card", "error_card")):
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
print("kimenet: %s" % ("HIBA" if problems else "RENDBEN"))
if problems:
    print("részletek a naplóban (GUI-fagyás esetén a szálak verme is): " + LOG_PATH)
for p in problems: print(" -", p)
for e in errors[:3]: print("\n--- kivétel ---\n" + e)
sys.exit(1 if problems else 0)
