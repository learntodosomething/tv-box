# -*- coding: utf-8 -*-
"""Opcionális függőségek (QtWebEngine) és a közös logger."""
import logging


# A beépített, teljes képernyős YouTube-nézet a QtWebEngine (Chromium-alapú,
# Qt-be épített böngésző-motor) modult igényli - ez NEM települ a sima
# PyQt5-tel, külön csomag kell hozzá:
#   Windows / Linux (x86_64):  pip install PyQtWebEngine
#   Raspberry Pi / ARM Linux:  sudo apt install python3-pyqt5.qtwebengine
#     (ARM-re nincs kész pip-csomag, forrásból fordítani nagyon nehézkes -
#      ezért ott mindenképp az apt-os csomagot használd)
#
# HA NINCS TELEPÍTVE: a program ettől még elindul, csak a YouTube-csempe
# ilyenkor a KORÁBBI, külön Brave-ablakos módra esik vissza (lásd
# EXTERNAL_APPS lejjebb) - tehát semmi nem törik el, csak nem lesz "appon
# belüli" élmény, amíg fel nem teszed a fenti csomagot.
# A WebEngine komponenseket külön importáljuk. Fontos: egyes régebbi
# PyQtWebEngine kiadásokban a QWebEngineScript nem érhető el, miközben
# maga a QWebEngineView és az URL-interceptor tökéletesen működik.
# Egy opcionális komponens hiánya ezért NEM jelentheti azt, hogy az egész
# beépített böngésző "nincs telepítve".
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
    WEBENGINE_AVAILABLE = True
except ImportError:
    QWebEngineView = None
    QWebEngineProfile = None
    QWebEnginePage = None
    WEBENGINE_AVAILABLE = False


try:
    from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
except ImportError:
    QWebEngineUrlRequestInterceptor = None


try:
    from PyQt5.QtWebEngineCore import QWebEngineScript
except ImportError:
    QWebEngineScript = None


# A korábban néma `except Exception: pass` blokkok most ide naplóznak -
# fejlesztői hibakereséskor ez segít kideríteni, ha pl. a VLC-példány
# létrehozása vagy egy platform-specifikus videó-beágyazás meghiúsul,
# anélkül, hogy a felhasználó felé bármilyen technikai hibaüzenetet mutatnánk.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [tvbox] %(levelname)s: %(message)s")


logger = logging.getLogger("tvbox")


if not WEBENGINE_AVAILABLE:
    logger.warning(
        "A QtWebEngine nincs telepítve - a YouTube egyelőre külön Brave-"
        "ablakban fog megnyílni, nem az alkalmazáson belül. Telepítéshez "
        "lásd a fájl elején lévő megjegyzést (pip install PyQtWebEngine, "
        "vagy Raspberry Pi-n: sudo apt install python3-pyqt5.qtwebengine)."
    )
