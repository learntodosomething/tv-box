# -*- coding: utf-8 -*-
"""A főablak elemeinek felépítése (kártyák, menük, OSD-k)."""
from PyQt5.QtWidgets import (QAbstractItemView, QHBoxLayout, QListWidget, QListWidgetItem, QProgressBar, QVBoxLayout, QWidget)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import QPropertyAnimation, QSize, Qt
from tvbox.config import SETTINGS_SCHEMA
from tvbox.external_apps import (EXTERNAL_APPS, EXTERNAL_ORDER, WEB_APPS, WEB_APP_ORDER)
from tvbox.theme import (MENU_STYLE, _font, _label, set_translucent)
from tvbox.widgets import (CategoryHeaderWidget, ChannelItemWidget, EqualizerBars, GlassPanel, PillButton, SettingsRowWidget, SourceTile, SpinnerWidget, TintedLabel)
from tvbox import theme


class UIBuildMixin:

    # ------------------------------------------------------------------
    # UI felépítés
    # ------------------------------------------------------------------
    def _build_video_frame(self):
        self.video_frame = QWidget(self.central)
        self.video_frame.setStyleSheet("background-color: black;")

    def _build_info_card(self):
        panel = GlassPanel(self.central, radius=24, margin=16, glass=True)
        layout = panel.contentLayout()
        row = QHBoxLayout()
        row.setSpacing(16)
        layout.addLayout(row)

        self.channel_badge = TintedLabel(
            "1", bg_color=QColor(theme.THEME.ACCENT), text_color=QColor("#000000"),
            font=_font(19, QFont.Bold), fixed_size=(56, 56),
        )
        row.addWidget(self.channel_badge)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        text_col.setAlignment(Qt.AlignVCenter)
        self.channel_name_label = _label("", size=18, weight=QFont.DemiBold, color="#FFFFFF")
        text_col.addWidget(self.channel_name_label)
        row.addLayout(text_col, 1)

        time_col = QVBoxLayout()
        time_col.setSpacing(2)
        time_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # Az óra betűmérete és a kártya magassága szándékosan bőkezű térközzel
        # illeszkedik egymáshoz, hogy semmiképp ne vágódjon le semmilyen
        # betűtípus-metrika esetén (lásd a fájl elején lévő 2. pontot).
        self.time_label = _label("--:--", size=19, weight=QFont.Bold, color="#FFFFFF",
                                  align=Qt.AlignRight)
        self.date_label = _label("", size=10, weight=QFont.Medium, color=theme.THEME.TEXT_DIM,
                                  align=Qt.AlignRight)
        time_col.addWidget(self.time_label)
        time_col.addWidget(self.date_label)
        row.addLayout(time_col)

        panel.setFixedSize(480, 100)
        panel.hide()
        self.info_card = panel

    def _build_menu_panel(self):
        panel = GlassPanel(
            self.central, radius=28, margin=16,
            bg=theme.THEME.MENU_BG, border=theme.THEME.MENU_BORDER, glass=True,
        )
        layout = panel.contentLayout()
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        self.menu_icon_label = TintedLabel(
            "📺", bg_color=QColor(theme.THEME.ACCENT.red(), theme.THEME.ACCENT.green(), theme.THEME.ACCENT.blue(), 42),
            text_color=QColor("#FFFFFF"), font=_font(15), fixed_size=(34, 34),
        )
        header_row.addWidget(self.menu_icon_label)

        self.menu_title_label = _label("Csatornák", size=18, weight=QFont.Bold, color="#FFFFFF")
        header_row.addWidget(self.menu_title_label)
        header_row.addStretch()
        self.menu_count_label = _label("", size=12, weight=QFont.Medium, color=theme.THEME.TEXT_FAINT)
        header_row.addWidget(self.menu_count_label)
        layout.addLayout(header_row)

        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: rgba(255,255,255,26);")
        layout.addWidget(divider)

        # TELJESÍTMÉNY: itt már NEM egyetlen, minden csatornaváltáskor
        # újraépülő QListWidget van, hanem egy konténer, amibe forrásonként
        # (TV / Rádió / ...) EGYSZER, igény szerint ("lazy") épül fel egy-egy
        # saját QListWidget - lásd _ensure_menu_built(). Mindig csak az
        # aktuális forrásé látszik, a többi rejtve várakozik a gyorsítótárban.
        self.menu_list_container = QWidget()
        self._menu_list_layout = QVBoxLayout(self.menu_list_container)
        self._menu_list_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.menu_list_container, 1)

        hint = _label("↑ ↓ mozgás   •   Enter kiválasztás   •   M / Esc bezárás",
                       size=10, weight=QFont.Medium, color=theme.THEME.TEXT_FAINT)
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        panel.hide()
        self.menu_panel = panel

    def _create_menu_list_widget(self):
        """Egy forráshoz (TV / Rádió / ...) tartozó, önálló QListWidget
        legyártása - lásd _ensure_menu_built()."""
        listw = QListWidget()
        listw.setFrameShape(QListWidget.NoFrame)
        set_translucent(listw)
        set_translucent(listw.viewport())
        listw.viewport().setAutoFillBackground(False)
        listw.setStyleSheet(MENU_STYLE)
        listw.setFocusPolicy(Qt.NoFocus)
        # A beépített kijelölés-rajzolást teljesen kikapcsoljuk - a fókuszt
        # a ChannelItemWidget saját maga rajzolja meg (lásd ott a magyarázatot).
        listw.setSelectionMode(QAbstractItemView.NoSelection)
        listw.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        listw.itemClicked.connect(self._on_menu_item_clicked)
        listw.currentRowChanged.connect(self._on_menu_current_row_changed)
        return listw

    def _ensure_menu_built(self, mode):
        """Az adott forrás listáját CSAK EGYSZER építi fel (utána a
        self.menu_lists gyorsítótárban marad) - lásd a teljesítmény-
        megjegyzést a _build_menu_panel()-nél."""
        if mode in self.menu_lists:
            return
        state = self.sources[mode]
        listw = self._create_menu_list_widget()

        row = 0
        current_row = 0
        row_widgets = {}
        for category_name, keys in state["categories"]:
            header_item = QListWidgetItem()
            header_item.setFlags(Qt.ItemIsEnabled)
            header_item.setData(Qt.UserRole, None)
            header_item.setSizeHint(QSize(280, 46))
            listw.addItem(header_item)
            listw.setItemWidget(header_item, CategoryHeaderWidget(category_name))
            row += 1

            for key in keys:
                name = state["channels"][key][0]
                item = QListWidgetItem()
                item.setData(Qt.UserRole, key)
                item.setSizeHint(QSize(280, 56))
                listw.addItem(item)
                widget = ChannelItemWidget(key, name, is_current=(key == state["current_key"]))
                listw.setItemWidget(item, widget)
                row_widgets[key] = (row, widget)
                if key == state["current_key"]:
                    current_row = row
                row += 1

        self._menu_list_layout.addWidget(listw)
        listw.hide()

        self.menu_lists[mode] = listw
        self._menu_row_widgets[mode] = row_widgets
        self._menu_current_row[mode] = current_row
        self._menu_highlighted_key[mode] = state["current_key"]

        # A setCurrentRow() szinkron kiváltja a currentRowChanged jelzést,
        # ami a self.menu property-n keresztül ÉRI EL ezt a listát - ezért
        # a fenti gyorsítótár-bejegyzéseknek MÁR itt, ELŐTTE be kell
        # állniuk, különben a callback self.menu-je még None-t adna vissza.
        listw.setCurrentRow(current_row)

    def _invalidate_menu_cache(self):
        """A teljes csatornalista-gyorsítótár eldobása - csak ritka,
        globális eseményeknél kell (pl. témaváltás), hogy a már felépített
        sorok is biztosan az új színekkel épüljenek újra legközelebb."""
        for listw in self.menu_lists.values():
            self._menu_list_layout.removeWidget(listw)
            listw.deleteLater()
        self.menu_lists.clear()
        self._menu_row_widgets.clear()
        self._menu_highlighted_key.clear()
        self._menu_current_row.clear()

    def _show_menu_list_for_mode(self, mode):
        for m, listw in self.menu_lists.items():
            listw.setVisible(m == mode)

    def _update_current_highlight(self, mode):
        """Csatornaváltáskor CSAK a régi és az új aktív sort frissíti
        (nem építi újra a teljes listát) - ez a lényege annak, hogy nagy
        (50+ elemes) listáknál is gyors maradjon minden váltás."""
        state = self.sources[mode]
        current_key = state["current_key"]
        row_widgets = self._menu_row_widgets.get(mode, {})
        prev_key = self._menu_highlighted_key.get(mode)

        if prev_key is not None and prev_key != current_key and prev_key in row_widgets:
            _, prev_widget = row_widgets[prev_key]
            prev_widget.set_current(False)

        if current_key in row_widgets:
            row, widget = row_widgets[current_key]
            widget.set_current(True)
            listw = self.menu_lists.get(mode)
            if listw is not None:
                listw.setCurrentRow(row)
            self._menu_current_row[mode] = row

        self._menu_highlighted_key[mode] = current_key

    @property
    def menu(self):
        """Az AKTUÁLIS forrás (TV / Rádió / ...) csatorna-listája. A menü-
        navigáció (_move_menu_selection, keyPressEvent stb.) ezen keresztül
        mindig ugyanúgy egyetlen QListWidget-tel dolgozik, mint korábban -
        csak épp forrásonként külön, gyorsítótárazott példánnyal."""
        return self.menu_lists.get(self.mode)

    def _build_mode_menu(self):
        # Kifejezett kérésre TÖMÖR (nem áttetsző), világoskék hátterű kártya,
        # a forrásokkal EGYMÁS MELLETT, nagy csempékként (nem lista).
        panel = GlassPanel(
            self.central, radius=30, margin=20,
            bg=theme.THEME.MODE_PANEL_BG, border=theme.THEME.MODE_PANEL_BORDER, glass=False,
        )
        layout = panel.contentLayout()
        layout.setSpacing(14)

        title = _label("Forrás váltása", size=18, weight=QFont.Bold, color=theme.THEME.MODE_TILE_TEXT)
        layout.addWidget(title)

        tiles_row = QHBoxLayout()
        tiles_row.setSpacing(14)
        tiles_row.setAlignment(Qt.AlignCenter)
        layout.addLayout(tiles_row)

        # Csempék: előbb a "valódi" (VLC-vel lejátszott) források - TV,
        # Rádió -, majd UGYANABBAN A SORBAN a külső alkalmazások (pl.
        # YouTube a Brave-ben) - a felhasználó szempontjából ez egyetlen,
        # egységes választósor, a billentyűzetes navigáció (Balra/Jobbra)
        # is végigmegy mindegyiken, akármelyik típusúak.
        self.mode_tiles = []
        for mode_key in self.mode_order:
            state = self.sources[mode_key]
            count = len(state["channels"])
            description = "%d %s" % (count, state["unit"])
            tile = SourceTile(mode_key, state["icon"], state["label"], description, panel)
            tile.clicked.connect(self._on_mode_tile_clicked)
            tiles_row.addWidget(tile)
            self.mode_tiles.append(tile)

        for app_key in WEB_APP_ORDER:
            app = WEB_APPS[app_key]
            tile = SourceTile(app_key, app["icon"], app["label"], app["description"], panel)
            tile.clicked.connect(self._on_mode_tile_clicked)
            tiles_row.addWidget(tile)
            self.mode_tiles.append(tile)

        for app_key in EXTERNAL_ORDER:
            app = EXTERNAL_APPS[app_key]
            tile = SourceTile(app_key, app["icon"], app["label"], app["description"], panel)
            tile.clicked.connect(self._on_mode_tile_clicked)
            tiles_row.addWidget(tile)
            self.mode_tiles.append(tile)

        hint = _label("← → mozgás   •   Enter kiválasztás   •   B / Esc bezárás",
                       size=10, weight=QFont.Medium, color=theme.THEME.MODE_TILE_DESC)
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        # A "Beállítások" belefér ugyanebbe a menübe, de KÜLÖN elválasztva
        # (saját, elválasztó vonal alatti sor, más - pirula - alakkal), hogy
        # ne keveredjen a forrás-csempékkel, mégis pontosan ugyanazokkal a
        # billentyűkkel (nyilak + Enter) elérhető legyen, mint azok.
        settings_divider = QWidget()
        settings_divider.setFixedHeight(1)
        settings_divider.setStyleSheet("background-color: rgba(11,18,32,40);")
        layout.addWidget(settings_divider)

        self.settings_button = PillButton("⚙️", "Beállítások", panel)
        self.settings_button.clicked.connect(self._on_settings_button_clicked)
        layout.addWidget(self.settings_button)

        tile_w = 150
        n = max(1, len(self.mode_tiles))
        panel_w = 20 * 2 + n * tile_w + (n - 1) * 14 + 8
        panel_h = 410
        panel.setFixedSize(panel_w, panel_h)
        panel.hide()
        self.mode_menu = panel

    def _build_settings_panel(self):
        panel = GlassPanel(
            self.central, radius=28, margin=18,
            bg=theme.THEME.MENU_BG, border=theme.THEME.MENU_BORDER, glass=True,
        )
        layout = panel.contentLayout()
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        icon = TintedLabel(
            "⚙️", bg_color=QColor(theme.THEME.ACCENT.red(), theme.THEME.ACCENT.green(), theme.THEME.ACCENT.blue(), 42),
            text_color=QColor("#FFFFFF"), font=_font(15), fixed_size=(34, 34),
        )
        header_row.addWidget(icon)
        self.settings_title_label = _label("Beállítások", size=18, weight=QFont.Bold, color="#FFFFFF")
        header_row.addWidget(self.settings_title_label)
        header_row.addStretch()
        layout.addLayout(header_row)

        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: rgba(255,255,255,26);")
        layout.addWidget(divider)

        rows_layout = QVBoxLayout()
        rows_layout.setSpacing(2)
        layout.addLayout(rows_layout)

        self.settings_rows = []
        for spec in SETTINGS_SCHEMA:
            value = self.settings_data[spec["key"]]
            idx = spec["options"].index(value) if value in spec["options"] else 0
            row_widget = SettingsRowWidget(spec["label"], spec["labels"][idx])
            rows_layout.addWidget(row_widget)
            self.settings_rows.append(row_widget)

        hint = _label(
            "↑ ↓ sor   •   ← → érték   •   Esc / S bezárás",
            size=10, weight=QFont.Medium, color=theme.THEME.TEXT_FAINT,
        )
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        panel.setFixedSize(380, 108 + len(SETTINGS_SCHEMA) * 46)
        panel.hide()
        self.settings_panel = panel

    def _build_radio_visualizer(self):
        panel = GlassPanel(self.central, radius=30, margin=20, glass=True)
        layout = panel.contentLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(14)

        icon = _label("📻", size=42, align=Qt.AlignCenter)
        layout.addWidget(icon, alignment=Qt.AlignHCenter)

        self.radio_station_label = _label(
            "", size=20, weight=QFont.Bold, color="#FFFFFF",
            align=Qt.AlignCenter, wrap=True,
        )
        layout.addWidget(self.radio_station_label)

        self.radio_bars = EqualizerBars(panel)
        layout.addWidget(self.radio_bars, alignment=Qt.AlignHCenter)

        panel.setFixedSize(360, 260)
        panel.hide()
        self.radio_visualizer = panel

    def _build_number_osd(self):
        panel = GlassPanel(self.central, radius=20, margin=14)
        layout = panel.contentLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.number_text = _label("", size=32, weight=QFont.Bold, color="#FFFFFF",
                                   align=Qt.AlignCenter)
        layout.addWidget(self.number_text)
        self.number_hint = _label("csatorna megnyitása...", size=11, weight=QFont.Medium,
                                   color=theme.THEME.TEXT_DIM, align=Qt.AlignCenter)
        layout.addWidget(self.number_hint)
        panel.setFixedSize(180, 110)
        panel.hide()
        self.number_osd = panel

    def _build_preview_osd(self):
        """Jobb felső sarok: 'erre fogsz váltani' kártya + lefutó időcsík.
        A nyilak csak ezt állítják; a tényleges váltás a várakozás után (vagy
        Enterre) történik, közben a jelenlegi adás tovább megy."""
        panel = GlassPanel(self.central, radius=22, margin=16, glass=True)
        layout = panel.contentLayout()
        layout.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(14)
        self.preview_badge = TintedLabel(
            "1", bg_color=QColor(theme.THEME.ACCENT), text_color=QColor("#000000"),
            font=_font(19, QFont.Bold), fixed_size=(56, 56),
        )
        row.addWidget(self.preview_badge)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setAlignment(Qt.AlignVCenter)
        self.preview_caption = _label("Váltás erre  ·  Enter: most", size=10, weight=QFont.Medium,
                                      color=theme.THEME.TEXT_DIM)
        self.preview_name = _label("", size=16, weight=QFont.DemiBold, color="#FFFFFF")
        text_col.addWidget(self.preview_caption)
        text_col.addWidget(self.preview_name)
        row.addLayout(text_col, 1)
        layout.addLayout(row)

        self.preview_bar = QProgressBar()
        set_translucent(self.preview_bar)
        self.preview_bar.setRange(0, 100)
        self.preview_bar.setValue(100)
        self.preview_bar.setTextVisible(False)
        self.preview_bar.setFixedHeight(6)
        self.preview_bar.setStyleSheet(theme.VOLUME_BAR_STYLE)
        layout.addWidget(self.preview_bar)

        # Az időcsík csak kozmetika (a váltást a preview_timer végzi).
        self._preview_anim = QPropertyAnimation(self.preview_bar, b"value", self)

        panel.setFixedSize(360, 112)
        panel.hide()
        self.preview_osd = panel

    def _build_volume_osd(self):
        panel = GlassPanel(self.central, radius=20, margin=14, glass=True)
        layout = panel.contentLayout()
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        self.volume_caption = _label("Hangerő", size=13, weight=QFont.DemiBold, color="#FFFFFF")
        self.volume_value = _label("80%", size=13, weight=QFont.DemiBold, color=theme.THEME.TEXT_DIM,
                                    align=Qt.AlignRight)
        top_row.addWidget(self.volume_caption)
        top_row.addStretch()
        top_row.addWidget(self.volume_value)
        layout.addLayout(top_row)

        self.volume_bar = QProgressBar()
        set_translucent(self.volume_bar)
        self.volume_bar.setRange(0, 100)
        self.volume_bar.setTextVisible(False)
        self.volume_bar.setFixedHeight(8)
        self.volume_bar.setStyleSheet(theme.VOLUME_BAR_STYLE)
        layout.addWidget(self.volume_bar)

        panel.setFixedSize(300, 78)
        panel.hide()
        self.volume_osd = panel

    def _build_loading_card(self):
        panel = GlassPanel(self.central, radius=26, margin=18)
        layout = panel.contentLayout()
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignCenter)

        self.spinner = SpinnerWidget(panel, size=48, line_width=5)
        layout.addWidget(self.spinner, alignment=Qt.AlignHCenter)

        self.loading_caption = _label("Csatlakozás a csatornához...", size=14,
                                       weight=QFont.DemiBold, color="#FFFFFF",
                                       align=Qt.AlignCenter, wrap=True)
        layout.addWidget(self.loading_caption)

        panel.setFixedSize(260, 160)
        panel.hide()
        self.loading_card = panel

    def _build_error_card(self):
        panel = GlassPanel(
            self.central, radius=26, margin=18,
            bg=theme.THEME.ERROR_BG, border=theme.THEME.ERROR_BORDER,
        )
        layout = panel.contentLayout()
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        self.error_card_label = _label(
            "⚠  Nem sikerült elérni a csatornát", size=15, weight=QFont.Bold,
            color="#FFD8D8", align=Qt.AlignCenter, wrap=True,
        )
        layout.addWidget(self.error_card_label)

        hint = _label("Nyomj Enter-t az újrapróbálkozáshoz", size=11, weight=QFont.Medium,
                       color="#F2B9B9", align=Qt.AlignCenter, wrap=True)
        layout.addWidget(hint)

        panel.setFixedSize(360, 150)
        panel.hide()
        self.error_card = panel

    def _show_error_message(self, text):
        """Az error_card ÁLTALÁNOS célra is használható (nem csak
        adáshibánál) - pl. ha egy külső alkalmazás (YouTube/Brave)
        indítása sikertelen, mert nincs telepítve a böngésző."""
        self.error_card_label.setText("⚠  %s" % text)
        self._show_widget(self.error_card)

    def _build_exit_confirm_card(self):
        panel = GlassPanel(self.central, radius=24, margin=16, glass=True)
        layout = panel.contentLayout()
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        label = _label("Kilépés a TV Box-ból?", size=15, weight=QFont.Bold,
                        color="#FFFFFF", align=Qt.AlignCenter, wrap=True)
        layout.addWidget(label)

        hint = _label("Nyomd meg újra az Esc / Q gombot a megerősítéshez",
                       size=11, weight=QFont.Medium, color=theme.THEME.TEXT_DIM,
                       align=Qt.AlignCenter, wrap=True)
        layout.addWidget(hint)

        panel.setFixedSize(360, 110)
        panel.hide()
        self.exit_confirm_card = panel

    def _build_help_card(self):
        panel = GlassPanel(
            self.central, radius=28, margin=20,
            bg=theme.THEME.MENU_BG, border=theme.THEME.MENU_BORDER, glass=True,
        )
        layout = panel.contentLayout()
        layout.setSpacing(10)

        title = _label("Billentyűparancsok", size=18, weight=QFont.Bold, color="#FFFFFF")
        layout.addWidget(title)

        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: rgba(255,255,255,26);")
        layout.addWidget(divider)

        shortcuts = [
            ("← / →", "Csatorna-előnézet (idő után vált)"),
            ("↑ / ↓", "Hangerő fel / le"),
            ("0-9", "Csatornaszám beírása"),
            ("Enter", "Váltás azonnal / megerősítés"),
            ("Space / V", "Némítás"),
            ("Backspace", "Ugrás az előző csatornára"),
            ("M", "Csatornalista meg-/bezárása"),
            ("B", "Forrásváltás (TV / Rádió / YouTube)"),
            ("S", "Beállítások meg-/bezárása"),
            ("H / ?", "Ez a súgó"),
            ("Esc / Q", "Kilépés"),
        ]
        for key_label, desc in shortcuts:
            row = QHBoxLayout()
            row.setSpacing(14)
            # Egységes, FIX szélességű jelvény minden billentyűnek (a
            # leghosszabb címke, "Backspace" is kényelmesen elfér benne) -
            # így a sorok szépen egy oszlopba rendeződnek, és a jelvény
            # sosem szorulhat össze a sizeHint alá, ha a leírás hosszú.
            key_widget = TintedLabel(
                key_label, bg_color=QColor(255, 255, 255, 22), text_color=QColor("#FFFFFF"),
                font=_font(11, QFont.Bold), padding=(8, 4), fixed_size=(96, 30),
            )
            row.addWidget(key_widget, 0, Qt.AlignLeft)
            # A leírás TÖRDELHETŐ (wrap=True) - enélkül egy hosszabb leírás
            # (pl. "Kilépés (kétszeri megerősítéssel)") egyetlen sorként
            # akart volna elférni, ami szélességi kényszert adott a sorra,
            # és ez - stretch=0 lévén - a jelvényt nyomta össze a sizeHint-je
            # alá (emiatt vágódott le korábban a jelvény szövege).
            desc_label = _label(desc, size=12, weight=QFont.Medium, color=theme.THEME.TEXT_DIM, wrap=True)
            row.addWidget(desc_label, 1)
            layout.addLayout(row)

        hint = _label("Bármelyik gomb becsukja ezt az ablakot", size=10,
                       weight=QFont.Medium, color=theme.THEME.TEXT_FAINT, align=Qt.AlignCenter)
        layout.addWidget(hint)

        # Bőkezű magasság, hogy a 10 billentyű-sor semmiképp se lógjon bele
        # a lekerekített sarok-maszkba (lásd a GlassPanel elején lévő
        # magyarázatot arról, hogy a tartalom sosem nyúlhat a maszkon túlra).
        panel.setFixedSize(380, 600)
        panel.hide()
        self.help_card = panel
