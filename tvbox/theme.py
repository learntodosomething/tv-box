# -*- coding: utf-8 -*-
"""Témák, színek, stíluslapok és kis UI-segédfüggvények. FIGYELEM: a THEME/ACCENT futás közben cserélődik, ezért máshol `theme.THEME` formában kell használni."""
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from types import SimpleNamespace


# ===========================================================================
# TÉMA-REGISZTER
#
# A vizuális stílus (színek) mostantól nem néhány szórt konstans, hanem egy
# névvel ellátott, cserélhető "téma" objektum (SimpleNamespace). Minden
# widget a modul-szintű `THEME` változón keresztül olvassa a színeket - ha
# a jövőben egy beállítás-menüben a felhasználó másik témát választ, elég
# a `THEME` nevet egy másik `THEMES[...]` bejegyzésre állítani (az induláskor
# rögzített stílusú elemek, pl. néhány gomb-stílus, ilyenkor egy `apply_theme()`
# jellegű újraépítést igényelnének majd - az architektúra erre már felkészült,
# csak a UI hiányzik hozzá).
# ===========================================================================
def _c(hex_str, alpha=255):
    color = QColor(hex_str)
    color.setAlpha(alpha)
    return color


MIDNIGHT = SimpleNamespace(
    name="Midnight Blue",
    ACCENT=_c("#12A6FF"),
    ACCENT_2=_c("#7C5CFF"),
    DANGER=_c("#FF5D6C"),

    CARD_BG=_c("#0E1422", 150),
    CARD_BORDER=_c("#FFFFFF", 40),

    MENU_BG=_c("#0A0F1A", 150),
    MENU_BORDER=_c("#FFFFFF", 36),

    SOLID_BG=_c("#0E1320", 205),
    SOLID_BORDER=_c("#FFFFFF", 40),

    ERROR_BG=_c("#3D1216", 205),
    ERROR_BORDER=_c("#FF7882", 90),

    TEXT="#F3F7FC",
    TEXT_DIM="#9BAAC0",
    TEXT_FAINT="#6C7B90",

    # A forrásváltó ("B") panel - explicit kérésre TÖMÖR, világoskék.
    MODE_PANEL_BG="#D8ECFB",
    MODE_PANEL_BORDER="#A6D2F2",
    MODE_TILE_BG="#FFFFFF",
    MODE_TILE_BORDER="#C3E1F6",
    MODE_TILE_SELECTED_BG="#0B72D9",
    MODE_TILE_TEXT="#0B1220",
    MODE_TILE_DESC="#4A6178",
    MODE_TILE_SELECTED_TEXT="#FFFFFF",
)


AURORA = SimpleNamespace(
    name="Aurora Amber",
    ACCENT=_c("#FF9D4D"),
    ACCENT_2=_c("#FF5E7E"),
    DANGER=_c("#FF5D6C"),

    CARD_BG=_c("#241521", 150),
    CARD_BORDER=_c("#FFFFFF", 40),

    MENU_BG=_c("#1E1220", 150),
    MENU_BORDER=_c("#FFFFFF", 36),

    SOLID_BG=_c("#211526", 205),
    SOLID_BORDER=_c("#FFFFFF", 40),

    ERROR_BG=_c("#3D1216", 205),
    ERROR_BORDER=_c("#FF7882", 90),

    TEXT="#FBF3EE",
    TEXT_DIM="#C9AFC2",
    TEXT_FAINT="#8C7189",

    MODE_PANEL_BG="#FFE9D3",
    MODE_PANEL_BORDER="#F3C79A",
    MODE_TILE_BG="#FFFFFF",
    MODE_TILE_BORDER="#F6D9B8",
    MODE_TILE_SELECTED_BG="#E0752A",
    MODE_TILE_TEXT="#3B2318",
    MODE_TILE_DESC="#7A5A46",
    MODE_TILE_SELECTED_TEXT="#FFFFFF",
)


THEMES = {"midnight": MIDNIGHT, "aurora": AURORA}


# <<< A jövőbeli témaváltáshoz elég ezt a kulcsot átírni (pl. "aurora"-ra). >>>
ACTIVE_THEME_KEY = "midnight"


THEME = THEMES[ACTIVE_THEME_KEY]


ACCENT = THEME.ACCENT.name()


def _set_active_theme(key):
    """Modul-szintű THEME csere - ez az, amire a fájl eleji megjegyzés
    ('ehhez csak egy UI-t kell majd rákötni') utalt. Most már van UI hozzá
    (lásd Beállítások -> Téma): a TVBox.apply_theme() ezt hívja meg, majd
    frissíti a már felépített widgetek színeit is (lásd ott)."""
    global THEME, ACTIVE_THEME_KEY, ACCENT
    if key not in THEMES:
        key = "midnight"
    ACTIVE_THEME_KEY = key
    THEME = THEMES[key]
    ACCENT = THEME.ACCENT.name()
    return THEME


def _volume_bar_stylesheet():
    return VOLUME_BAR_STYLE_TEMPLATE % (THEME.ACCENT.name(), THEME.ACCENT_2.name())


FONT_FALLBACKS = [
    "Inter", "Poppins", "Roboto", "Noto Sans", "Ubuntu",
    "Cantarell", "DejaVu Sans", "Segoe UI", "Arial", "sans-serif",
]


HU_WEEKDAYS = ["hétfő", "kedd", "szerda", "csütörtök", "péntek", "szombat", "vasárnap"]


HU_MONTHS = ["jan.", "febr.", "márc.", "ápr.", "máj.", "jún.",
             "júl.", "aug.", "szept.", "okt.", "nov.", "dec."]


MENU_STYLE = """
QListWidget {
    background: transparent;
    border: none;
    outline: none;
    padding: 4px 2px;
}
QListWidget::item {
    border-radius: 18px;
    margin: 3px 6px;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 4px 2px 4px 0px;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 55);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 90);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


# Megjegyzés: a fenti stílusból SZÁNDÉKOSAN hiányzik a
# `QListWidget::item:selected` / `:hover` háttérszabály. A kijelölést és a
# hover-kiemelést mostantól maga a sor-widget (ChannelItemWidget) rajzolja
# meg saját magának - lásd a fájl elején lévő 4. pontot arról, hogy ez
# miért old meg egy görgetéssel kapcsolatos, korábbi vizuális hibát.

VOLUME_BAR_STYLE_TEMPLATE = """
QProgressBar {
    background-color: rgba(255, 255, 255, 30);
    border: none;
    border-radius: 4px;
    height: 8px;
}
QProgressBar::chunk {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 %s, stop:1 %s
    );
    border-radius: 4px;
}
"""


VOLUME_BAR_STYLE = _volume_bar_stylesheet()


def set_translucent(widget):
    """Biztosítja, hogy a widget saját maga körül ne fessen tömör hátteret -
    ez minden egyes, kártyákon belül használt widgetre vonatkozik (feliratok,
    listák, sávok), nem csak a kártyák külső keretére."""
    widget.setAttribute(Qt.WA_TranslucentBackground, True)
    widget.setAttribute(Qt.WA_NoSystemBackground, True)


def _font(size, weight=QFont.Normal, family=None):
    f = QFont(family or FONT_FALLBACKS[0], size)
    f.setWeight(weight)
    if hasattr(f, "setFamilies"):
        f.setFamilies(FONT_FALLBACKS)
    return f


def _label(text="", size=14, weight=QFont.Normal, color=None, align=None, wrap=False):
    lbl = QLabel(text)
    lbl.setStyleSheet("color: %s; background: transparent;" % (color or THEME.TEXT))
    lbl.setFont(_font(size, weight))
    if align is not None:
        lbl.setAlignment(align)
    if wrap:
        lbl.setWordWrap(True)
    return lbl
