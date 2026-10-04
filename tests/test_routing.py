"""A forrásváltó csempék útvonalának tesztje hamis PyQt5-tel (Qt nélkül futtatható).
Azt védi, hogy a YouTube csempe soha ne hozzon létre Chromium-ot, ha a beépített mód ki van kapcsolva."""
import sys, os, types, importlib
from unittest import mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def fake_qt():
    for name in ("PyQt5", "PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWebEngineWidgets", "PyQt5.QtWebEngineCore"):
        m = mock.MagicMock(); m.__path__ = []; sys.modules[name] = m
    sys.modules["PyQt5.QtCore"].Qt = mock.MagicMock()
    class T:  # QTimer
        @staticmethod
        def singleShot(ms, fn): fn()
    sys.modules["PyQt5.QtCore"].QTimer = T

def load(order=None):
    for n in [k for k in sys.modules if k.startswith("tvbox")]: del sys.modules[n]
    fake_qt()
    ext = importlib.import_module("tvbox.external_apps")
    if order is not None:
        ext.WEB_APP_ORDER[:] = order
        ext.EXTERNAL_ORDER[:] = [k for k in ext.EXTERNAL_APPS if k not in order]
    menus = importlib.import_module("tvbox.menus")
    return menus

class Fake:
    def __init__(s): s.calls = []
    def close_mode_menu(s): pass
    def setFocus(s): pass
    def _show_web_app(s, k): s.calls.append(("web", k))
    def _launch_external_app(s, k): s.calls.append(("ext", k))
    def switch_mode(s, k): s.calls.append(("mode", k))

def test_default_config_is_embedded_youtube():
    menus = load()                      # alapértelmezett konfiguráció, semmi felülírás
    ext = sys.modules["tvbox.external_apps"]
    assert ext.WEB_APP_ORDER == ["youtube"] and ext.EXTERNAL_ORDER == []
    f = Fake(); menus.MenuMixin._on_mode_tile_clicked(f, "youtube")
    assert f.calls == [("web", "youtube")], f.calls

def test_no_webengine_falls_back_to_brave():
    for n in [k for k in sys.modules if k.startswith("tvbox")]: del sys.modules[n]
    fake_qt()
    sys.modules["PyQt5.QtWebEngineWidgets"] = None        # import -> ImportError
    ext = importlib.import_module("tvbox.external_apps")
    assert ext.WEB_APP_ORDER == [] and ext.EXTERNAL_ORDER == ["youtube"]

def test_embedded_disabled_goes_to_brave():
    menus = load([])
    f = Fake(); menus.MenuMixin._on_mode_tile_clicked(f, "youtube")
    assert f.calls == [("ext", "youtube")], f.calls
    f = Fake(); menus.MenuMixin._on_mode_tile_clicked(f, "tv")
    assert f.calls == [("mode", "tv")]

def test_enter_on_tile_disabled():
    menus = load([])
    f = Fake(); tile = types.SimpleNamespace(mode_key="youtube")
    f.mode_tiles, f._mode_cursor = [tile], 0
    f.open_settings = lambda: f.calls.append(("settings",))
    menus.MenuMixin._activate_mode_selection(f)
    assert f.calls == [("ext", "youtube")], f.calls

def test_embedded_enabled_goes_to_web():
    menus = load(["youtube"])
    f = Fake(); menus.MenuMixin._on_mode_tile_clicked(f, "youtube")
    assert f.calls == [("web", "youtube")], f.calls

if __name__ == "__main__":
    for n, fn in list(globals().items()):
        if n.startswith("test_"): fn(); print("OK", n)
