# -*- coding: utf-8 -*-
"""Telefonos távirányító - a Qt (GUI-szál) oldala.

A HTTP-szerver (tvbox/remote.py) háttérszálon fut; ide csak egy Qt-signalon át
érkeznek a parancsok, így minden UI-művelet a GUI-szálon történik. Az állapotot
(snapshot) a GUI-szál frissíti félmásodpercenként, a szerver csak ezt olvassa.
"""
import secrets
import time
from PyQt5.QtCore import QEvent, QObject, Qt, QTimer, QUrl, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QKeyEvent, QPainter
from PyQt5.QtWidgets import QApplication, QWidget
from tvbox import theme
from tvbox.compat import logger
from tvbox.external_apps import EXTERNAL_APPS, EXTERNAL_ORDER, WEB_APP_ORDER, WEB_APPS
from tvbox.qrcode_min import make_qr
from tvbox.remote import PORT_TRIES, RemoteServer, lan_ip, youtube_target
from tvbox.remote_page import PAGE
from tvbox.theme import _label
from tvbox.widgets import GlassPanel, TintedLabel


class RemoteBridge(QObject):
    """Szálak közti híd: a szerver-szálról kibocsátott signal a GUI-szálon fut le."""
    command = pyqtSignal(dict)


class QrWidget(QWidget):
    """Fekete-fehér QR-kód kirajzolása egész pixeles modulokkal (élesebb, jobban olvasható)."""

    def __init__(self, size=260, parent=None):
        super().__init__(parent)
        self._matrix = None
        self.setFixedSize(size, size)

    def set_matrix(self, matrix):
        self._matrix = matrix
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#FFFFFF"))
        m = self._matrix
        if not m:
            return
        quiet = 4
        total = len(m) + 2 * quiet
        cell = max(1, self.width() // total)
        off = (self.width() - cell * total) // 2
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#000000"))
        for y, row in enumerate(m):
            for x, dark in enumerate(row):
                if dark:
                    p.drawRect(off + (x + quiet) * cell, off + (y + quiet) * cell, cell, cell)


REMOTE_HINT_AFTER_S = 20.0

_KEYMAP = {
    "up": (Qt.Key_Up, ""), "down": (Qt.Key_Down, ""),
    "left": (Qt.Key_Left, ""), "right": (Qt.Key_Right, ""),
    "enter": (Qt.Key_Return, "\r"), "esc": (Qt.Key_Escape, "\x1b"),
    "back": (Qt.Key_Backspace, "\x08"),
    "menu": (Qt.Key_M, "m"), "source": (Qt.Key_B, "b"),
    "settings": (Qt.Key_S, "s"), "help": (Qt.Key_H, "h"),
}
_JS_VOLUME = ("(function(d){var v=document.querySelector('video');if(!v)return;"
              "v.muted=false;v.volume=Math.max(0,Math.min(1,v.volume+d));})(%s);")
_JS_MUTE = "(function(){var v=document.querySelector('video');if(v)v.muted=!v.muted;})();"


class RemoteMixin:

    # ------------------------------------------------------------------
    # Felépítés
    # ------------------------------------------------------------------
    def _build_remote_panel(self):
        panel = GlassPanel(
            self.central, radius=28, margin=20,
            bg=theme.THEME.MENU_BG, border=theme.THEME.MENU_BORDER, glass=True,
        )
        layout = panel.contentLayout()
        layout.setSpacing(12)
        layout.addWidget(_label("📱  Telefonos távirányító", size=18, weight=QFont.Bold, color="#FFFFFF"))

        self.remote_qr = QrWidget(260)
        layout.addWidget(self.remote_qr, 0, Qt.AlignHCenter)

        self.remote_status_label = _label("", size=12, weight=QFont.DemiBold, color="#FFFFFF",
                                          align=Qt.AlignCenter, wrap=True)
        layout.addWidget(self.remote_status_label)
        self.remote_url_label = _label("", size=10, color=theme.THEME.TEXT_DIM,
                                       align=Qt.AlignCenter, wrap=True)
        layout.addWidget(self.remote_url_label)
        hint = _label("N: új kód   •   bármely más gomb: bezár", size=10,
                      weight=QFont.Medium, color=theme.THEME.TEXT_FAINT, align=Qt.AlignCenter)
        layout.addWidget(hint)

        panel.setFixedSize(400, 570)
        panel.hide()
        self.remote_panel = panel
        self.remote_panel_visible = False

    def _init_remote(self):
        self._remote_server = None
        self._remote_error = ""
        self._remote_snapshot_data = {}
        self._remote_catalog_cache = {"modes": [], "channels": {}}
        self._remote_opened_at = 0.0
        self._remote_connected_shown = False
        self._remote_hint_shown = False
        self._remote_bridge = RemoteBridge(self)
        self._remote_bridge.command.connect(self._on_remote_command)
        self.remote_timer = QTimer(self)
        self.remote_timer.timeout.connect(self._remote_tick)
        if self.settings_data.get("remote_enabled"):
            QTimer.singleShot(1000, self.start_remote)

    # ------------------------------------------------------------------
    # Szerver életciklus
    # ------------------------------------------------------------------
    def _remote_token(self):
        token = self.settings_data.get("_remote_token")
        if not (isinstance(token, str) and len(token) >= 10):
            token = secrets.token_urlsafe(9)
            self.settings_data["_remote_token"] = token
            self.save_timer.start(400)
        return token

    def start_remote(self):
        if self._remote_server is not None and self._remote_server.running:
            return True
        try:
            self._remote_catalog_cache = self._build_remote_catalog()
            self._remote_refresh_snapshot()
            server = RemoteServer(
                self._remote_token(),
                self._remote_bridge.command.emit,     # szálbiztos: a GUI-szálra sorolja
                lambda: self._remote_snapshot_data,
                lambda: self._remote_catalog_cache,
                PAGE,
            )
            server.start()
        except OSError as e:
            self._remote_error = str(e)
            logger.warning("A telefonos távirányító nem indítható: %s", e)
            return False
        self._remote_server = server
        self._remote_error = ""
        self.remote_timer.start(500)
        logger.info("Telefonos távirányító: %s", server.url())
        return True

    def stop_remote(self):
        self.remote_timer.stop()
        server, self._remote_server = self._remote_server, None
        if server is not None:
            server.stop()
        self._remote_snapshot_data = {}

    def _apply_remote_setting(self, enabled):
        """A Beállítások 'Telefonos távirányító' sorának hatása."""
        if enabled:
            if not self.start_remote():
                self.settings_data["remote_enabled"] = False      # a sor "Ki"-re áll vissza
            QTimer.singleShot(0, self._open_remote_from_settings)
        else:
            self.stop_remote()
            self.close_remote_panel()

    def _open_remote_from_settings(self):
        if self.settings_visible:
            self.close_settings()
        self.open_remote_panel()

    # ------------------------------------------------------------------
    # QR-panel
    # ------------------------------------------------------------------
    def open_remote_panel(self):
        self._cancel_preview()
        if self.menu_visible:
            self.close_menu()
        if self.mode_menu_visible:
            self.close_mode_menu()
        if self.settings_visible:
            self.close_settings()
        if self.help_visible:
            self.close_help()
        self.setFocus()
        self._fill_remote_panel()
        self._remote_opened_at = time.monotonic()
        self._remote_connected_shown = False
        self._remote_hint_shown = False
        self.remote_panel_visible = True
        self._show_widget(self.remote_panel)
        self.remote_panel.raise_()

    def _fill_remote_panel(self):
        server = self._remote_server
        if server is not None and server.running:
            ip = lan_ip()
            url = server.url(ip)
            try:
                self.remote_qr.set_matrix(make_qr(url, "M"))
            except ValueError:
                self.remote_qr.set_matrix(None)
            if ip.startswith("127."):
                self.remote_status_label.setText("⚠ Nem találok hálózati kapcsolatot – a telefon nem fogja elérni.")
            else:
                self.remote_status_label.setText("Olvasd be a telefonoddal (ugyanarról a Wi-Fi-ről)")
            self.remote_url_label.setText(url)
        else:
            self.remote_qr.set_matrix(None)
            if self._remote_error:
                self.remote_status_label.setText("Nem sikerült elindítani a távirányítót.")
                self.remote_url_label.setText(self._remote_error)
            else:
                self.remote_status_label.setText("A telefonos távirányító ki van kapcsolva.")
                self.remote_url_label.setText("Bekapcsolás: Beállítások → Telefonos távirányító")

    def close_remote_panel(self):
        if not self.remote_panel_visible:
            return
        self.remote_panel_visible = False
        self._hide_widget(self.remote_panel)
        self._return_focus()

    def _remote_new_token(self):
        """N: új titkos kód - a már beolvasott telefonok hozzáférése megszűnik."""
        self.settings_data["_remote_token"] = secrets.token_urlsafe(9)
        self.save_timer.start(400)
        if self._remote_server is not None:
            self._remote_server.token = self.settings_data["_remote_token"]
        self._fill_remote_panel()
        self._remote_opened_at = time.monotonic()
        self._remote_connected_shown = False

    def _remote_tick(self):
        try:
            self._remote_refresh_snapshot()
            server = self._remote_server
            if (self.remote_panel_visible and server is not None and not self._remote_connected_shown
                    and server.seen_since(self._remote_opened_at)):
                self._remote_connected_shown = True
                self.remote_status_label.setText("✓ Telefon csatlakoztatva")
                QTimer.singleShot(1300, self.close_remote_panel)
            elif (self.remote_panel_visible and server is not None and not self._remote_connected_shown
                    and not self._remote_hint_shown
                    and time.monotonic() - self._remote_opened_at > REMOTE_HINT_AFTER_S):
                # 20 mp óta nem jött telefon: a leggyakoribb okok kiírása
                self._remote_hint_shown = True
                self.remote_status_label.setText(
                    "Nem csatlakozik? Ugyanaz a Wi-Fi kell (vendég-Wi-Fin gyakran nem megy), "
                    "kapcsold ki a mobilnetet, és engedélyezd a tűzfalban a %d–%d portot "
                    "(tools/remote_firewall_windows.bat)." % (server.port, server.port + PORT_TRIES - 1))
        except Exception:  # noqa - egy időzítő soha ne dobjon kivételt
            logger.exception("Távirányító-állapot frissítése sikertelen")

    # ------------------------------------------------------------------
    # Állapot és katalógus a telefon számára
    # ------------------------------------------------------------------
    def _youtube_availability(self):
        if "youtube" in WEB_APP_ORDER:
            return "embedded"
        if "youtube" in EXTERNAL_ORDER:
            return "external"
        return "off"

    def _build_remote_catalog(self):
        modes, channels = [], {}
        for key, state in self.sources.items():
            modes.append({"key": key, "icon": state["icon"], "label": state["label"]})
            cats = []
            for cat_name, keys in state["categories"]:
                cats.append({"cat": cat_name,
                             "items": [{"k": k, "n": state["channels"][k][0]} for k in keys]})
            channels[key] = cats
        if self._youtube_availability() != "off":
            app = WEB_APPS.get("youtube") or EXTERNAL_APPS.get("youtube") or {}
            modes.append({"key": "youtube", "icon": app.get("icon", "▶️"),
                          "label": app.get("label", "YouTube")})
        return {"modes": modes, "channels": channels}

    def _remote_refresh_snapshot(self):
        key = self.current_key
        name = self.channels[key][0] if key in self.channels else None
        if self.error_card.isVisible():
            status = "error"
        elif self.loading_card.isVisible():
            status = "buffering" if getattr(self, "_buffer_pct", 100) < 100 else "loading"
        else:
            status = "playing"
        preview = None
        pk = getattr(self, "_preview_key", None)
        if pk in self.channels:
            preview = {"key": pk, "name": self.channels[pk][0]}
        self._remote_snapshot_data = {            # egyetlen értékadás = szálbiztos csere
            "mode": self.mode,
            "active": self.active_web_app or self.mode,
            "now": {"key": key, "name": name},
            "status": "web" if self.active_web_app else status,
            "volume": self.volume,
            "muted": bool(self.muted),
            "preview": preview,
            "youtube": self._youtube_availability(),
        }

    # ------------------------------------------------------------------
    # Parancsok (GUI-szál)
    # ------------------------------------------------------------------
    def _on_remote_command(self, cmd):
        try:
            self._handle_remote_command(cmd)
        except Exception:  # noqa
            logger.exception("Távirányító-parancs sikertelen: %r", cmd)
        try:
            self._remote_refresh_snapshot()
        except Exception:  # noqa
            pass

    def _modal_open(self):
        return (self.menu_visible or self.mode_menu_visible or self.settings_visible
                or self.help_visible or self.remote_panel_visible)

    def _handle_remote_command(self, cmd):
        kind = cmd.get("cmd")
        if self.remote_panel_visible:
            self.close_remote_panel()              # az első parancs bezárja a QR-panelt
        if kind == "key":
            self._remote_key(cmd["name"])
        elif kind == "digit":
            self._remote_press(getattr(Qt, "Key_" + cmd["value"]), cmd["value"])
        elif kind == "volume":
            self._remote_volume(cmd["delta"])
        elif kind == "mute":
            self._remote_mute()
        elif kind == "zap":
            if not self.active_web_app and not self._modal_open():
                self._switch_relative(cmd["dir"])
        elif kind == "mode":
            self._remote_mode(cmd["mode"])
        elif kind == "channel":
            self._remote_channel(cmd["mode"], cmd["key"])
        elif kind == "youtube":
            self._remote_youtube(cmd["text"])

    def _web_has_keys(self):
        """A billentyűk a YouTube-nak mennek, ha az aktív és nincs nyitva TV Box-panel."""
        return bool(self.active_web_app and self.web_view is not None
                    and not (self.mode_menu_visible or self.settings_visible or self.help_visible))

    def _remote_press(self, key, text):
        if self._web_has_keys():
            target = self.web_view.focusProxy() or QApplication.focusWidget() or self.web_view
        else:
            target = self                           # ugyanaz az út, mint a fizikai billentyűzetnél
        QApplication.sendEvent(target, QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier, text))
        QApplication.sendEvent(target, QKeyEvent(QEvent.KeyRelease, key, Qt.NoModifier, text))

    def _remote_key(self, name):
        if self._web_has_keys():
            if name == "esc":
                self._leave_web_app_and_resume()
                return
            if name == "source":
                self._open_mode_menu_from_web_app()
                return
            if name == "settings":
                self.toggle_settings()
                return
            if name == "help":
                self.open_help()
                return
            if name == "menu":
                return                              # webnézetben nincs csatornalista
        # A telefonról SOHA nem lehet kilépni a programból (a kanapéról nem indítható újra):
        # az Esc csak bezár - menüt, panelt, előnézetet. Szabad állapotban nem csinál semmit.
        if name == "esc" and not self._modal_open() and self._preview_key is None:
            return
        key, text = _KEYMAP[name]
        self._remote_press(key, text)

    def _remote_volume(self, delta):
        if self.active_web_app and self.web_view is not None:
            self.web_view.page().runJavaScript(_JS_VOLUME % (delta / 100.0))
        else:
            self._change_volume(delta)

    def _remote_mute(self):
        if self.active_web_app and self.web_view is not None:
            self.web_view.page().runJavaScript(_JS_MUTE)
        else:
            self._toggle_mute()

    def _close_panels_for_switch(self):
        if self.settings_visible:
            self.close_settings()
        if self.help_visible:
            self.close_help()

    def _remote_mode(self, mode):
        if mode == "youtube":
            if self.active_web_app == "youtube":
                return
            self._close_panels_for_switch()
            self._on_mode_tile_clicked("youtube")
        elif mode in self.sources:
            self._close_panels_for_switch()
            self._on_mode_tile_clicked(mode)

    def _remote_channel(self, mode, key):
        if mode not in self.sources or key not in self.sources[mode]["channels"]:
            return
        if (mode == self.mode and key == self.current_key and not self.active_web_app
                and not self.error_card.isVisible()):
            return                                  # már ez megy
        self._close_panels_for_switch()
        if mode != self.mode or self.active_web_app:
            self.switch_mode(mode)
        self.play_channel(key)

    def _remote_youtube(self, text):
        if "youtube" not in WEB_APP_ORDER:
            return                                  # külső (Brave) módban nincs keresés
        _kind, url = youtube_target(text)
        self._close_panels_for_switch()
        if self.active_web_app != "youtube":
            self._show_web_app("youtube")
        if self.web_view is None:
            return
        before = self.web_view.url().toString()
        self.web_view.setUrl(QUrl(url))
        # Ugyanazon az oldalon csak a '#' utáni rész változik: az SPA nem biztos, hogy
        # reagál rá, ezért újratöltjük - az új lap már a megadott útvonalon indul.
        if "#" in url and before.startswith("https://www.youtube.com/tv"):
            QTimer.singleShot(400, self._remote_reload_web)

    def _remote_reload_web(self):
        if self.web_view is not None and self.active_web_app == "youtube":
            self.web_view.reload()
