# -*- coding: utf-8 -*-
"""Billentyű- és görgő-események."""
from PyQt5.QtCore import Qt


class InputMixin:

    # ------------------------------------------------------------------
    # Egér: görgő = hangerő
    # ------------------------------------------------------------------
    def wheelEvent(self, event):
        # A klasszikus egérgörgő egy "kattanása" 120 egység; ehhez képest
        # arányosan számoljuk a hangerő-változást, hogy egy érintőpad/nagy
        # felbontású görgő sok apró eseménye ne tudja gyorsan túllőni a
        # hangerőt 0%-ra vagy 100%-ra. Eseményenként legfeljebb ±15%-ra
        # korlátozzuk a változást egy esetleges hirtelen, nagy "pöccintés" ellen.
        delta = event.angleDelta().y()
        if delta == 0:
            return
        change = int(round((delta / 120.0) * 5))
        if change == 0:
            change = 1 if delta > 0 else -1
        change = max(-15, min(15, change))
        self._change_volume(change)
        super().wheelEvent(event)

    # ------------------------------------------------------------------
    # Billentyűzet
    # ------------------------------------------------------------------
    def keyPressEvent(self, event):
        text = event.text()
        key_code = event.key()

        # -- Billentyű-súgó: ha nyitva van, BÁRMELYIK gomb becsukja --
        if self.help_visible:
            self.close_help()
            return

        if text.lower() == "h" or text == "?":
            self.open_help()
            return

        # -- Beállítások panel --
        if self.settings_visible:
            if key_code == Qt.Key_Up:
                self._move_settings_selection(-1)
            elif key_code == Qt.Key_Down:
                self._move_settings_selection(1)
            elif key_code == Qt.Key_Left:
                self._step_settings_value(-1)
            elif key_code in (Qt.Key_Right, Qt.Key_Return, Qt.Key_Enter):
                self._step_settings_value(1)
            elif key_code == Qt.Key_Escape or text.lower() == "s":
                self.close_settings()
            return

        # -- Forrásváltó menü (legmagasabb prioritás, ha nyitva van) --
        if self.mode_menu_visible:
            if key_code in (Qt.Key_Left, Qt.Key_Up):
                self._move_mode_selection(-1)
            elif key_code in (Qt.Key_Right, Qt.Key_Down):
                self._move_mode_selection(1)
            elif key_code in (Qt.Key_Return, Qt.Key_Enter):
                self._activate_mode_selection()
            elif key_code == Qt.Key_Escape or text.lower() == "b":
                self.close_mode_menu()
            return

        # -- Beépített webnézet (pl. YouTube) aktív --
        # NORMÁL esetben a _web_exit_shortcut / _web_menu_shortcut (lásd
        # __init__) kapja el az Esc-et és a B-t MÉG AZELŐTT, hogy ide
        # egyáltalán eljutnának, hiszen a QShortcut a fókusztól függetlenül
        # is működik. Ez a blokk itt a LÉNYEGI védőháló: e nélkül minden
        # MÁS billentyű (nyilak, számok, M, V, Space, Backspace) simán
        # átszivárgott ide, és csendben csatornát váltott / listát nyitott
        # a webnézet ALATT, miközben a felhasználó a YouTube-ot nézte -
        # pontosan ez okozta a korábban jelentett hibákat. Amíg a webnézet
        # aktív, itt semmi mást nem engedünk lefutni.
        if self.active_web_app:
            if key_code == Qt.Key_Escape:
                self._leave_web_app_and_resume()
            elif text.lower() == "b":
                self._open_mode_menu_from_web_app()
            elif text.lower() == "s":
                self.toggle_settings()
            return

        if text.lower() == "b":
            self.open_mode_menu()
            return

        if text.lower() == "m":
            self.toggle_menu()
            return

        if text.lower() == "s":
            self.toggle_settings()
            return

        if self.menu_visible:
            if key_code == Qt.Key_Up:
                self._move_menu_selection(-1)
            elif key_code == Qt.Key_Down:
                self._move_menu_selection(1)
            elif key_code in (Qt.Key_Return, Qt.Key_Enter):
                item = self.menu.currentItem()
                if item:
                    key = item.data(Qt.UserRole)
                    if key:
                        self.play_channel(key)
            elif key_code == Qt.Key_Escape:
                self.close_menu()
            else:
                self.reset_menu_timer()
            return

        # Menük zárva - normál üzemmód
        if self.error_card.isVisible() and key_code in (Qt.Key_Return, Qt.Key_Enter):
            self._retry_current_channel()
            return

        if text.isdigit():
            self._append_digit(text)
            return

        if key_code == Qt.Key_Left:
            self._switch_relative(-1)
        elif key_code == Qt.Key_Right:
            self._switch_relative(1)
        elif key_code == Qt.Key_Up:
            self._change_volume(5)
        elif key_code == Qt.Key_Down:
            self._change_volume(-5)
        elif key_code == Qt.Key_Space or text.lower() == "v":
            self._toggle_mute()
        elif key_code == Qt.Key_Backspace:
            self._play_previous()
        elif key_code == Qt.Key_Escape or text.lower() == "q":
            self._handle_exit_request()
