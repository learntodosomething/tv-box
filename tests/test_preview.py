"""A TV-szerű csatorna-előnézet logikája hamis PyQt5-tel (Qt nélkül futtatható)."""
import sys, os, importlib
from unittest import mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

class FakeTimer:
    def __init__(s, *a): s.active, s.ms, s.timeout = False, None, mock.MagicMock()
    def start(s, ms=None): s.active, s.ms = True, ms
    def stop(s): s.active = False
    def isActive(s): return s.active
    def setSingleShot(s, v): pass

def load():
    for n in [k for k in sys.modules if k.startswith("tvbox")]: del sys.modules[n]
    for name in ("PyQt5", "PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWebEngineWidgets", "PyQt5.QtWebEngineCore"):
        m = mock.MagicMock(); m.__path__ = []; sys.modules[name] = m
    sys.modules["PyQt5.QtCore"].QTimer = FakeTimer
    sys.modules["PyQt5.QtCore"].QObject = object
    menus = importlib.import_module("tvbox.menus"); player = importlib.import_module("tvbox.player")
    class F(menus.MenuMixin, player.PlayerMixin):
        def __init__(s, n=5):
            s.channel_keys = [str(i) for i in range(1, n + 1)]
            s.channels = {k: ("Csat" + k, "u" + k) for k in s.channel_keys}
            s.current_key, s.mode, s.settings_data = "1", "tv", {"digit_timeout_ms": 3000}
            s._preview_key = None
            s.preview_timer, s.digit_timer = FakeTimer(), FakeTimer()
            s.channel_buffer = ""
            for n_ in ("number_osd", "preview_osd", "preview_name", "preview_badge", "preview_bar",
                       "number_text", "number_hint", "error_card"): setattr(s, n_, mock.MagicMock())
            s.error_card.isVisible = lambda: False
            s._preview_anim = mock.MagicMock()
            s.played = []
        def play_channel(s, key):
            s._cancel_preview(); s.current_key = key; s.played.append(key)
        def _show_widget(s, w): pass
        def _hide_widget(s, w): pass
        def _animations_enabled(s): return True
    return F

def test_arrows_only_preview_then_switch_after_delay():
    F = load(); f = F()
    for _ in range(3): f._switch_relative(1)
    assert f._preview_key == "4" and f.current_key == "1" and f.played == []     # közben a régi csatorna megy
    assert f.preview_timer.active and f.preview_timer.ms == 3000
    f._confirm_preview()                                                         # a 3 mp lejárt
    assert f.played == ["4"] and f._preview_key is None and not f.preview_timer.active

def test_left_wraps_and_mixed_directions():
    F = load(); f = F()
    f._switch_relative(-1); assert f._preview_key == "5"
    f._switch_relative(1); f._switch_relative(1); assert f._preview_key == "2"

def test_back_to_current_does_not_restart_stream():
    F = load(); f = F()
    f._switch_relative(1); f._switch_relative(-1); assert f._preview_key == "1"
    f._confirm_preview(); assert f.played == []

def test_cancel_and_digits_cancel_preview():
    F = load(); f = F()
    f._switch_relative(1); f._cancel_preview()
    assert f._preview_key is None and not f.preview_timer.active
    f._confirm_preview(); assert f.played == []
    f._switch_relative(1); f._append_digit("3")
    assert f._preview_key is None and not f.preview_timer.active

def test_preview_and_digit_buffer_exclusive():
    F = load(); f = F()
    f._append_digit("0"); assert f.channel_buffer == "0" and f.digit_timer.active
    f._switch_relative(1)
    assert f.channel_buffer == "" and not f.digit_timer.active and f._preview_key == "2"

def test_error_card_allows_replay_of_same_channel():
    F = load(); f = F()
    f._switch_relative(1); f._switch_relative(-1)
    f.error_card.isVisible = lambda: True
    f._confirm_preview(); assert f.played == ["1"]

def test_delay_follows_setting():
    F = load(); f = F(); f.settings_data["digit_timeout_ms"] = 5000
    f._switch_relative(1); assert f.preview_timer.ms == 5000

if __name__ == "__main__":
    for n, fn in list(globals().items()):
        if n.startswith("test_"): fn(); print("OK", n)
