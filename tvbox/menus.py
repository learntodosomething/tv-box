# -*- coding: utf-8 -*-
"""Csatornamenü és forrásváltó menü kezelése."""
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtCore import (QEasingCurve, QPropertyAnimation, QRect, QTimer, Qt)
from tvbox.external_apps import EXTERNAL_APPS, WEB_APP_ORDER
from tvbox.widgets import ChannelItemWidget


class MenuMixin:

    # ------------------------------------------------------------------
    # Csatornamenü
    # ------------------------------------------------------------------
    def _on_menu_item_clicked(self, item):
        key = item.data(Qt.UserRole)
        if key:
            self.play_channel(key)

    def _on_menu_current_row_changed(self, row):
        """A billentyűzet-fókuszt MINDIG a ténylegesen ott lévő sor-widgeten
        állítjuk be közvetlenül - sosem egy külön, esetleg elcsúszó
        kijelölő-téglalapon keresztül (lásd a 4. pontot a fájl elején)."""
        # O(1): csak a régi és az új sort frissítjük (korábban minden sort).
        listw = self.menu
        if listw is None:
            return
        prev = getattr(self, "_focused_row_widget", None)
        if prev is not None:
            try:
                prev.set_focused(False)
            except RuntimeError:  # a widget közben megsemmisült (témaváltás)
                pass
        self._focused_row_widget = None
        item = listw.item(row) if row >= 0 else None
        widget = listw.itemWidget(item) if item is not None else None
        if isinstance(widget, ChannelItemWidget):
            widget.set_focused(True)
            self._focused_row_widget = widget

    def _refresh_menu_items(self):
        self._ensure_menu_built(self.mode)
        state = self.sources[self.mode]
        self.menu_icon_label.setText(state["icon"])
        self.menu_title_label.setText(state["menu_title"])
        self.menu_count_label.setText("%d %s" % (len(self.channels), state["unit"]))
        self._show_menu_list_for_mode(self.mode)
        self._update_current_highlight(self.mode)

    def _center_menu_on_current(self):
        """A jelenlegi csatornára görgetést KÜLÖN, a panel láthatóvá
        válása UTÁN, egy körrel később hívjuk meg (lásd open_menu()).
        JAVÍTVA: korábban a scrollToItem() még a panel show() előtt,
        egy még el nem rendezett (0 méretű viewport-tal rendelkező)
        listán futott le - emiatt Qt nem tudta helyesen kiszámolni a
        középre-görgetést, és a lista ott maradt, ahol a felhasználó
        legutóbb, a bezáráskor elgörgette, FÜGGETLENÜL attól, hogy
        közben melyik csatornára váltott. Mivel most a lista MÁR látszik
        (és a Qt eseményhurok egy kört futott, lásd QTimer.singleShot(0,...)),
        a viewport mérete és a scrollbar-tartomány már érvényes, így a
        középre-igazítás minden megnyitáskor a TÉNYLEGESEN aktuális
        csatornát célozza meg, nem a régi görgetési pozíciót."""
        listw = self.menu
        if listw is None:
            return
        row = self._menu_current_row.get(self.mode, 0)
        item = listw.item(row)
        if item:
            listw.scrollToItem(item, QAbstractItemView.PositionAtCenter)

    def _stop_menu_slide(self):
        anim = getattr(self, "_menu_slide_anim", None)
        self._menu_slide_anim = None
        if anim is not None:
            try:
                anim.stop()
            except RuntimeError:  # DeleteWhenStopped már törölte
                pass

    def _finish_close_menu(self):
        # JAVÍTVA: gyors M-M (vagy csatornaváltás + M) esetén a régi "bezárás"
        # animáció vége elrejtette a közben újranyitott menüt, így a menü
        # "nyitott" állapotú maradt láthatatlanul, és elnyelte a billentyűket.
        self._menu_slide_anim = None
        if not self.menu_visible:
            self.menu_panel.hide()

    def open_menu(self):
        self._cancel_preview()
        self._stop_menu_slide()
        if self.mode_menu_visible:
            self.close_mode_menu()
        if self.settings_visible:
            self.close_settings()

        self.menu_visible = True
        self._refresh_menu_items()

        w, h = self.width(), self.height()
        panel_w = self.PANEL_WIDTH
        start_rect = QRect(w, 0, panel_w, h)
        end_rect = QRect(w - panel_w, 0, panel_w, h)

        if not self._animations_enabled():
            self.menu_panel.setGeometry(end_rect)
            self.menu_panel.show()
            self.menu_panel.raise_()
        else:
            self.menu_panel.setGeometry(start_rect)
            self.menu_panel.show()
            self.menu_panel.raise_()

            anim = QPropertyAnimation(self.menu_panel, b"geometry", self)
            anim.setDuration(280)
            anim.setStartValue(start_rect)
            anim.setEndValue(end_rect)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start(QPropertyAnimation.DeleteWhenStopped)
            self._menu_slide_anim = anim

        # Lásd a _center_menu_on_current() docstringjét: szándékosan EGY
        # körrel később fut le, miután a panel már látható.
        QTimer.singleShot(0, self._center_menu_on_current)

        self.reset_menu_timer()

    def close_menu(self):
        self._stop_menu_slide()
        if not self.menu_visible:
            self.menu_panel.hide()
            return

        self.menu_visible = False
        self.menu_hide_timer.stop()

        w, h = self.width(), self.height()
        panel_w = self.PANEL_WIDTH
        start_rect = self.menu_panel.geometry()
        end_rect = QRect(w, 0, panel_w, h)

        if not self._animations_enabled():
            self.menu_panel.hide()
        else:
            anim = QPropertyAnimation(self.menu_panel, b"geometry", self)
            anim.setDuration(230)
            anim.setStartValue(start_rect)
            anim.setEndValue(end_rect)
            anim.setEasingCurve(QEasingCurve.InCubic)
            anim.finished.connect(self._finish_close_menu)
            anim.start(QPropertyAnimation.DeleteWhenStopped)
            self._menu_slide_anim = anim

        self.setFocus()

    def toggle_menu(self):
        if self.menu_visible:
            self.close_menu()
        else:
            self.open_menu()

    def reset_menu_timer(self):
        if not self.menu_visible:
            return
        duration = self.settings_data.get("menu_autoclose_ms")
        self.menu_hide_timer.stop()
        if duration:  # None = "Soha" -> nincs automatikus bezárás
            self.menu_hide_timer.start(duration)

    def _move_menu_selection(self, direction):
        if self.menu is None:
            return
        row = self.menu.currentRow()
        n = self.menu.count()
        for _ in range(n):
            row += direction
            if row < 0 or row >= n:
                break
            item = self.menu.item(row)
            # FONTOS: Qt.ItemIsSelectable-t vizsgálunk, NEM Qt.ItemIsEnabled-t.
            # A kategória-fejléc sorok is "enabled"-ek (setFlags(Qt.ItemIsEnabled)),
            # csak nem "selectable"-ek - a helytelen flag-ellenőrzés miatt a
            # billentyűzetes navigáció korábban minden fejlécen megállt, ahelyett
            # hogy továbbugrott volna a következő valódi csatornára.
            if item.flags() & Qt.ItemIsSelectable:
                self.menu.setCurrentRow(row)
                self.menu.scrollToItem(item)
                break
        self.reset_menu_timer()

    def _switch_relative(self, direction):
        if not self.channel_keys:
            return
        # TV-szerű működés: a nyíl csak az ELŐNÉZETET lépteti (több lenyomás
        # egymás után továbblép), a tényleges váltás a várakozás után vagy
        # Enterre történik. Közben a jelenlegi adás tovább megy.
        base = self._preview_key if self._preview_key in self.channel_keys else self.current_key
        if base in self.channel_keys:
            new_idx = (self.channel_keys.index(base) + direction) % len(self.channel_keys)
        else:
            new_idx = 0
        self._show_channel_preview(self.channel_keys[new_idx])

    # ------------------------------------------------------------------
    # Forrásváltó menü ("B" billentyű: TV / Rádió / YouTube / Beállítások)
    # ------------------------------------------------------------------
    def _on_mode_tile_clicked(self, mode_key):
        self.close_mode_menu()
        if mode_key in WEB_APP_ORDER:
            # A QtWebEngine indítását leválasztjuk a kattintási eseményről is.
            QTimer.singleShot(150, lambda k=mode_key: self._show_web_app(k))
        elif mode_key in EXTERNAL_APPS:
            self._launch_external_app(mode_key)
        else:
            self.switch_mode(mode_key)

    def _on_settings_button_clicked(self):
        self.close_mode_menu()
        self.open_settings()

    def _update_mode_tile_selection(self):
        n = len(self.mode_tiles)
        for i, tile in enumerate(self.mode_tiles):
            tile.set_selected(i == self._mode_cursor)
        self.settings_button.set_selected(self._mode_cursor == n)

    def open_mode_menu(self):
        self._cancel_preview()
        if self.menu_visible:
            self.close_menu()
        if self.settings_visible:
            self.close_settings()

        self.mode_menu_visible = True
        self.setFocus()
        if self.active_web_app:
            # A kurzor arra a csempére álljon, amit épp nézünk.
            matches = [i for i, t in enumerate(self.mode_tiles) if t.mode_key == self.active_web_app]
            self._mode_cursor = matches[0] if matches else 0
        else:
            self._mode_cursor = self.mode_order.index(self.mode) if self.mode in self.mode_order else 0
        self._update_mode_tile_selection()
        self._show_widget(self.mode_menu)
        self.mode_menu.raise_()

    def close_mode_menu(self):
        self.mode_menu_visible = False
        self._hide_widget(self.mode_menu)
        self._return_focus()

    def _return_focus(self):
        """A panelek (forrásváltó/Beállítások/súgó) bezárása után a fókuszt
        oda adja vissza, ahova valójában kell: ha épp egy beépített
        webnézet (pl. YouTube) aktív, akkor annak (különben a nyilak/Enter
        onnantól nem a webnézetnek mennének), egyébként a főablaknak."""
        if self.active_web_app and self.web_view is not None:
            self.web_view.setFocus()
        else:
            self.setFocus()

    def toggle_mode_menu(self):
        if self.mode_menu_visible:
            self.close_mode_menu()
        else:
            self.open_mode_menu()

    def _move_mode_selection(self, direction):
        # +1: az utolsó "pozíció" a külön elválasztott, de a nyilakkal
        # ugyanúgy elérhető "Beállítások" gomb.
        n = len(self.mode_tiles) + 1
        if n == 0:
            return
        self._mode_cursor = max(0, min(n - 1, self._mode_cursor + direction))
        self._update_mode_tile_selection()

    def _activate_mode_selection(self):
        """A forrásváltóban Enter-re fut le: vagy egy forrásra/külső
        alkalmazásra vált, vagy - ha a kurzor a külön elválasztott utolsó
        pozíción áll - megnyitja a Beállításokat.

        FONTOS, FELHASZNÁLÓ ÁLTAL JELENTETT HIBA MIATTI VÁLTOZÁS: ha innen
        (billentyűzettel, Enterrel) KÖZVETLENÜL, ugyanabban a hívási
        láncban hívtuk meg a _show_web_app()-ot, az néha összeomlott -
        EGÉR-kattintásra viszont sosem. A legvalószínűbb magyarázat: a
        _show_web_app() a QWebEngineView-ra tesz fókuszt, MIKÖZBEN Qt még
        éppen ennek az Enter billentyű-eseménynek a kézbesítését végzi a
        (régi) fókusz-widgeten - ez a fókuszváltás + natív Chromium-
        kompozitor kombináció egy időzítés-érzékeny, natív szintű
        versenyhelyzetet okozott. A `QTimer.singleShot(0, ...)` addig
        várat, amíg Qt teljesen befejezi a JELENLEGI billentyű-esemény
        kézbesítését, és csak utána, egy ÚJ eseményhurok-körben építi fel
        / mutatja meg a webnézetet - ez strukturálisan kizárja ezt a
        verseny­helyzetet, függetlenül attól, hogy pontosan mi volt a
        natív hiba oka."""
        if self._mode_cursor == len(self.mode_tiles):
            self.close_mode_menu()
            self.open_settings()
        elif self.mode_tiles:
            tile = self.mode_tiles[self._mode_cursor]
            self.close_mode_menu()
            if tile.mode_key in WEB_APP_ORDER:
                # A natív VLC felület és a QtWebEngine ugyanazon top-level
                # ablakban időzítésérzékeny lehet. Enter eseményből ne
                # közvetlenül indítsuk a Chromium nézetet.
                self.setFocus()
                QTimer.singleShot(150, lambda k=tile.mode_key: self._show_web_app(k))
            elif tile.mode_key in EXTERNAL_APPS:
                self._launch_external_app(tile.mode_key)
            else:
                self.switch_mode(tile.mode_key)
