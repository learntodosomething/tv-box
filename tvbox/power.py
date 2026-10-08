# -*- coding: utf-8 -*-
"""Készenléti mód ("kikapcsolás" / "bekapcsolás") - telefonról is vezérelhető.

A TV Box programja közben FUT (ez kell ahhoz, hogy a telefonról vissza lehessen
kapcsolni), de a "kikapcsolt" állapotban:
  * a lejátszás leáll (hang és hálózat is), a külső YouTube/Brave ablak bezárul,
  * a teljes képernyőt fekete lap takarja (lásd dimmer.py), a panelek bezárulnak,
  * X11 alatt a monitor is alvó állapotba kerül (xset dpms force off),
  * minden bemenet (telefon, billentyűzet) figyelmen kívül marad, KIVÉVE a
    bekapcsolást: a telefonon 2 mp-es nyomva tartás, a billentyűzeten bármely gomb.
A gép áramtalanítása/leállítása szándékosan NEM része ennek: azután a telefon
már nem érné el a TV Box-ot.
"""
import os
import shutil
import subprocess
import sys

from PyQt5.QtCore import QTimer
from tvbox.compat import logger

POWER_HOLD_MIN_MS = 1800        # a szerver ennél rövidebb "nyomva tartást" nem fogad el


class PowerMixin:

    def _init_power(self):
        self.standby = False

    # ------------------------------------------------------------------
    def enter_standby(self):
        if self.standby:
            return
        logger.info("Készenléti mód: be")
        self.standby = True                      # ELŐSZÖR: innentől a play_channel() is tiltott
        for name, closer in (("menu_visible", self.close_menu), ("mode_menu_visible", self.close_mode_menu),
                             ("settings_visible", self.close_settings), ("help_visible", self.close_help),
                             ("remote_panel_visible", self.close_remote_panel)):
            if getattr(self, name, False):
                closer()
        self._cancel_exit_confirm()
        self._cancel_preview()
        try:
            self._leave_web_app_if_active()
        except Exception:
            pass
        self._halt_playback()
        self._stop_external_apps()
        for card in (self.loading_card, self.error_card, self.number_osd, self.volume_osd,
                     self.info_card, self.radio_visualizer):
            if card.isVisible():
                card.hide()
        self.channel_buffer = ""
        self.digit_timer.stop()
        self._refresh_dim()                      # teljesen fekete
        self._screen_power(False)

    def leave_standby(self):
        if not self.standby:
            return
        logger.info("Készenléti mód: ki")
        self.standby = False
        self._screen_power(True)
        self._refresh_dim()                      # vissza a beállított fényerőre
        if self.isMinimized():
            self.showNormal()
        if not self.isFullScreen():
            self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        if self.current_key:
            QTimer.singleShot(150, lambda: self.current_key and not self.standby
                              and self.play_channel(self.current_key))

    def _stop_external_apps(self):
        """A külön ablakban futó alkalmazások (YouTube/Brave) bezárása."""
        for key, proc in list(self._external_processes.items()):
            try:
                if proc.poll() is None:
                    proc.terminate()
            except Exception as e:
                logger.warning("A(z) %s bezárása sikertelen: %s", key, e)

    def _screen_power(self, on):
        """Monitor ki/be (csak X11 + xset esetén; máshol a fekete lap marad)."""
        if not (sys.platform.startswith("linux") and os.environ.get("DISPLAY") and shutil.which("xset")):
            return
        try:
            subprocess.Popen(["xset", "dpms", "force", "on" if on else "off"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.info("A monitor ki/be kapcsolása nem sikerült: %s", e)

    def _remote_power(self, state):
        if state == "off":
            self.enter_standby()
        elif state == "on":
            self.leave_standby()
