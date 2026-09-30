# -*- coding: utf-8 -*-
"""VLC lejátszás, hangerő, csatornaszám-beírás."""
import sys
from PyQt5.QtCore import QObject, pyqtSignal
from tvbox.compat import logger


# ===========================================================================
# libVLC eseményeket biztonságosan a Qt GUI-szálra továbbító jelzések
# ===========================================================================
class PlayerSignals(QObject):
    playing = pyqtSignal()
    error = pyqtSignal()
    buffering = pyqtSignal(float)


class PlayerMixin:

    # ------------------------------------------------------------------
    # VLC indítás / vezérlés
    # ------------------------------------------------------------------
    def init_vlc(self):
        """A videó-kimenet natív ablakba ágyazása. Az esemény-callbackek már
        a konstruktorban bekötésre kerültek (lásd ott a magyarázatot)."""
        try:
            if sys.platform.startswith("linux"):
                self.player.set_xwindow(int(self.video_frame.winId()))
            elif sys.platform == "win32":
                self.player.set_hwnd(int(self.video_frame.winId()))
            elif sys.platform == "darwin":
                self.player.set_nsobject(int(self.video_frame.winId()))
        except Exception as e:
            logger.warning("Nem sikerült beágyazni a videó-kimenetet: %s", e)

        start_key = self.current_key or (self.channel_keys[0] if self.channel_keys else None)
        if start_key:
            self.play_channel(start_key)

    def play_channel(self, key):
        if key not in self.channels:
            return

        # Ha épp egy beépített webnézet (pl. YouTube) volt aktív, most
        # eltüntetjük, mielőtt a videó/rádió újra megjelenne.
        self._leave_web_app_if_active()

        if key != self.current_key:
            self.previous_key = self.current_key
        self.current_key = key
        name, url = self.channels[key]

        self._hide_widget(self.error_card)
        self.loading_caption.setText("Csatlakozás a csatornához...")
        self._show_widget(self.loading_card)
        # "Watchdog": ha ennyi időn belül nem érkezik sem "lejátszás elindult",
        # sem "hiba" jelzés a lejátszótól (pl. mert az URL egyszerűen nem
        # válaszol - holt szerver, DNS-timeout, tűzfal), automatikusan
        # hibaállapotba kapcsolunk, hogy a töltés-jelző sose ragadjon be
        # a végtelenségig. Minden play_channel()-hívás újraindítja.
        self.watchdog_timer.start(12000)

        try:
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()
        except Exception as e:
            logger.warning("Nem sikerült elindítani a lejátszást (%s): %s", url, e)
            self._on_stream_error()
            return

        self.channel_badge.setText(key)
        self.channel_name_label.setText(name)
        self.update_time()

        if self.mode == "radio":
            self.radio_station_label.setText(name)
            self._show_widget(self.radio_visualizer)
        else:
            self._hide_widget(self.radio_visualizer)

        self._show_widget(self.info_card)
        info_ms = self.settings_data.get("info_card_ms", 4500)
        self.hide_timer.stop()
        if info_ms:  # None = "Mindig látszik" -> nincs automatikus elrejtés
            self.hide_timer.start(info_ms)

        self._refresh_menu_items()
        self.close_menu()
        self.save_timer.start(400)

    def _play_previous(self):
        if self.previous_key:
            self.play_channel(self.previous_key)

    def _retry_current_channel(self):
        if self.current_key:
            self.play_channel(self.current_key)

    def _on_stream_playing(self):
        self.watchdog_timer.stop()
        self._hide_widget(self.loading_card)

    def _on_stream_error(self):
        self.watchdog_timer.stop()
        self._hide_widget(self.loading_card)
        self.error_card_label.setText("⚠  Nem sikerült elérni a csatornát")
        self._show_widget(self.error_card)

    def _on_stream_buffering(self, percent):
        try:
            pct = int(percent)
        except (TypeError, ValueError):
            pct = 100

        # A libVLC élő adásoknál menet közben is küldhet Buffering eseményt,
        # de a "Playing" esemény ilyenkor nem tűzik újra - ezért ITT, a 100%-os
        # állapotnál kell elrejteni a kártyát, nem szabad megvárni a Playing-et.
        if pct >= 100:
            self.watchdog_timer.stop()
            self._hide_widget(self.loading_card)
            return

        self.loading_caption.setText("Pufferelés... %d%%" % pct)
        if not self.loading_card.isVisible():
            self._show_widget(self.loading_card)

    def _on_watchdog_timeout(self):
        """Ha ennyi idő alatt sem "lejátszás elindult", sem "hiba" jelzés nem
        érkezett a lejátszótól, feltételezzük, hogy az adás nem válaszol, és
        magunktól hibaállapotba váltunk - lásd a play_channel()-nél lévő
        magyarázatot."""
        if self.loading_card.isVisible():
            logger.warning("Watchdog időtúllépés - a csatorna (%s) nem válaszolt időben.", self.current_key)
            self._on_stream_error()

    # ------------------------------------------------------------------
    # Hangerő
    # ------------------------------------------------------------------
    def _change_volume(self, delta):
        self.muted = False
        self.player.audio_set_mute(False)
        self.volume = max(0, min(100, self.volume + delta))
        self.player.audio_set_volume(self.volume)
        self._show_volume_osd()
        self.save_timer.start(400)

    def _toggle_mute(self):
        self.muted = not self.muted
        self.player.audio_set_mute(self.muted)
        self._show_volume_osd()
        self.save_timer.start(400)

    def _show_volume_osd(self):
        if self.muted:
            self.volume_caption.setText("Némítva")
            self.volume_value.setText("--")
            self.volume_bar.setValue(0)
        else:
            self.volume_caption.setText("Hangerő")
            self.volume_value.setText("%d%%" % self.volume)
            self.volume_bar.setValue(self.volume)
        self._show_widget(self.volume_osd)
        self.volume_hide_timer.start(1500)

    # ------------------------------------------------------------------
    # Csatornaszám beírás (számbillentyűk)
    # ------------------------------------------------------------------
    def _lookup_channel_key(self, buffer):
        """A beírt szám alapján megkeresi a hozzá tartozó csatornakulcsot.
        A csatornakulcsok sosem tartalmaznak vezető nullát (pl. "1", nem
        "01") - ha a felhasználó megszokásból mégis beír egyet (pl. "01"),
        ezt is elfogadjuk, ha a nulláktól megfosztott alak létező csatorna."""
        if buffer in self.channels:
            return buffer
        stripped = buffer.lstrip("0")
        if stripped and stripped in self.channels:
            return stripped
        return None

    def _append_digit(self, digit):
        if len(self.channel_buffer) >= 3:
            self.channel_buffer = ""
        self.channel_buffer += digit
        buffer = self.channel_buffer
        self.number_text.setText(buffer)

        match_key = self._lookup_channel_key(buffer)
        self.number_hint.setText(
            self.channels[match_key][0] if match_key else "nincs ilyen csatorna"
        )
        self._show_widget(self.number_osd)

        # Ha a beírt szám EGYÉRTELMŰEN egy létező csatornára utal - vagyis
        # nincs olyan másik csatornaszám, ami ugyanezekkel a számjegyekkel
        # kezdődne -, nincs értelme végigvárni a 3 másodperces türelmi
        # időt: azonnal váltunk, ahogy egy "igazi" TV-nél is megszokott.
        has_longer_match = any(k != buffer and k.startswith(buffer) for k in self.channels)
        if match_key and not has_longer_match:
            self._confirm_digit_buffer()
            return

        self.digit_timer.start(self.settings_data.get("digit_timeout_ms", 3000))

    def _confirm_digit_buffer(self):
        self.digit_timer.stop()
        buffer = self.channel_buffer
        self.channel_buffer = ""
        self._hide_widget(self.number_osd)
        match_key = self._lookup_channel_key(buffer)
        if match_key:
            self.play_channel(match_key)
