# -*- coding: utf-8 -*-
"""EPG - a Qt-s integráció (háttérszálas betöltés, időzítők, UI-frissítés).

A feldolgozó mag és a leírás (forrás megadása, gyorsítótár, névegyeztetés)
a tvbox/epg_core.py-ban van, Qt nélkül, hogy külön tesztelhető legyen.
"""
import threading
import time

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from tvbox.compat import logger
from tvbox.epg_core import (EPG_REFRESH_S, EPG_TICK_MS, fmt_clock, load_epg,
                            name_candidates, resolve_epg_source)


# ===========================================================================
# Qt-oldali integráció
# ===========================================================================
class EpgSignals(QObject):
    loaded = pyqtSignal(object, int)
    failed = pyqtSignal(str, int)


class EpgMixin:

    def _resolve_epg_source_early(self):
        """A UI felépítése ELŐTT hívandó (a kártyák magassága függ tőle)."""
        self.epg_source = resolve_epg_source(self.settings_data)

    def _init_epg(self):
        """A főablak konstruktorából hívandó, a UI felépítése UTÁN."""
        if not hasattr(self, "epg_source"):
            self._resolve_epg_source_early()
        self.epg_data = None
        self._epg_rev = 0
        self._epg_remote_map = {}
        self.epg_error = ""
        self._epg_loading = False
        self._epg_gen = 0
        self._epg_pending_force = None
        self._epg_signals = EpgSignals()
        self._epg_signals.loaded.connect(self._on_epg_loaded)
        self._epg_signals.failed.connect(self._on_epg_failed)

        wanted = set()
        for state in self.sources.values():
            for name, _url in state["channels"].values():
                wanted.update(name_candidates(name))
        self._epg_wanted = wanted

        self.epg_timer = QTimer(self)
        self.epg_timer.timeout.connect(self._epg_tick)
        self.epg_timer.start(EPG_TICK_MS)

        if self.epg_source and self.epg_enabled():
            # Kis késleltetés: az első csatorna elindulását/UI-t ne lassítsa.
            QTimer.singleShot(1500, lambda: self._epg_start_load(False))

    # -- állapot --------------------------------------------------------
    def epg_enabled(self):
        return bool(self.epg_source) and bool(self.settings_data.get("epg", True))

    def epg_now_next(self, name):
        if not self.epg_enabled() or self.epg_data is None:
            return None, None
        try:
            return self.epg_data.now_next(name)
        except Exception as e:      # védőháló: az EPG sosem döntheti el a lejátszást
            logger.warning("EPG lekérdezési hiba (%s): %s", name, e)
            return None, None

    # -- betöltés -------------------------------------------------------
    def _epg_start_load(self, force):
        if not self.epg_source:
            return
        if self._epg_loading:
            # Már fut egy betöltés - a végén (ha kell) újraindítjuk.
            self._epg_pending_force = bool(force) or bool(self._epg_pending_force)
            return
        self._epg_loading = True
        self._epg_gen += 1
        gen = self._epg_gen
        source, wanted, signals = self.epg_source, set(self._epg_wanted), self._epg_signals

        def worker():
            try:
                data = load_epg(source, wanted, force=force)
                signals.loaded.emit(data, gen)
            except Exception as e:
                try:
                    signals.failed.emit("%s: %s" % (type(e).__name__, e), gen)
                except RuntimeError:
                    pass        # az ablak közben bezárult
            except BaseException:
                pass

        threading.Thread(target=worker, name="tvbox-epg", daemon=True).start()

    def _epg_finish_cycle(self):
        self._epg_loading = False
        pending, self._epg_pending_force = self._epg_pending_force, None
        if pending is not None and self.epg_enabled():
            self._epg_start_load(pending)

    def _on_epg_loaded(self, data, gen):
        self.epg_data = data
        self.epg_error = ""
        logger.info("EPG betöltve: %d csatorna (%s)", data.channel_count, data.source)
        self._epg_finish_cycle()
        self._epg_refresh_ui()

    def _on_epg_failed(self, message, gen):
        self.epg_error = message
        logger.warning("EPG betöltés sikertelen: %s", message)
        self._epg_finish_cycle()
        self._epg_refresh_ui()

    def _on_epg_setting_changed(self):
        if self.epg_enabled() and self.epg_data is None and not self._epg_loading:
            self._epg_start_load(False)
        self._epg_refresh_ui()

    # -- időzített frissítés -------------------------------------------
    def _epg_tick(self):
        if not self.epg_enabled():
            return
        if (self.epg_data is not None and not self._epg_loading
                and time.time() - self.epg_data.loaded_at > EPG_REFRESH_S):
            self._epg_start_load(True)
        self._epg_refresh_ui(only_visible=True)

    # -- UI frissítése --------------------------------------------------
    def _epg_refresh_ui(self, only_visible=False):
        self._epg_rebuild_remote_map()
        if only_visible:
            if self.info_card.isVisible():
                self._update_epg_info()
            if self.menu_visible:
                self._refresh_menu_epg()
            return
        self._update_epg_info()
        self._refresh_menu_epg()

    # -- telefonos távirányító ---------------------------------------------
    def _epg_rebuild_remote_map(self):
        """{mód: {csatornakulcs: "ÓÓ:PP Cím"}} - a telefon csatornalistájához.
        Egyetlen értékadással cserélődik (szálbiztos olvasás a HTTP-szálból),
        a `rev` csak akkor nő, ha tényleg változott a tartalom."""
        new_map = {}
        if self.epg_enabled() and self.epg_data is not None:
            for mode_key, state in self.sources.items():
                items = {}
                for key, (name, _url) in state["channels"].items():
                    current, _nxt = self.epg_now_next(name)
                    if current is not None:
                        items[key] = "%s %s" % (fmt_clock(current.start), current.title)
                if items:
                    new_map[mode_key] = items
        if new_map != self._epg_remote_map:
            self._epg_remote_map = new_map
            self._epg_rev += 1

    def epg_remote_map(self):
        return {"rev": self._epg_rev, "now": self._epg_remote_map}

    def epg_state_snapshot(self):
        """A /api/state-be kerülő rész: az éppen nézett csatorna most/következő műsora."""
        out = {"rev": self._epg_rev, "now": None, "next": None}
        if not self.epg_enabled() or self.current_key not in self.channels:
            return out
        current, nxt = self.epg_now_next(self.channels[self.current_key][0])
        if current is not None:
            out["now"] = {"t": current.title, "s": fmt_clock(current.start), "e": fmt_clock(current.stop),
                          "p": round(max(0.0, min(1.0, (time.time() - current.start)
                                                  / max(1.0, current.stop - current.start))), 3)}
        if nxt is not None:
            out["next"] = {"t": nxt.title, "s": fmt_clock(nxt.start)}
        return out

    def _update_preview_epg(self, key):
        """Az előnézeti kártyán a léptetett csatorna most futó műsora."""
        label = getattr(self, "preview_epg", None)
        if label is None:
            return
        text = ""
        if key in self.channels:
            current, _nxt = self.epg_now_next(self.channels[key][0])
            if current is not None:
                text = "%s–%s  %s" % (fmt_clock(current.start), fmt_clock(current.stop), current.title)
        label.setFullText(text)
        label.setVisible(bool(text))

    def _epg_status_text(self):
        if not self.epg_source:
            return "Nincs EPG-forrás beállítva"
        if not self.settings_data.get("epg", True):
            return "A műsorinfó ki van kapcsolva"
        if self._epg_loading and self.epg_data is None:
            return "Műsorinfó betöltése…"
        if self.epg_error and self.epg_data is None:
            return "A műsorinfó nem érhető el"
        return "Nincs műsorinfó ehhez a csatornához"

    def _update_epg_info(self, explicit=False):
        """Az info kártya műsor-sorainak frissítése az aktuális csatornához.
        `explicit`: ha a felhasználó kérte ('I' billentyű), állapotüzenetet
        is mutatunk, ha nincs adat."""
        if not hasattr(self, "epg_now_label"):
            return
        name = self.channels[self.current_key][0] if self.current_key in self.channels else ""
        current, nxt = self.epg_now_next(name) if name else (None, None)

        if current is None and nxt is None:
            if explicit:
                self.epg_now_label.setFullText(self._epg_status_text())
                self.epg_now_label.show()
            else:
                self.epg_now_label.hide()
            self.epg_progress.hide()
            self.epg_next_label.hide()
            return

        if current is not None:
            self.epg_now_label.setFullText(
                "%s–%s  %s" % (fmt_clock(current.start), fmt_clock(current.stop), current.title))
            span = max(1.0, current.stop - current.start)
            self.epg_progress.set_fraction((time.time() - current.start) / span)
            self.epg_progress.show()
        else:
            self.epg_now_label.setFullText("Most: nincs műsorinfó")
            self.epg_progress.hide()
        self.epg_now_label.show()

        if nxt is not None:
            self.epg_next_label.setFullText("Következő  %s  %s" % (fmt_clock(nxt.start), nxt.title))
            self.epg_next_label.show()
        else:
            self.epg_next_label.hide()

    def _refresh_menu_epg(self):
        """A csatornalista soraiban a most futó műsor címének frissítése
        (csak az aktuális forrás listáján, és csak a ténylegesen változó
        sorokon fut le a tényleges átfestés)."""
        row_widgets = self._menu_row_widgets.get(self.mode)
        if not row_widgets:
            return
        channels = self.channels
        for key, (_row, widget) in row_widgets.items():
            text = ""
            if self.epg_enabled() and self.epg_data is not None:
                current, _nxt = self.epg_now_next(channels[key][0])
                if current is not None:
                    text = "%s  %s" % (fmt_clock(current.start), current.title)
            widget.set_subtitle(text)

    def show_epg_info(self):
        """'I' billentyű: az info kártya (csatornanév + most/következő műsor)
        újra megjelenítése."""
        if self.current_key is None:
            return
        self._update_epg_info(explicit=True)
        if not self.info_card.isVisible():
            self._show_widget(self.info_card)
        info_ms = self.settings_data.get("info_card_ms", 5000)
        self.hide_timer.stop()
        if info_ms:
            self.hide_timer.start(max(info_ms, 5000))

    def _stop_epg(self):
        try:
            self.epg_timer.stop()
        except Exception:
            pass
