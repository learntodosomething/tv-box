# -*- coding: utf-8 -*-
"""Kilépés-megerősítés, súgó, beállítások panel, fényerő, téma, animációk."""
import glob
import os
from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, QTimer
from tvbox.compat import logger
from tvbox.config import BACKLIGHT_GLOB, SETTINGS_SCHEMA
from tvbox.theme import _set_active_theme, _volume_bar_stylesheet
from tvbox import theme


class PanelMixin:

    # ------------------------------------------------------------------
    # Kilépés-megerősítés (Esc / Q)
    #
    # Egy fullscreen, távirányítóval/billentyűzettel kezelt "TV-doboznál"
    # veszélyes, ha egyetlen véletlen Esc/Q lenyomás azonnal, visszavonás
    # nélkül bezárja a TELJES alkalmazást. Az első lenyomás csak egy
    # megerősítő kártyát mutat; csak a MÁSODIK, néhány másodpercen belüli
    # lenyomás zárja be ténylegesen a programot.
    # ------------------------------------------------------------------
    def _handle_exit_request(self):
        if not self.settings_data.get("confirm_exit", True):
            # A felhasználó kikapcsolta a megerősítést a Beállításokban -
            # egyetlen Esc/Q azonnal kilép, megerősítő kártya nélkül.
            # Ne állítsuk le a VLC-t ugyanabban a billentyűeseményben,
            # amely a kilépést kezdeményezi. A closeEvent() végzi a stop()-ot.
            # Ez elkerüli a natív libVLC/Qt ablakkezelési versenyhelyzetet.
            QTimer.singleShot(100, self.close)
            return

        if self._exit_confirm_pending:
            self.exit_confirm_timer.stop()
            self._exit_confirm_pending = False
            self._hide_widget(self.exit_confirm_card)
            # A closeEvent() lesz az egyetlen hely, ahol a VLC leáll.
            QTimer.singleShot(100, self.close)
        else:
            self._exit_confirm_pending = True
            self._show_widget(self.exit_confirm_card)
            self.exit_confirm_timer.start(3000)

    def _cancel_exit_confirm(self):
        self._exit_confirm_pending = False
        self._hide_widget(self.exit_confirm_card)

    # ------------------------------------------------------------------
    # Billentyű-súgó (H vagy ?)
    # ------------------------------------------------------------------
    def toggle_help(self):
        if self.help_visible:
            self.close_help()
        else:
            self.open_help()

    def open_help(self):
        self._cancel_preview()
        if self.menu_visible:
            self.close_menu()
        if self.mode_menu_visible:
            self.close_mode_menu()
        # A panel navigációja a főablak keyPressEvent()-jén keresztül
        # működik - ha épp egy beépített webnézet (pl. YouTube) tartja a
        # billentyűzet-fókuszt, ide EXPLICIT vissza kell kérni, különben a
        # panel megnyitna, de semmilyen billentyű nem érne el hozzá.
        self.setFocus()
        self.help_visible = True
        self._show_widget(self.help_card)
        self.help_card.raise_()
        self.help_hide_timer.start(8000)

    def close_help(self):
        self.help_visible = False
        self.help_hide_timer.stop()
        self._hide_widget(self.help_card)
        self._return_focus()

    # ------------------------------------------------------------------
    # Beállítások panel (a forrásváltóból, "S" billentyűvel is nyitható)
    # ------------------------------------------------------------------
    def toggle_settings(self):
        if self.settings_visible:
            self.close_settings()
        else:
            self.open_settings()

    def open_settings(self):
        self._cancel_preview()
        if self.menu_visible:
            self.close_menu()
        if self.mode_menu_visible:
            self.close_mode_menu()
        self.setFocus()
        self.settings_visible = True
        self._settings_cursor = 0
        self._refresh_settings_rows()
        self._show_widget(self.settings_panel)
        self.settings_panel.raise_()

    def close_settings(self):
        self.settings_visible = False
        self._hide_widget(self.settings_panel)
        self._return_focus()

    def _refresh_settings_rows(self):
        for i, (spec, row_widget) in enumerate(zip(SETTINGS_SCHEMA, self.settings_rows)):
            value = self.settings_data[spec["key"]]
            idx = spec["options"].index(value) if value in spec["options"] else 0
            row_widget.set_value_text(spec["labels"][idx])
            row_widget.set_focused(i == self._settings_cursor)

    def _move_settings_selection(self, direction):
        n = len(self.settings_rows)
        if n == 0:
            return
        self._settings_cursor = max(0, min(n - 1, self._settings_cursor + direction))
        self._refresh_settings_rows()

    def _step_settings_value(self, direction):
        if not self.settings_rows:
            return
        spec = SETTINGS_SCHEMA[self._settings_cursor]
        options = spec["options"]
        current_value = self.settings_data[spec["key"]]
        idx = options.index(current_value) if current_value in options else 0
        new_idx = max(0, min(len(options) - 1, idx + direction))
        if new_idx == idx:
            return
        new_value = options[new_idx]
        self.settings_data[spec["key"]] = new_value
        self._apply_setting(spec["key"], new_value)
        self._refresh_settings_rows()
        self.save_timer.start(400)

    def _apply_setting(self, key, value):
        """Egy beállítás értékének azonnali (élő) alkalmazása - a legtöbb
        beállítás csak egy jövőbeli időzítést/viselkedést befolyásol
        (nincs azonnali látható hatása), de pl. a fényerő és a téma
        rögtön látszik."""
        if key == "brightness":
            self._apply_brightness(value)
        elif key == "theme":
            self.apply_theme(value)
        elif key == "youtube_adblock":
            if self.youtube_adblock_interceptor is not None:
                self.youtube_adblock_interceptor.set_enabled(value)
            if self.active_web_app == "youtube" and self.web_view is not None:
                self.web_view.reload()
        elif key == "info_card_ms":
            # Ha épp látszik az infókártya, az új beállítás szerint
            # azonnal újraindítjuk (vagy leállítjuk) az elrejtés-időzítőt,
            # hogy ne kelljen csatornát váltani a hatás eléréséhez.
            if self.info_card.isVisible():
                self.hide_timer.stop()
                if value:
                    self.hide_timer.start(value)
        # A többi (kilépés-megerősítés, menü-időzítés, animációk,
        # számbeírás-türelem) a self.settings_data-ból olvasódik ki
        # a megfelelő helyeken (lásd reset_menu_timer, _append_digit,
        # _handle_exit_request, _animations_enabled).

    def _apply_brightness(self, percent):
        """Kijelző-háttérvilágítás állítása sysfs-en keresztül (Raspberry
        Pi hivatalos érintő-kijelzőjénél tipikusan elérhető). Ha a
        rendszeren nincs vezérelhető háttérvilágítás (pl. sima HDMI-
        monitor), ez CSENDBEN, hiba nélkül nem csinál semmit - a
        beállítás a felületen továbbra is látszik és állítható marad,
        csak nincs látható hatása azon a kijelzőn."""
        try:
            candidates = glob.glob(BACKLIGHT_GLOB)
            if not candidates:
                return
            backlight_dir = candidates[0]
            max_path = os.path.join(backlight_dir, "max_brightness")
            brightness_path = os.path.join(backlight_dir, "brightness")
            with open(max_path) as f:
                max_value = int(f.read().strip())
            target = max(1, int(round(max_value * (percent / 100.0))))
            with open(brightness_path, "w") as f:
                f.write(str(target))
        except Exception as e:
            logger.info("Fényerő-szabályzás nem elérhető ezen a kijelzőn (%s).", e)

    def apply_theme(self, key):
        """Élő témaváltás: az új THEME azonnal érvényesül a jelenleg
        épített panelek háttér-/keretszínén és a felhasználói felület
        legfontosabb, akcentus-színű elemein. A csatornalisták
        gyorsítótárát eldobjuk, hogy legközelebbi megnyitáskor biztosan
        az ÚJ témával épüljenek fel újra (lásd _invalidate_menu_cache)."""
        _set_active_theme(key)
        # (a VOLUME_BAR_STYLE a theme modulban él)
        theme.VOLUME_BAR_STYLE = _volume_bar_stylesheet()
        self.volume_bar.setStyleSheet(theme.VOLUME_BAR_STYLE)
        self.preview_bar.setStyleSheet(theme.VOLUME_BAR_STYLE)

        self.info_card.set_colors(theme.THEME.SOLID_BG, theme.THEME.SOLID_BORDER)
        self.menu_panel.set_colors(theme.THEME.MENU_BG, theme.THEME.MENU_BORDER)
        self.mode_menu.set_colors(theme.THEME.MODE_PANEL_BG, theme.THEME.MODE_PANEL_BORDER)
        self.settings_panel.set_colors(theme.THEME.MENU_BG, theme.THEME.MENU_BORDER)
        self.radio_visualizer.set_colors(theme.THEME.SOLID_BG, theme.THEME.SOLID_BORDER)
        self.number_osd.set_colors(theme.THEME.SOLID_BG, theme.THEME.SOLID_BORDER)
        self.preview_osd.set_colors(theme.THEME.SOLID_BG, theme.THEME.SOLID_BORDER)
        self.volume_osd.set_colors(theme.THEME.SOLID_BG, theme.THEME.SOLID_BORDER)
        self.loading_card.set_colors(theme.THEME.SOLID_BG, theme.THEME.SOLID_BORDER)
        self.exit_confirm_card.set_colors(theme.THEME.SOLID_BG, theme.THEME.SOLID_BORDER)
        self.help_card.set_colors(theme.THEME.MENU_BG, theme.THEME.MENU_BORDER)
        # Az error_card szándékosan NEM téma-függő (mindkét téma ugyanazt
        # a piros "veszély" színt használja rá) - lásd THEME.ERROR_BG/BORDER.

        for tile in self.mode_tiles:
            tile.set_selected(tile._selected)
        self.settings_button.set_selected(self.settings_button._selected)

        # A már felépített csatornalisták (más forrásra váltva) a régi téma
        # színeivel maradnának - ahelyett, hogy mindet manuálisan
        # újrafestenénk, egyszerűen eldobjuk a gyorsítótárat: a következő
        # _refresh_menu_items() úgyis újraépíti majd (lásd _ensure_menu_built).
        self._invalidate_menu_cache()
        if self.menu_visible or self.current_key:
            self._refresh_menu_items()

        for widget in (self.info_card, self.menu_panel, self.mode_menu, self.settings_panel,
                       self.radio_visualizer, self.number_osd, self.preview_osd, self.volume_osd,
                       self.loading_card, self.exit_confirm_card, self.help_card):
            widget.update()

    # ------------------------------------------------------------------
    # Animált megjelenítés / elrejtés (a GlassPanel saját 'opacity'
    # property-jén keresztül - lásd a fájl elején lévő magyarázatot)
    # ------------------------------------------------------------------
    def _animations_enabled(self):
        return bool(self.settings_data.get("animations", True))

    def _kick_video_repaint(self):
        """'Megrugdossa' a VLC natív videó-felületét egy 1 pixeles, majd
        visszaállított geometria-változtatással, hogy kikényszerítsen egy
        VALÓDI újrarajzolást.

        HÁTTÉR: miután a beépített YouTube-nézet (QtWebEngine/Chromium,
        SAJÁT natív GPU-kompozitorral) legalább egyszer megjelent, a VLC
        natív videó-felülete (SAJÁT, MÁSIK natív GPU-kompozitorral)
        időnként nem frissül automatikusan, amikor egy Qt-overlay (info-
        kártya, menü, hangerő-kijelző) megjelenik/eltűnik fölötte - a kép
        "beragad" feketén/az utolsó kockán, amíg valami mást (pl. az
        ablak fókuszvesztése/visszakapása) nem kényszerít ki egy teljes,
        alacsonyabb szintű újrakompozitálást az ablakkezelőnél. Ez KÉT,
        EGYMÁSTÓL FÜGGETLEN natív renderelő motor (VLC és Chromium)
        ugyanabban a top-level ablakban való osztozásának egy mélyen
        gyökerező, driver-/ablakkezelő-függő tünete - nem Python-szintű
        hiba, amit "rendesen" ki lehetne javítani. Ez a geometria-
        trükk a legtöbb esetben újrarajzolásra kényszeríti a natív
        felületet, de NEM garantált 100%-os megoldás minden GPU-n/
        ablakkezelőn - ha ez a probléma továbbra is jelentkezik,
        érdemes megfontolni a YouTube-ot KÜLÖN Brave-ablakban futtatni
        (lásd EXTERNAL_APPS), mert az teljesen elkerüli ezt a
        konfliktust azzal, hogy a két natív renderelő sosem osztozik
        egy ablakon."""
        # JAVÍTVA: korábban minden hívás a JELENLEGI (esetleg már összezsugorított)
        # geometriából indult, és azt "állította vissza" - egy csatornaváltáskor
        # több hívás is történt, így a videófelület minden váltásnál 1-2 pixelt
        # veszített, és sosem nyerte vissza. Most egyetlen, összevont "rúgás"
        # fut, és mindig az ablak TÉNYLEGES méretére állít vissza.
        # Csak akkor van értelme, ha egy beágyazott Chromium is él az ablakban.
        if self.web_view is None or getattr(self, "_kick_pending", False):
            return
        if not self.isVisible() or self.isMinimized():
            return
        w, h = self.width(), self.height()
        if w < 2:
            return
        self._kick_pending = True
        self.video_frame.setGeometry(0, 0, w - 1, h)
        QTimer.singleShot(0, self._finish_video_kick)

    def _finish_video_kick(self):
        self._kick_pending = False
        self.video_frame.setGeometry(0, 0, self.width(), self.height())

    def _show_widget(self, panel):
        # Már teljesen látszik: nincs mit animálni (korábban minden hívás -
        # pl. zapping közben az infókártyánál - újraindította a fade-et).
        visible_now = panel.isVisible() and not getattr(panel, "_hiding", False)
        panel._hiding = False
        if visible_now and panel.opacity >= 0.99:
            panel.raise_()
            return
        was_visible = panel.isVisible()
        panel.show()
        panel.raise_()
        if not was_visible:
            self._kick_video_repaint()
        if not self._animations_enabled():
            self._stop_fade(panel)
            panel.opacity = 1.0
            panel.update()
            return
        start = panel.opacity if was_visible else 0.0
        self._animate_opacity(panel, start, 1.0, 190)

    def _hide_widget(self, panel):
        if not panel.isVisible() or getattr(panel, "_hiding", False):
            return
        panel._hiding = True
        self._kick_video_repaint()
        if not self._animations_enabled():
            self._stop_fade(panel)
            self._finish_hide(panel)
            return
        self._animate_opacity(panel, panel.opacity, 0.0, 190,
                              on_finished=lambda p=panel: self._finish_hide(p))

    def _finish_hide(self, panel):
        # Csak akkor rejtünk, ha közben nem kértük újra a megjelenítését.
        if getattr(panel, "_hiding", False):
            panel._hiding = False
            panel.opacity = 0.0
            panel.hide()

    def _stop_fade(self, panel):
        anim = getattr(panel, "_fade_anim", None)
        if anim is not None:
            anim.stop()

    def _animate_opacity(self, panel, start, end, duration, on_finished=None):
        # JAVÍTVA: panelenként EGY újrahasznált animáció. Korábban egy
        # félbehagyott "eltűnés" animáció a későbbi "megjelenés" UTÁN is
        # lefutott, és elrejtette a frissen megjelent panelt (pl. hangerő-OSD
        # vagy infókártya gyors egymásutáni hívásnál), a kiolvasott
        # DeleteWhenStopped objektumra való hivatkozás pedig RuntimeError-t
        # okozhatott.
        anim = getattr(panel, "_fade_anim", None)
        if anim is None:
            anim = QPropertyAnimation(panel, b"opacity", panel)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            panel._fade_anim = anim
        else:
            anim.stop()
            try:
                anim.finished.disconnect()
            except TypeError:
                pass
        anim.setDuration(duration)
        anim.setStartValue(start)
        anim.setEndValue(end)
        if on_finished:
            anim.finished.connect(on_finished)
        anim.start()
