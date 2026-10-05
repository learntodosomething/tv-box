"""A telefonos távirányító Qt-oldali parancskezelése hamis PyQt5-tel (Qt nélkül futtatható)."""
import sys, os, json, importlib, types, urllib.request
from unittest import mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

KEYS = {n: i + 100 for i, n in enumerate(["Up", "Down", "Left", "Right", "Return", "Escape", "Backspace", "M", "B", "S", "H"] + list("0123456789"))}
EVENTS, TIMERS = [], []

class FakeKeyEvent:
    def __init__(s, t, key, mod, text): s.t, s.key, s.text = t, key, text

class FakeApp:
    @staticmethod
    def sendEvent(target, ev): EVENTS.append((target, ev.t, ev.key, ev.text))
    @staticmethod
    def focusWidget(): return None

class FakeTimer:
    def __init__(s, *a): s.timeout = mock.MagicMock()
    def start(s, *a): pass
    def stop(s): pass
    @staticmethod
    def singleShot(ms, fn): TIMERS.append((ms, fn))

class FakeUrl:
    def __init__(s, u): s.u = u

def load(youtube_embedded=True):
    for n in [k for k in sys.modules if k.startswith("tvbox")]: del sys.modules[n]
    for name in ("PyQt5", "PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWebEngineWidgets", "PyQt5.QtWebEngineCore"):
        m = mock.MagicMock(); m.__path__ = []; sys.modules[name] = m
    core = sys.modules["PyQt5.QtCore"]
    core.Qt = types.SimpleNamespace(NoModifier=0, AlignHCenter=1, AlignCenter=2, NoPen=3,
                                    **{"Key_" + k: v for k, v in KEYS.items()})
    core.QEvent = types.SimpleNamespace(KeyPress=6, KeyRelease=7)
    core.QTimer, core.QUrl, core.QObject = FakeTimer, FakeUrl, object
    sys.modules["PyQt5.QtGui"].QKeyEvent = FakeKeyEvent
    sys.modules["PyQt5.QtWidgets"].QApplication = FakeApp
    ext = importlib.import_module("tvbox.external_apps")
    if not youtube_embedded:
        ext.WEB_APP_ORDER[:] = []; ext.EXTERNAL_ORDER[:] = ["youtube"]
    return importlib.import_module("tvbox.remote_ui")

class Win:
    def __init__(s, ui):
        s.__class__ = type("Win", (Win, ui.RemoteMixin), {})
        s.sources = {
            "tv": {"icon": "📺", "label": "Televízió", "channels": {"1": ("M1", "u"), "2": ("M2", "u"), "3": ("RTL", "u")},
                   "categories": [("Közszolgálati", ["1", "2"]), ("Kereskedelmi", ["3"])], "current_key": "1"},
            "radio": {"icon": "📻", "label": "Rádió", "channels": {"1": ("Klub", "u"), "2": ("Retro", "u")},
                      "categories": [("Adók", ["1", "2"])], "current_key": "1"},
        }
        s.mode, s.active_web_app, s.volume, s.muted, s._preview_key = "tv", None, 70, False, None
        s.menu_visible = s.mode_menu_visible = s.settings_visible = s.help_visible = s.remote_panel_visible = False
        s.error_card, s.loading_card = mock.MagicMock(), mock.MagicMock()
        s.error_card.isVisible.return_value = s.loading_card.isVisible.return_value = False
        s.web_view = mock.MagicMock(); s.web_view.focusProxy.return_value = "PROXY"
        s.web_view.url.return_value.toString.return_value = ""
        s.calls = []
        s.settings_data = {}
        s._remote_snapshot_data = {}
    channels = property(lambda s: s.sources[s.mode]["channels"])
    current_key = property(lambda s: s.sources[s.mode]["current_key"])
    def _rec(s, name, *a): s.calls.append((name,) + a)
    def _switch_relative(s, d): s._rec("zap", d)
    def _change_volume(s, d): s._rec("vol", d)
    def _toggle_mute(s): s._rec("mute")
    def _on_mode_tile_clicked(s, m): s._rec("tile", m)
    def switch_mode(s, m): s._rec("switch_mode", m); s.mode = m; s.active_web_app = None
    def play_channel(s, k): s._rec("play", k); s.sources[s.mode]["current_key"] = k
    def _show_web_app(s, k): s._rec("show_web", k); s.active_web_app = k
    def _leave_web_app_and_resume(s): s._rec("leave_web")
    def _open_mode_menu_from_web_app(s): s._rec("source_web")
    def toggle_settings(s): s._rec("settings")
    def open_help(s): s._rec("help")
    def close_settings(s): s._rec("close_settings"); s.settings_visible = False
    def close_help(s): s._rec("close_help"); s.help_visible = False
    def close_remote_panel(s): s._rec("close_remote"); s.remote_panel_visible = False

def fresh(embedded=True):
    EVENTS.clear(); TIMERS.clear()
    ui = load(embedded); return ui, Win(ui)

def test_catalog_and_snapshot_are_json_serializable():
    ui, w = fresh()
    cat = w._build_remote_catalog()
    assert [m["key"] for m in cat["modes"]] == ["tv", "radio", "youtube"]
    assert cat["channels"]["tv"][0] == {"cat": "Közszolgálati", "items": [{"k": "1", "n": "M1"}, {"k": "2", "n": "M2"}]}
    w._preview_key = "2"; w._remote_refresh_snapshot(); s = w._remote_snapshot_data
    assert s["now"] == {"key": "1", "name": "M1"} and s["preview"] == {"key": "2", "name": "M2"}
    assert s["youtube"] == "embedded" and s["status"] == "playing" and s["active"] == "tv"
    json.dumps(cat); json.dumps(s)
    w.loading_card.isVisible.return_value = True; w._buffer_pct = 40; w._remote_refresh_snapshot()
    assert w._remote_snapshot_data["status"] == "buffering"
    w.error_card.isVisible.return_value = True; w._remote_refresh_snapshot()
    assert w._remote_snapshot_data["status"] == "error"
    w.active_web_app = "youtube"; w._remote_refresh_snapshot()
    assert w._remote_snapshot_data["active"] == "youtube" and w._remote_snapshot_data["status"] == "web"

def test_no_youtube_mode_in_catalog_when_disabled_and_search_ignored():
    ui, w = fresh(embedded=False)
    assert w._youtube_availability() == "external"
    w._on_remote_command({"cmd": "youtube", "text": "macska"})
    assert not [c for c in w.calls if c[0] == "show_web"]

def test_keys_go_to_main_window_normally():
    ui, w = fresh()
    w._on_remote_command({"cmd": "key", "name": "up"})
    assert EVENTS == [(w, 6, KEYS["Up"], ""), (w, 7, KEYS["Up"], "")]
    EVENTS.clear(); w._on_remote_command({"cmd": "digit", "value": "7"})
    assert EVENTS[0] == (w, 6, KEYS["7"], "7")
    EVENTS.clear(); w._on_remote_command({"cmd": "key", "name": "enter"})
    assert EVENTS[0][3] == "\r" and EVENTS[0][0] is w

def test_keys_go_to_youtube_when_active_unless_panel_open():
    ui, w = fresh(); w.active_web_app = "youtube"
    w._on_remote_command({"cmd": "key", "name": "down"})
    assert EVENTS[0][0] == "PROXY" and EVENTS[0][2] == KEYS["Down"]
    EVENTS.clear(); w._on_remote_command({"cmd": "key", "name": "back"})
    assert EVENTS[0][0] == "PROXY" and EVENTS[0][2] == KEYS["Backspace"]
    w.calls.clear(); EVENTS.clear()
    for name, expect in (("esc", "leave_web"), ("source", "source_web"), ("settings", "settings"), ("help", "help")):
        w._on_remote_command({"cmd": "key", "name": name}); assert w.calls[-1] == (expect,), name
    EVENTS.clear(); w.calls.clear(); w._on_remote_command({"cmd": "key", "name": "menu"})
    assert not EVENTS and not w.calls                       # webnézetben nincs csatornalista
    w.mode_menu_visible = True; w._on_remote_command({"cmd": "key", "name": "right"})
    assert EVENTS[0][0] is w                                # nyitott TV Box-panel: a főablaké a billentyű

def test_phone_can_never_quit_the_app():
    ui, w = fresh()
    w._on_remote_command({"cmd": "key", "name": "esc"})
    assert not EVENTS                                       # szabad állapot: semmi (nincs kilépés-megerősítés sem)
    w._preview_key = "2"; w._on_remote_command({"cmd": "key", "name": "esc"})
    assert EVENTS and EVENTS[0][2] == KEYS["Escape"]        # előnézet elvetése
    EVENTS.clear(); w._preview_key = None; w.menu_visible = True
    w._on_remote_command({"cmd": "key", "name": "esc"}); assert EVENTS and EVENTS[0][0] is w   # menü bezárása

def test_volume_and_mute():
    ui, w = fresh()
    w._on_remote_command({"cmd": "volume", "delta": -5}); w._on_remote_command({"cmd": "mute"})
    assert w.calls == [("vol", -5), ("mute",)]
    w.active_web_app = "youtube"; w.calls.clear()
    w._on_remote_command({"cmd": "volume", "delta": 5})
    js = w.web_view.page().runJavaScript.call_args[0][0]
    assert "video" in js and "0.05" in js and not w.calls
    w._on_remote_command({"cmd": "mute"}); assert "muted=!v.muted" in w.web_view.page().runJavaScript.call_args[0][0]

def test_zap_only_when_free():
    ui, w = fresh(); w._on_remote_command({"cmd": "zap", "dir": 1}); assert w.calls == [("zap", 1)]
    w.calls.clear(); w.menu_visible = True; w._on_remote_command({"cmd": "zap", "dir": 1}); assert not w.calls
    w.menu_visible = False; w.active_web_app = "youtube"; w._on_remote_command({"cmd": "zap", "dir": 1}); assert not w.calls

def test_mode_routing():
    ui, w = fresh()
    w._on_remote_command({"cmd": "mode", "mode": "radio"}); assert w.calls == [("tile", "radio")]
    w.calls.clear(); w._on_remote_command({"cmd": "mode", "mode": "youtube"}); assert w.calls == [("tile", "youtube")]
    w.calls.clear(); w.active_web_app = "youtube"; w._on_remote_command({"cmd": "mode", "mode": "youtube"}); assert not w.calls
    w.settings_visible = True; w._on_remote_command({"cmd": "mode", "mode": "tv"})
    assert w.calls[0] == ("close_settings",) and w.calls[-1] == ("tile", "tv")

def test_channel_selection():
    ui, w = fresh()
    w._on_remote_command({"cmd": "channel", "mode": "tv", "key": "3"}); assert w.calls == [("play", "3")]
    w.calls.clear(); w._on_remote_command({"cmd": "channel", "mode": "tv", "key": "3"}); assert not w.calls     # már ez megy
    w._on_remote_command({"cmd": "channel", "mode": "tv", "key": "99"}); assert not w.calls
    w._on_remote_command({"cmd": "channel", "mode": "youtube", "key": "1"}); assert not w.calls
    w._on_remote_command({"cmd": "channel", "mode": "radio", "key": "2"})
    assert w.calls == [("switch_mode", "radio"), ("play", "2")]
    w.calls.clear(); w.active_web_app = "youtube"; w._on_remote_command({"cmd": "channel", "mode": "radio", "key": "2"})
    assert w.calls == [("switch_mode", "radio"), ("play", "2")]                                               # YouTube-ból is vált

def test_youtube_search_and_link():
    ui, w = fresh()
    w._on_remote_command({"cmd": "youtube", "text": "macskás videók"})
    assert ("show_web", "youtube") in w.calls
    url = w.web_view.setUrl.call_args[0][0].u
    assert url.startswith("https://www.youtube.com/tv#/search?q=") and "macsk%C3%A1s" in url
    assert not TIMERS                                       # hideg betöltés: nem kell újratölteni
    w.web_view.url.return_value.toString.return_value = "https://www.youtube.com/tv"
    w.calls.clear(); w._on_remote_command({"cmd": "youtube", "text": "https://youtu.be/dQw4w9WgXcQ"})
    assert w.web_view.setUrl.call_args[0][0].u == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    w._on_remote_command({"cmd": "youtube", "text": "kutyák"})
    assert any(ms == 400 for ms, _ in TIMERS)               # már a /tv oldalon: újratöltés a '#' miatt
    TIMERS[-1][1](); w.web_view.reload.assert_called_once()

def test_first_command_closes_qr_panel_and_errors_dont_propagate():
    ui, w = fresh(); w.remote_panel_visible = True
    w._on_remote_command({"cmd": "mute"}); assert w.calls[0] == ("close_remote",)
    w._switch_relative = lambda d: 1 / 0
    w._on_remote_command({"cmd": "zap", "dir": 1})          # nem dobhat kivételt
    w._on_remote_command({"cmd": "ismeretlen"})

def test_hint_appears_when_no_phone_connects():
    import time
    ui, w = fresh()
    w.remote_status_label = mock.MagicMock(); w.remote_panel_visible = True
    w._remote_connected_shown = False; w._remote_hint_shown = False
    w._remote_server = mock.MagicMock(port=8765); w._remote_server.seen_since.return_value = False
    w._remote_opened_at = time.monotonic() - 5
    w._remote_tick(); assert not w.remote_status_label.setText.called          # még korai
    w._remote_opened_at = time.monotonic() - 30
    w._remote_tick(); text = w.remote_status_label.setText.call_args[0][0]
    assert "tűzfal" in text and "8765" in text and "8784" in text
    w.remote_status_label.setText.reset_mock(); w._remote_tick()
    assert not w.remote_status_label.setText.called                            # csak egyszer írja ki
    # ha közben csatlakozott egy telefon, a siker-üzenet jön, nem a súgó
    w._remote_hint_shown = False; w._remote_server.seen_since.return_value = True
    w._remote_tick(); assert "csatlakoztatva" in w.remote_status_label.setText.call_args[0][0]

def test_full_chain_http_to_handler():
    from tvbox import remote
    from tvbox.remote_page import PAGE
    ui, w = fresh(); w._remote_catalog_cache = w._build_remote_catalog(); w._remote_refresh_snapshot()
    srv = remote.RemoteServer("tokTOKEN12", w._on_remote_command, lambda: w._remote_snapshot_data,
                              lambda: w._remote_catalog_cache, PAGE, host="127.0.0.1", port=0)
    srv.start()
    def call(method, path, body=None):
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (srv.port, path), method=method,
                                     data=json.dumps(body).encode() if body else None, headers={"X-Token": "tokTOKEN12"})
        with urllib.request.urlopen(req, timeout=5) as r: return json.loads(r.read())
    try:
        assert call("POST", "/api/cmd", {"cmd": "channel", "mode": "radio", "key": "2"}) == {"ok": True}
        assert w.calls == [("switch_mode", "radio"), ("play", "2")]
        st = call("GET", "/api/state")
        assert st["mode"] == "radio" and st["now"]["name"] == "Retro"
        assert [m["key"] for m in call("GET", "/api/channels")["modes"]] == ["tv", "radio", "youtube"]
    finally: srv.stop()

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("OK", n)
