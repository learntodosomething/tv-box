# -*- coding: utf-8 -*-
"""Fényerő = fekete, áttetsző fedőréteg a teljes képernyő előtt.

A Fényerő beállítás korábban a kijelző sysfs-háttérvilágítását írta, ami egy
sima HDMI-monitoron nem létezik, ezért nem csinált semmit. Most egy KÜLÖN,
keret nélküli, átlátszó, a bemenetet átengedő ablak fekete lapot rajzol a
teljes képernyőre: 100% = nincs sötétítés (az ablak el sem jelenik), lejjebb
egyre sötétebb a kép (a fedőréteg átlátszatlansága = 100% - fényerő).

Mivel külön ablak, a VLC natív videófelülete és a TV Box saját kártyái FÖLÖTT
is látszik. X11 alatt az ablakkezelőt kikerülő ablak, így a külön Brave-ablakos
YouTube (kiosk) fölött is; Windows-on a "mindig felül" jelző elég. Wayland alatt
a kliens nem tud más alkalmazások fölé kerülni - ott csak a TV Box saját képét
sötétíti (és ha a Qt xcb/XWayland módban fut, mint a PyQt5 alapértelmezése, a fenti
X11-es megoldás érvényes).

KOMPOZITOR NÉLKÜLI X11 (pl. régebbi Raspberry Pi OS, sima openbox): ott az
átlátszó ablak nem keverhető, fekete lapként jelenne meg - ezért ilyenkor a
fedőréteg HELYETT a VLC saját fényerő-szűrőjét használjuk (csak a videóképet
sötétíti, a kártyákat nem). A viselkedés felülbírálható: TVBOX_DIM=overlay|vlc.

A KÉSZENLÉTI mód (lásd power.py) ugyanezt az ablakot teljesen feketére állítja.
"""
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QApplication, QWidget
from tvbox.compat import logger

MIN_BRIGHTNESS = 10


class DimOverlay(QWidget):
    def __init__(self):
        flags = (Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                 | Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus
                 | Qt.NoDropShadowWindowHint)
        if (QApplication.platformName() or "") == "xcb":
            # X11: az ablakkezelők a TELJES KÉPERNYŐS ablakokat a "mindig felül" ablakok FÖLÉ
            # rakják - a fedőréteg így a TV Box mögé kerülne. Az ablakkezelőt kikerülő
            # (override-redirect) ablak minden fölött marad, és fókuszt sem kap/vesz el.
            flags |= Qt.X11BypassWindowManagerHint
        super().__init__(None, flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_QuitOnClose, False)         # ne tartsa életben az alkalmazást
        self.setFocusPolicy(Qt.NoFocus)
        self.setWindowTitle("TV Box fényerő")
        self._alpha = 0

    @property
    def alpha(self):
        return self._alpha

    def set_alpha(self, alpha):
        alpha = max(0, min(255, int(alpha)))
        if alpha != self._alpha:
            self._alpha = alpha
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, self._alpha))


def dim_alpha_for(percent):
    """Fényerő-% -> a fekete fedőréteg átlátszatlansága (0..255)."""
    percent = max(MIN_BRIGHTNESS, min(100, int(percent)))
    return int(round((100 - percent) * 255 / 100.0))


class DimMixin:

    def _init_dim(self):
        self._dim_overlay = None
        self._brightness = 100
        self._vlc_dim_active = False

    # -- támogatottság ---------------------------------------------------
    def _dim_supported(self):
        """Keverhető-e átlátszó, külön ablak ezen a rendszeren?"""
        forced = os.environ.get("TVBOX_DIM", "").strip().lower()
        if forced == "overlay":
            return True
        if forced == "vlc":
            return False
        platform = QApplication.platformName() or ""
        if platform in ("windows", "cocoa", "offscreen") or platform.startswith("wayland"):
            return True
        if platform == "xcb":
            try:
                from PyQt5.QtX11Extras import QX11Info
                return bool(QX11Info.isCompositingManagerRunning())
            except Exception:
                return False
        return False                 # eglfs / linuxfb: nincs több ablak

    # -- alkalmazás ------------------------------------------------------
    def _apply_brightness(self, percent):
        try:
            percent = int(percent)
        except (TypeError, ValueError):
            percent = 100
        self._brightness = max(MIN_BRIGHTNESS, min(100, percent))
        self._refresh_dim()

    def _current_dim_alpha(self):
        if getattr(self, "standby", False):
            return 255
        return dim_alpha_for(self._brightness)

    def _refresh_dim(self):
        alpha = self._current_dim_alpha()
        use_overlay = alpha >= 255 or self._dim_supported()
        try:
            if use_overlay:
                self._set_vlc_dim(100)
                self._set_overlay_alpha(alpha)
            else:
                self._set_overlay_alpha(0)
                self._set_vlc_dim(self._brightness)
        except Exception as e:                     # a fényerő sosem dönthet el semmit
            logger.warning("Fényerő-beállítás sikertelen: %s", e)

    def _set_overlay_alpha(self, alpha):
        if alpha <= 0:
            if self._dim_overlay is not None:
                self._dim_overlay.set_alpha(0)
                self._dim_overlay.hide()
            return
        if self._dim_overlay is None:
            self._dim_overlay = DimOverlay()
        ov = self._dim_overlay
        ov.set_alpha(alpha)
        self._place_dim_overlay()
        if not ov.isVisible():
            was_active = self.isActiveWindow()
            ov.show()
            if was_active and not self.isActiveWindow():
                self.activateWindow()              # a fedőréteg ne vigye el a billentyűzet-fókuszt
        ov.raise_()

    def _place_dim_overlay(self):
        ov = getattr(self, "_dim_overlay", None)
        if ov is None:
            return
        handle = self.windowHandle()
        screen = handle.screen() if handle is not None else None
        screen = screen or QApplication.primaryScreen()
        if screen is not None and ov.geometry() != screen.geometry():
            ov.setGeometry(screen.geometry())

    def _set_vlc_dim(self, percent):
        """Tartalék (kompozitor nélküli X11): a VLC fényerő-szűrője, 1.0 = normál."""
        if percent >= 100 and not self._vlc_dim_active:
            return
        try:
            import vlc
            player = self.player
            player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1 if percent < 100 else 0)
            player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, max(0.1, percent / 100.0))
            self._vlc_dim_active = percent < 100
        except Exception as e:
            logger.info("A VLC fényerő-szűrő nem érhető el: %s", e)

    def moveEvent(self, event):
        self._place_dim_overlay()
        super().moveEvent(event)

    def _close_dim_overlay(self):
        ov, self._dim_overlay = self._dim_overlay, None
        if ov is not None:
            try:
                ov.hide()
                ov.close()
                ov.deleteLater()
            except Exception:
                pass
