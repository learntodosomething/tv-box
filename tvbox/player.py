# -*- coding: utf-8 -*-
"""VLC lejátszás, hangerő, csatornaszám-beírás."""
import sys
import time
from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFontMetrics
from tvbox.buffering import (SHOW_BUFFER_CARD_AFTER_S, StreamSupervisor, url_id)
from tvbox import theme
from tvbox.compat import logger
from tvbox.vlcworker import VlcWorker


# ===========================================================================
# libVLC eseményeket biztonságosan a Qt GUI-szálra továbbító jelzések
# ===========================================================================
class PlayerSignals(QObject):
    playing = pyqtSignal()
    error = pyqtSignal()
    buffering = pyqtSignal(float)
    ended = pyqtSignal()
    switched = pyqtSignal(int)   # munkaszál: a régi bemenet lezárult (gen)
    failed = pyqtSignal(int)     # munkaszál: a lejátszás indítása kivételt dobott (gen)


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

    def _init_playback_helpers(self):
        """Egyszer, a konstruktorból hívandó: felügyelő + időzítők."""
        self.supervisor = StreamSupervisor(load_learned_cache(self.settings_data))
        self._started_at = time.monotonic()
        self._pending_media = None          # (key, url, is_radio, cache_ms)

        # Csatornaváltás-késleltetés (debounce): nyomva tartott nyílnál nem
        # indítunk 30 lejátszást/mp-ben, csak a legutolsó számít.
        self.play_debounce_timer = QTimer(self)
        self.play_debounce_timer.setSingleShot(True)
        self.play_debounce_timer.timeout.connect(self._start_pending_media)

        # Stall-őr: másodpercenként megnézi, nem akadt-e el a puffer.
        self.stall_timer = QTimer(self)
        self.stall_timer.timeout.connect(self._check_stall)

        # Automatikus újracsatlakozás (backoff után)
        self.retry_timer = QTimer(self)
        self.retry_timer.setSingleShot(True)
        self.retry_timer.timeout.connect(self._do_retry)
        self._retry_cache = None

        # A pufferelés-kártya csak tartós (>0.8 mp) pufferelésnél jelenik meg,
        # és a százalék-felirat is csak 4 frissítést/mp-ig változik.
        self.buffer_card_timer = QTimer(self)
        self.buffer_card_timer.setSingleShot(True)
        self.buffer_card_timer.timeout.connect(self._show_buffer_card)
        self._buffer_pct = 100

        # Csatorna-előnézet (nyíllal léptetett, még NEM aktív csatorna)
        self._preview_key = None
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._confirm_preview)

        # A libVLC blokkoló hívásai (set_media/play/stop/hangerő) NEM a GUI-szálon
        # futnak - lásd tvbox/vlcworker.py. A generáció-számláló + kapu azt
        # biztosítja, hogy a RÉGI adás késői eseményei (Error/EndReached a
        # lezárás közben) ne indítsanak téves újracsatlakozást az újon.
        self._play_gen = 0
        self._events_open = False
        self.player_signals.switched.connect(self._on_worker_switched)
        self.player_signals.failed.connect(self._on_worker_failed)
        self.worker = VlcWorker(
            self.instance, self.player,
            on_switched=lambda g: self.player_signals.switched.emit(g),
            on_failed=lambda g, e: (logger.warning("Lejátszás-indítási hiba: %r", e),
                                    self.player_signals.failed.emit(g)),
            log=logger.warning,
        )
        self.worker.start()

    def _on_worker_switched(self, gen):
        if gen == self._play_gen:
            self._events_open = True
            self._started_at = time.monotonic()

    def _on_worker_failed(self, gen):
        if gen == self._play_gen:
            self._events_open = True
            self._handle_stream_error()

    def play_channel(self, key):
        if key not in self.channels:
            return
        if getattr(self, "standby", False):
            return                      # készenlétben semmi nem indíthat lejátszást
        self._cancel_preview()

        # Ha épp egy beépített webnézet (pl. YouTube) volt aktív, most
        # eltüntetjük, mielőtt a videó/rádió újra megjelenne.
        self._leave_web_app_if_active()

        if key != self.current_key:
            self.previous_key = self.current_key
        self.current_key = key
        name, url = self.channels[key]
        is_radio = (self.mode == "radio")

        self.retry_timer.stop()
        self._hide_widget(self.error_card)
        self.loading_caption.setText("Csatlakozás a csatornához...")
        self._show_widget(self.loading_card)

        self.supervisor.reset(url, is_radio)
        self._queue_media(key, url, is_radio, self.supervisor.cache_ms())

        self.channel_badge.setText(key)
        self.channel_name_label.setText(name)
        self._update_epg_info()
        self.update_time()

        if is_radio:
            self.radio_station_label.setText(name)
            self._show_widget(self.radio_visualizer)
        else:
            self._hide_widget(self.radio_visualizer)

        self._show_widget(self.info_card)
        info_ms = self.settings_data.get("info_card_ms", 4500)
        self.hide_timer.stop()
        if info_ms:  # None = "Mindig látszik" -> nincs automatikus elrejtés
            self.hide_timer.start(info_ms)

        # A (drága) listaépítés csak akkor kell, ha a menü látszik vagy már
        # felépült; különben az open_menu() úgyis frissít.
        if self.menu_visible or self.mode in self.menu_lists:
            self._refresh_menu_items()
        self.close_menu()
        self.save_timer.start(400)

    # -- tényleges VLC-indítás (késleltetve, egyesítve) -----------------
    def _queue_media(self, key, url, is_radio, cache_ms, delay_ms=150):
        self._pending_media = (key, url, is_radio, cache_ms)
        self.play_debounce_timer.start(delay_ms)

    def _start_pending_media(self):
        if self._pending_media is None:
            return
        key, url, is_radio, cache_ms = self._pending_media
        self._pending_media = None
        self._started_at = time.monotonic()
        self._buffer_pct = 100
        self.buffer_card_timer.stop()
        self._play_gen += 1
        self._events_open = False
        opts = [":network-caching=%d" % cache_ms,
                ":live-caching=%d" % cache_ms,
                ":http-reconnect"]
        self.worker.request_play(self._play_gen, url, opts)
        self.stall_timer.start(1000)

    def _halt_playback(self):
        """Lejátszás teljes leállítása + minden hozzá tartozó időzítő."""
        self._cancel_preview()
        for t in (self.play_debounce_timer, self.stall_timer, self.retry_timer,
                  self.buffer_card_timer, self.watchdog_timer):
            t.stop()
        self._pending_media = None
        self._play_gen += 1
        self._events_open = False
        self.worker.request_stop(self._play_gen)

    def _play_previous(self):
        if self.previous_key:
            self.play_channel(self.previous_key)

    def _retry_current_channel(self):
        if self.current_key:
            self.play_channel(self.current_key)

    # -- VLC események (a GUI-szálon, signalon át érkeznek) -----------------
    def _on_stream_playing(self):
        if not self._events_open:
            return
        self.supervisor.on_playing(time.monotonic())
        self.buffer_card_timer.stop()
        self._hide_widget(self.loading_card)

    def _on_stream_error(self):
        if self._events_open:
            self._handle_stream_error()

    def _handle_stream_error(self):
        self.buffer_card_timer.stop()
        self._schedule_auto_retry("error")

    def _on_stream_ended(self):
        # Élő adás vége = szinte mindig megszakadt kapcsolat, nem valódi vég.
        if self._events_open:
            self._schedule_auto_retry("ended")

    def _on_stream_buffering(self, percent):
        if not self._events_open:
            return
        try:
            pct = float(percent)
        except (TypeError, ValueError):
            pct = 100.0
        now = time.monotonic()
        self.supervisor.on_buffering(pct, now)

        if pct >= 100:
            self._buffer_pct = 100
            self.buffer_card_timer.stop()
            self._hide_widget(self.loading_card)
            return

        # A százalék csak eltárolódik; a kártyát az időzítő mutatja meg, ha a
        # pufferelés ténylegesen elhúzódik (a libVLC szegmenshatároknál is
        # küld rövid, ártalmatlan Buffering eseményeket).
        self._buffer_pct = pct
        if self.loading_card.isVisible():
            self.loading_caption.setText("Pufferelés... %d%%" % int(pct))
        elif not self.buffer_card_timer.isActive():
            self.buffer_card_timer.start(int(SHOW_BUFFER_CARD_AFTER_S * 1000))

    def _show_buffer_card(self):
        if self._buffer_pct < 100:
            self.loading_caption.setText("Pufferelés... %d%%" % int(self._buffer_pct))
            self._show_widget(self.loading_card)

    # -- stall-felismerés és automatikus újracsatlakozás -----------------
    def _check_stall(self):
        if self.active_web_app or self.player is None:
            return
        verdict = self.supervisor.check(time.monotonic(), self._started_at)
        if verdict == "stalled":
            logger.warning("Elakadt adás (%s) - újracsatlakozás.", self.current_key)
            self._schedule_auto_retry("stalled")

    def _schedule_auto_retry(self, reason):
        self.stall_timer.stop()
        action, delay_s, cache_ms = self.supervisor.next_action(reason)
        if action == "giveup":
            self.watchdog_timer.stop()
            self._hide_widget(self.loading_card)
            self.error_card_label.setText("⚠  Nem sikerült elérni a csatornát")
            self._show_widget(self.error_card)
            self._persist_learned_cache()
            return
        self.loading_caption.setText("Újracsatlakozás...")
        self._show_widget(self.loading_card)
        self._retry_cache = cache_ms
        self.retry_timer.start(int(delay_s * 1000))
        self._persist_learned_cache()

    def _do_retry(self):
        if not self.current_key or self.active_web_app:
            return
        name, url = self.channels[self.current_key]
        self._queue_media(self.current_key, url, self.mode == "radio",
                          self._retry_cache or self.supervisor.cache_ms(), delay_ms=0)

    def _persist_learned_cache(self):
        self.settings_data["_stream_cache"] = dict(self.supervisor.learned)
        self.save_timer.start(400)

    def _on_watchdog_timeout(self):
        """Régi API-kompatibilitás: a stall-őr (_check_stall) vette át a
        szerepét, ez már csak biztonsági háló."""
        self._check_stall()

    # ------------------------------------------------------------------
    # Hangerő
    # ------------------------------------------------------------------
    def _change_volume(self, delta):
        self.muted = False
        self.volume = max(0, min(100, self.volume + delta))
        self.worker.request_audio(self.volume, self.muted)
        self._show_volume_osd()
        self.save_timer.start(400)

    def _toggle_mute(self):
        self.muted = not self.muted
        self.worker.request_audio(self.volume, self.muted)
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
    # Csatorna-előnézet: a nyíl csak kijelöl, a váltás késleltetve történik
    # ------------------------------------------------------------------
    def _preview_delay_ms(self):
        value = self.settings_data.get("digit_timeout_ms", 3000)
        return int(value) if value else 3000

    def _show_channel_preview(self, key):
        if key not in self.channels:
            return
        # A számbeírás és az előnézet nem futhat egyszerre ugyanazon a billentyűkön.
        self.digit_timer.stop()
        self.channel_buffer = ""
        self._hide_widget(self.number_osd)

        self._preview_key = key
        name = self.channels[key][0]
        self._update_preview_epg(key)
        fm = QFontMetrics(self.preview_name.font())
        self.preview_name.setText(fm.elidedText(name, Qt.ElideRight, 250))
        self.preview_badge.setText(key)
        self.preview_badge.setColors(theme.THEME.ACCENT, "#000000")

        delay = self._preview_delay_ms()
        self.preview_timer.start(delay)
        self._start_preview_bar(delay)
        self._show_widget(self.preview_osd)

    def _start_preview_bar(self, delay):
        anim = self._preview_anim
        anim.stop()
        if not self._animations_enabled():
            self.preview_bar.setValue(100)
            return
        anim.setDuration(delay)
        anim.setStartValue(100)
        anim.setEndValue(0)
        anim.start()

    def _clear_preview(self):
        self.preview_timer.stop()
        self._preview_anim.stop()
        key, self._preview_key = self._preview_key, None
        if key is not None:
            self._hide_widget(self.preview_osd)
        return key

    def _cancel_preview(self):
        self._clear_preview()

    def _confirm_preview(self):
        key = self._clear_preview()
        if key is None or key not in self.channels:
            return
        # Ha visszaléptünk a már játszó csatornára, nincs miért újraindítani.
        if key == self.current_key and not self.error_card.isVisible():
            return
        self.play_channel(key)

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
        self._cancel_preview()      # a számbeírás átveszi az előnézet helyét
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


def load_learned_cache(settings_data):
    raw = settings_data.get("_stream_cache") or {}
    out = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(k, str) and isinstance(v, int) and 0 <= v <= 3:
                out[k] = v
    return out
