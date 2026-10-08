# -*- coding: utf-8 -*-
"""Integrációs teszt a valódi alkalmazással (offscreen Qt, hamis VLC nélkül is):
mindig bekapcsolt távirányító, fényerő-fedőréteg, készenlét telefonról, beállítások telefonról,
külön ablakos YouTube rendszer-hangereje."""
import json, os, sys, tempfile, threading, time, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["HOME"] = tempfile.mkdtemp()
os.environ.pop("TVBOX_EPG", None)
import tvbox.config as cfg
cfg.CONFIG_PATH = os.path.join(os.environ["HOME"], "s.json")
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
app = QApplication([])
import tvbox.app as A
from tvbox.config import SETTINGS_SCHEMA
from tvbox.dimmer import dim_alpha_for
from tvbox import sysvol

FAILS = []
def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond: FAILS.append(msg)

w = A.TVBox(); w.resize(1280, 720); w.show(); QTest.qWait(2200)
srv = w._remote_server

# ---------------------------------------------------------------- mindig bekapcsolt funkciók
keys = [s["key"] for s in SETTINGS_SCHEMA]
check("remote_enabled" not in keys and "youtube_adblock" not in keys, "a két beállítás kikerült a sémából")
check(srv is not None and srv.running, "a telefonos távirányító magától elindult (nincs rá beállítás)")
check("remote_enabled" not in w.settings_data and "youtube_adblock" not in w.settings_data, "nincs a settings_data-ban")

def call(path, body=None):
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (srv.port, path),
        data=json.dumps(body).encode() if body is not None else None,
        headers={"X-Token": srv.token, "Content-Type": "application/json"}, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, None

def hcall(path, body=None):
    """HTTP-hívás háttérszálon, közben pörgeti a Qt eseményhurkot."""
    out = {}
    t = threading.Thread(target=lambda: out.update(r=call(path, body))); t.start()
    while t.is_alive(): QTest.qWait(20)
    QTest.qWait(80)
    return out["r"]

# ---------------------------------------------------------------- fényerő
ov = lambda: w._dim_overlay
check(ov() is None or not ov().isVisible(), "100%-on nincs fedőréteg (az ablak el sem jelenik)")
w.settings_data["brightness"] = 50; w._apply_setting("brightness", 50); QTest.qWait(100)
check(ov() is not None and ov().isVisible(), "50%-on megjelenik a fedőréteg")
check(ov().alpha == dim_alpha_for(50) == 128, "50%% fényerő = 50%%-os fekete fedés (alfa %s)" % ov().alpha)
check(bool(ov().windowFlags() & Qt.WindowTransparentForInput) and bool(ov().windowFlags() & Qt.WindowStaysOnTopHint),
      "a fedőréteg átengedi a bemenetet és legfelül van")
scr = QApplication.primaryScreen().geometry()
check(ov().geometry() == scr, "a fedőréteg a teljes képernyőt takarja (%s)" % ov().geometry())
w.settings_data["brightness"] = 20; w._apply_setting("brightness", 20); QTest.qWait(50)
check(ov().alpha == dim_alpha_for(20) == 204, "20%% fényerő = 80%%-os fedés (alfa %s)" % ov().alpha)
check([dim_alpha_for(p) for p in (100, 90, 50, 20)] == [0, 26, 128, 204], "a leképezés lineáris")
w.settings_data["brightness"] = 100; w._apply_setting("brightness", 100); QTest.qWait(50)
check(not ov().isVisible(), "visszaállítva 100%-ra eltűnik a fedőréteg")

# ---------------------------------------------------------------- beállítások telefonról
st, state = hcall("/api/state")
check("settings" in state and state["settings"]["brightness"] == 8, "az állapot tartalmazza a beállítás-indexeket (brightness=100% -> 8)")
st, cat = hcall("/api/channels")
check([x["k"] for x in cat["settings"]] == keys, "a katalógus a teljes beállítás-listát adja")
before = w.settings_data["brightness"]
st, _ = hcall("/api/cmd", {"cmd": "setting", "key": "brightness", "dir": -1})
check(st == 200 and w.settings_data["brightness"] == 90, "telefonról léptetett fényerő: %s -> %s" % (before, w.settings_data["brightness"]))
check(ov() is not None and ov().isVisible() and ov().alpha == dim_alpha_for(90), "a TV képe azonnal sötétedik")
st, state = hcall("/api/state")
check(state["settings"]["brightness"] == 7, "a telefon az új értéket látja")
hcall("/api/cmd", {"cmd": "setting", "key": "brightness", "dir": 1}); QTest.qWait(50)
st, _ = hcall("/api/cmd", {"cmd": "setting", "key": "theme", "dir": 1})
check(w.settings_data["theme"] == "aurora", "téma váltás telefonról")
hcall("/api/cmd", {"cmd": "setting", "key": "theme", "dir": -1})
hcall("/api/cmd", {"cmd": "setting", "key": "brightness", "dir": 1})            # a felső szélen nem lép tovább
check(w.settings_data["brightness"] == 100, "a lista szélén megáll")
w.open_settings(); QTest.qWait(800)       # a TV-ről indított változás legfeljebb ~0,5 mp-et késik a telefonon
st, state = hcall("/api/state"); check(state["settings_open"] is True, "a telefon tudja, hogy a TV-n nyitva a panel")
hcall("/api/cmd", {"cmd": "setting", "key": "animations", "dir": 1}); QTest.qWait(100)
check(w._settings_cursor == keys.index("animations") and w.settings_data["animations"] is False,
      "nyitott panelnél a TV-n a kiemelés a módosított sorra ugrik")
hcall("/api/cmd", {"cmd": "setting", "key": "animations", "dir": -1}); w.close_settings(); QTest.qWait(300)
# méret
sp = w.settings_panel
check(sp.width() >= 560 and sp.height() > 8 * 40, "a TV-s beállítás-panel nagyobb (%dx%d)" % (sp.width(), sp.height()))

# ---------------------------------------------------------------- készenlét
w.settings_data["brightness"] = 70; w._apply_setting("brightness", 70)
vol_before = w.volume
st, _ = hcall("/api/cmd", {"cmd": "power", "state": "off", "held": 200})
check(st == 400 and not w.standby, "rövid nyomás nem kapcsol ki (400)")
xset_calls = []
w._screen_power = lambda on: xset_calls.append(on)
st, _ = hcall("/api/cmd", {"cmd": "power", "state": "off", "held": 2000})
check(st == 200 and w.standby, "2 mp-es nyomás: készenlétbe lép")
check(ov().isVisible() and ov().alpha == 255, "teljesen fekete képernyő készenlétben")
check(xset_calls == [False], "a monitor-kikapcsolás meghívódik")
check(w._play_gen is not None and not w.loading_card.isVisible(), "a lejátszás leállt, nincs töltő-kártya")
gen = w._play_gen
w.play_channel("3"); check(w._play_gen == gen, "készenlétben a play_channel() hatástalan")
st, state = hcall("/api/state"); check(state["standby"] is True, "a telefon készenlétet lát")
ch_before = w.current_key
hcall("/api/cmd", {"cmd": "zap", "dir": 1}); hcall("/api/cmd", {"cmd": "volume", "delta": 5})
hcall("/api/cmd", {"cmd": "key", "name": "menu"}); hcall("/api/cmd", {"cmd": "digit", "value": "5"})
check(w.current_key == ch_before and not w.menu_visible and w.volume == vol_before, "készenlétben minden más parancs figyelmen kívül marad")
st, _ = hcall("/api/cmd", {"cmd": "power", "state": "on", "held": 2000})
QTest.qWait(500)
check(st == 200 and not w.standby, "2 mp-es nyomás: bekapcsol")
check(ov().isVisible() and ov().alpha == dim_alpha_for(70), "visszatér a beállított fényerő (%s)" % ov().alpha)
check(xset_calls == [False, True], "a monitor visszakapcsol")
check(w._play_gen > gen, "a lejátszás újraindult")
# billentyűzettel is felébreszthető
hcall("/api/cmd", {"cmd": "power", "state": "off", "held": 2000})
check(w.standby, "újra készenlét")
QTest.keyClick(w, Qt.Key_Left); QTest.qWait(400)
check(not w.standby and w.current_key == ch_before, "bármely billentyű felébreszt, és nem vált csatornát")

# ---------------------------------------------------------------- külső YouTube: rendszer-hangerő
class FakeBackend:
    name = "fake"
    def __init__(s): s.v, s.m, s.n = 30, False, 0
    def get(s): s.n += 1; return s.v, s.m
    def set(s, p): s.v = p
    def toggle_mute(s): s.m = not s.m
class FakeProc:
    def __init__(s): self_alive = True; s.alive = True; s.terminated = False
    def poll(s): return None if s.alive else 0
    def terminate(s): s.terminated = True; s.alive = False
fb = FakeBackend(); w.sysvol = sysvol.SystemVolume(backend=fb)
proc = FakeProc(); w._external_processes["youtube"] = proc
w.volume = 77; w.settings_data["brightness"] = 100; w._apply_setting("brightness", 100)
st, state = hcall("/api/state"); QTest.qWait(1800); st, state = hcall("/api/state")       # az első beolvasás 1-2 ütemezői ciklus
check(state["active"] == "youtube" and state["vol_scope"] == "system", "külön ablakos YouTube: a telefon YouTube-ot és rendszer-hangerőt jelez")
check(state["volume"] == 30, "a megjelenített hangerő a gépé (30%%), nem a VLC-é (77%%): %s" % state["volume"])
hcall("/api/cmd", {"cmd": "volume", "delta": 5}); QTest.qWait(500)
st, state = hcall("/api/state")
check(fb.v == 35 and state["volume"] == 35, "a + gomb a gép hangerejét állítja és a telefon 35%%-ot mutat (fb=%s, állapot=%s)" % (fb.v, state["volume"]))
hcall("/api/cmd", {"cmd": "volume", "delta": -10}); QTest.qWait(500)
st, state = hcall("/api/state"); check(fb.v == 25 and state["volume"] == 25, "a − gomb után 25%%: %s" % state["volume"])
hcall("/api/cmd", {"cmd": "mute"}); QTest.qWait(500)
st, state = hcall("/api/state"); check(fb.m is True and state["muted"] is True, "némítás a gépen, a telefon is látja")
fb.v = 60; QTest.qWait(2600); st, state = hcall("/api/state")
check(state["volume"] == 60, "ha a gépen máshol állítják, a telefon utánköveti (%s)" % state["volume"])
check(w.volume == 77, "a VLC-hangerő érintetlen maradt")
# készenlét közben a YouTube bezárul
hcall("/api/cmd", {"cmd": "power", "state": "off", "held": 2000}); QTest.qWait(300)
check(proc.terminated, "készenlétbe lépve a külön YouTube-ablak bezárul")
gen = w._play_gen
w._check_external_processes(); QTest.qWait(300)
check(w.standby and w._play_gen == gen, "a bezárt YouTube-ablak készenlétben nem indít lejátszást")
w.leave_standby(); QTest.qWait(400)

# ---------------------------------------------------------------- kilépés fedőréteggel
w.settings_data["brightness"] = 40; w._apply_setting("brightness", 40); QTest.qWait(100)
check(ov().isVisible(), "a fedőréteg látszik kilépés előtt")
done = []
QTimer.singleShot(200, w.close)
QTimer.singleShot(4000, lambda: (done.append("TIMEOUT"), app.quit()))
app.aboutToQuit.connect(lambda: done.append("quit"))
app.exec_()
check(done and done[0] == "quit", "látható fedőréteggel is kilép az alkalmazás (%s)" % done)
print("\nBUKOTT: %d" % len(FAILS) if FAILS else "\nMINDEN RENDBEN")
sys.exit(1 if FAILS else 0)
