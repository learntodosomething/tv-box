# -*- coding: utf-8 -*-
"""Saját Qt widgetek (panelek, csempék, listaelemek, animációk)."""
from PyQt5.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRegion)
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget)
from PyQt5.QtCore import (QRectF, QSize, QTimer, Qt, pyqtProperty, pyqtSignal)
from tvbox.theme import _font, _label, set_translucent
from tvbox import theme


# ===========================================================================
# GlassPanel - önmagát rajzoló "üveg" kártya
#
# - Nincs QGraphicsDropShadowEffect / QGraphicsOpacityEffect (ezek okozták
#   a libVLC natív videófelületével ütköző painter-hibákat egy korábbi
#   verzióban).
# - setMask()-kal a widget "doboza" pontosan a lekerekített (+ árnyék)
#   alakra van vágva, így a sarkoknál soha nem látszódhat sötét négyzet.
# - Az árnyék koncentrikus, EGYMÁST NEM ÁTFEDŐ gyűrűkből épül fel, hogy ne
#   adódjanak össze a rétegek egy jól látható, kemény szélű karikává.
# - `glass=True` esetén finom színátmenetes kitöltést, színátmenetes
#   szegélyt és egy halvány felső fénycsíkot kap az "üveg" hatásért.
# ===========================================================================
class GlassPanel(QWidget):
    def __init__(self, parent=None, radius=24, bg=None, border=None,
                 shadow=True, margin=16, glass=False):
        super().__init__(parent)
        set_translucent(self)
        self._radius = radius
        self._bg = QColor(bg) if bg is not None else QColor(theme.THEME.SOLID_BG)
        self._border = QColor(border) if border is not None else QColor(theme.THEME.SOLID_BORDER)
        self._shadow = shadow
        self._margin = margin
        self._glass = glass
        self._opacity = 1.0
        self._cache = None       # előrenderelt háttér (árnyék+kitöltés+keret)
        self._cache_key = None

        self._content = QVBoxLayout(self)
        self._content.setContentsMargins(margin, margin, margin, margin + 4)

    # -- a "fade" animációhoz használt valódi Qt property (nem effekt!) --
    def _get_opacity(self):
        return self._opacity

    def _set_opacity(self, value):
        self._opacity = value
        self.update()

    opacity = pyqtProperty(float, fget=_get_opacity, fset=_set_opacity)

    def contentLayout(self):
        return self._content

    def set_colors(self, bg=None, border=None):
        """Élő témaváltáshoz: a kártya háttér-/keretszíne a konstruktorban
        rögzül (self._bg/self._border), NEM olvassa újra a globális THEME-et
        minden rajzoláskor - ezt a metódust kell hívni utólag, ha a téma
        megváltozik (lásd TVBox.apply_theme())."""
        if bg is not None:
            self._bg = QColor(bg)
        if border is not None:
            self._border = QColor(border)
        self.update()

    # -- geometria --
    def _card_rect(self):
        m = self._margin
        return QRectF(self.rect()).adjusted(m - 6, m - 8, -(m - 6), -(m - 2))

    def _boundary_rect_radius(self, rect, i):
        """A kártya körüli i-edik (0 = maga a kártya) árnyékgyűrű határa."""
        if i <= 0:
            return rect, self._radius
        spread = i * 2.2
        r = rect.adjusted(-spread, -spread + 4, spread, spread + 6)
        return r, self._radius + spread

    def _boundary_path(self, rect, i):
        r, radius = self._boundary_rect_radius(rect, i)
        path = QPainterPath()
        path.addRoundedRect(r, radius, radius)
        return path

    def _outer_bounds(self, rect):
        if not self._shadow:
            return rect, self._radius
        return self._boundary_rect_radius(rect, 6)

    def resizeEvent(self, event):
        self._rebuild_mask()
        super().resizeEvent(event)

    def showEvent(self, event):
        self._rebuild_mask()
        super().showEvent(event)

    def _rebuild_mask(self):
        rect = self._card_rect()
        mask_rect, mask_radius = self._outer_bounds(rect)
        path = QPainterPath()
        path.addRoundedRect(mask_rect, mask_radius, mask_radius)
        try:
            region = QRegion(path.toFillPolygon().toPolygon())
        except Exception:
            region = QRegion(self.rect())
        self.setMask(region)

    # -- rajzolás --
    def paintEvent(self, event):
        # TELJESÍTMÉNY: az árnyék 6 gyűrűje QPainterPath-különbségekből áll,
        # ami drága; korábban ez MINDEN újrafestésnél lefutott (pl. a
        # forgó spinner 60 fps-nél a töltés-kártyán). Most csak méret-,
        # szín- vagy DPR-változáskor renderelünk, egyébként egy pixmap-másolás.
        dpr = self.devicePixelRatioF()
        key = (self.width(), self.height(), self._bg.rgba(), self._border.rgba(),
               self._glass, self._shadow, dpr)
        if self._cache is None or self._cache_key != key:
            self._cache = self._render_cache(dpr)
            self._cache_key = key
        painter = QPainter(self)
        painter.setOpacity(self._opacity)
        painter.drawPixmap(0, 0, self._cache)

    def _render_cache(self, dpr):
        pm = QPixmap(max(1, int(self.width() * dpr)), max(1, int(self.height() * dpr)))
        pm.setDevicePixelRatio(dpr)
        pm.fill(Qt.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self._card_rect()

        if self._shadow:
            self._paint_soft_shadow(painter, rect)

        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)

        if self._glass:
            gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            top_c = QColor(self._bg)
            top_c.setAlpha(min(255, self._bg.alpha() + 35))
            bottom_c = QColor(self._bg)
            bottom_c.setAlpha(max(0, self._bg.alpha() - 30))
            gradient.setColorAt(0.0, top_c)
            gradient.setColorAt(1.0, bottom_c)
            painter.fillPath(path, gradient)
        else:
            painter.fillPath(path, self._bg)

        if self._glass:
            border_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            border_gradient.setColorAt(0.0, QColor(255, 255, 255, 75))
            border_gradient.setColorAt(1.0, QColor(255, 255, 255, 18))
            pen = QPen(QBrush(border_gradient), 1.3)
        else:
            pen = QPen(self._border)
            pen.setWidthF(1.3)
        painter.setPen(pen)
        painter.drawPath(path)

        if self._glass:
            self._paint_glass_sheen(painter, rect)

        painter.end()
        return pm

    def _paint_soft_shadow(self, painter, rect):
        """Koncentrikus, EGYMÁST NEM ÁTFEDŐ gyűrűk - mindegyik pixel pontosan
        egyszer kap színt, ezért nem adódnak össze a rétegek egy kemény
        szélű, sötét karikává, hanem tényleg sima az elhalványulás."""
        prev_path = self._boundary_path(rect, 0)
        for i in range(1, 7):
            path_i = self._boundary_path(rect, i)
            ring = path_i.subtracted(prev_path)
            alpha = max(2, 18 - i * 3)
            painter.fillPath(ring, QColor(0, 0, 0, alpha))
            prev_path = path_i

    def _paint_glass_sheen(self, painter, rect):
        """Halvány fénycsík a kártya tetején - ettől hat "üvegesnek"."""
        top_h = max(2.0, rect.height() * 0.035)
        sheen_rect = QRectF(
            rect.left() + self._radius * 0.4, rect.top() + 1.4,
            rect.width() - self._radius * 0.8, top_h,
        )
        path = QPainterPath()
        path.addRoundedRect(sheen_rect, top_h / 2, top_h / 2)
        painter.fillPath(path, QColor(255, 255, 255, 26))


class TintedLabel(QWidget):
    """Kis, saját magát rajzoló, színezett hátterű jelvény/felirat.

    FONTOS: NEM szabad QLabel + QSS `background-color` + WA_TranslucentBackground
    kombinációt használni ehhez - Qt-ban ez a kombináció (méréseink szerint)
    EGYÁLTALÁN NEM festi ki az explicit hátteret, csak a szöveg marad látható,
    a színes jelvény/kör/pirula háttere pedig néma csendben eltűnik. Pontosan
    ez okozta korábban, hogy a csatornaszám-jelvények gyakorlatilag
    láthatatlanok voltak. Ez a widget ehelyett - a GlassPanelhez hasonlóan -
    közvetlenül QPainterrel rajzolja ki magát, ami nem érintett ebben a hibában."""

    def __init__(self, text, bg_color, text_color, font, radius=None,
                 padding=(10, 4), fixed_size=None, parent=None):
        super().__init__(parent)
        set_translucent(self)
        self._text = text
        self._bg_color = QColor(bg_color)
        self._text_color = QColor(text_color)
        self._font = font
        self._padding = padding
        self._radius = radius
        if fixed_size:
            self.setFixedSize(*fixed_size)

    def setText(self, text):
        self._text = text
        self.updateGeometry()
        self.update()

    def setColors(self, bg_color, text_color):
        self._bg_color = QColor(bg_color)
        self._text_color = QColor(text_color)
        self.update()

    def sizeHint(self):
        from PyQt5.QtGui import QFontMetrics
        fm = QFontMetrics(self._font)
        w = fm.horizontalAdvance(self._text) + self._padding[0] * 2
        h = fm.height() + self._padding[1] * 2
        return QSize(w, h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(self.rect())
        radius = self._radius if self._radius is not None else rect.height() / 2
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, self._bg_color)
        painter.setPen(self._text_color)
        painter.setFont(self._font)
        painter.drawText(rect, Qt.AlignCenter, self._text)


class AccentStripe(QWidget):
    """Vékony jelzőcsík (pl. a kiválasztott menüelem mellett)."""

    def __init__(self, parent=None, width=4):
        super().__init__(parent)
        set_translucent(self)
        self.setFixedWidth(width)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 2, 2)
        painter.fillPath(path, theme.THEME.ACCENT)


# ===========================================================================
# Betöltés-jelző (spinner)
# ===========================================================================
class SpinnerWidget(QWidget):
    def __init__(self, parent=None, size=52, line_width=5):
        super().__init__(parent)
        set_translucent(self)
        self._angle = 0
        self._line_width = line_width
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)

    def _rotate(self):
        self._angle = (self._angle + 12) % 360
        self.update()

    def showEvent(self, event):
        self._timer.start(33)  # 30 fps elég egy spinnerhez; 60 fps feleslegesen terhelte a GUI-t
        super().showEvent(event)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect().adjusted(
            self._line_width, self._line_width, -self._line_width, -self._line_width
        )
        span = 100 * 16

        track_pen = QPen(QColor(255, 255, 255, 30))
        track_pen.setWidth(self._line_width)
        track_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)

        pen = QPen(theme.THEME.ACCENT)
        pen.setWidth(self._line_width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        start = int(-self._angle * 16)
        painter.drawArc(rect, start, span)


class EqualizerBars(QWidget):
    """Egyszerű, animált "hangsáv" kijelző rádió módhoz."""

    def __init__(self, parent=None, bars=5, width=140, height=44):
        super().__init__(parent)
        set_translucent(self)
        self._bars = bars
        self._levels = [0.35] * bars
        self.setFixedSize(width, height)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)

    def showEvent(self, event):
        self._timer.start(160)
        super().showEvent(event)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def _animate(self):
        import random
        self._levels = [random.uniform(0.25, 1.0) for _ in range(self._bars)]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.width(), self.height()
        gap = 8
        bar_w = (w - gap * (self._bars - 1)) / self._bars

        for i, level in enumerate(self._levels):
            bar_h = max(4.0, h * level)
            x = i * (bar_w + gap)
            y = h - bar_h
            path = QPainterPath()
            path.addRoundedRect(QRectF(x, y, bar_w, bar_h), bar_w / 2, bar_w / 2)
            color = QColor(theme.THEME.ACCENT) if i % 2 == 0 else QColor(theme.THEME.ACCENT_2)
            painter.fillPath(path, color)


# ===========================================================================
# EPG-hez: egysoros, jobbra elidált felirat és vékony folyamatsáv
# ===========================================================================
class ElidedLabel(QLabel):
    """Egysoros felirat, ami a szélességéhez igazítva "..."-ra vágja a hosszú
    szöveget (a QLabel magától nem tud elidálni, és a hosszú műsorcím a
    kártya/lista szélességét tolná szét)."""

    def __init__(self, size=11, weight=QFont.Medium, color=None, parent=None):
        super().__init__("", parent)
        self._full = ""
        self.setStyleSheet("color: %s; background: transparent;" % (color or theme.THEME.TEXT_DIM))
        self.setFont(_font(size, weight))
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumWidth(10)

    def setFullText(self, text):
        self._full = text or ""
        self._apply()

    def fullText(self):
        return self._full

    def resizeEvent(self, event):
        self._apply()
        super().resizeEvent(event)

    def _apply(self):
        elided = self.fontMetrics().elidedText(self._full, Qt.ElideRight, max(10, self.width()))
        if elided != self.text():
            super().setText(elided)


class EpgProgressBar(QWidget):
    """Vékony, saját magát rajzoló folyamatsáv a most futó műsor előrehaladásához."""

    def __init__(self, parent=None, height=4):
        super().__init__(parent)
        set_translucent(self)
        self._fraction = 0.0
        self.setFixedHeight(height)

    def set_fraction(self, value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = 0.0
        value = 0.0 if value != value else max(0.0, min(1.0, value))     # NaN-védelem
        if abs(value - self._fraction) > 0.004:
            self._fraction = value
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect())
        radius = r.height() / 2
        track = QPainterPath()
        track.addRoundedRect(r, radius, radius)
        painter.fillPath(track, QColor(255, 255, 255, 40))
        if self._fraction > 0:
            fill = QPainterPath()
            fill.addRoundedRect(QRectF(r.left(), r.top(), max(r.height(), r.width() * self._fraction), r.height()),
                                radius, radius)
            painter.fillPath(fill, QColor(theme.THEME.ACCENT))



# ===========================================================================
# Menü / lista elemek
# ===========================================================================
class ChannelItemWidget(QWidget):
    """Egy csatorna sora a menüben: jelvény a számmal + név, a kiválasztott
    csatornánál bal oldali színes csíkkal.

    A billentyűzettel navigált "fókusz" (self._focused) ÉS az egérrel való
    ráállás (self._hover) kiemelését is MAGA a widget rajzolja meg saját
    paintEvent-jében - így a kiemelő téglalap sosem tud "elszakadni" a
    valós sortól görgetés közben (ez volt a korábbi vizuális hiba oka)."""

    def __init__(self, key, name, is_current=False, parent=None):
        super().__init__(parent)
        set_translucent(self)
        self._focused = False
        self._hover = False
        self._is_current = False
        self.key = key

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 12, 6)
        layout.setSpacing(12)

        self.stripe = AccentStripe(self, width=4)
        layout.addWidget(self.stripe)

        self.badge = TintedLabel(key, bg_color=QColor(255, 255, 255, 26),
                                  text_color=QColor("#FFFFFF"),
                                  font=_font(13, QFont.Bold), fixed_size=(40, 40))
        layout.addWidget(self.badge)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)
        self.name_label = _label(name, size=14, weight=QFont.Medium,
                                  color=theme.THEME.TEXT_DIM, wrap=True)
        text_col.addWidget(self.name_label)
        # EPG: a most futó műsor címe a név alatt (üres = rejtve, nem foglal helyet)
        self.sub_label = ElidedLabel(size=10, weight=QFont.Medium, color=theme.THEME.TEXT_FAINT)
        self.sub_label.hide()
        text_col.addWidget(self.sub_label)
        layout.addLayout(text_col, 1)

        self.set_current(is_current)

    def set_subtitle(self, text):
        """A név alatti kis sor (EPG: most futó műsor). Csak akkor nyúl a
        widgethez, ha a szöveg ténylegesen változik - a listafrissítés így
        olcsó marad."""
        text = text or ""
        if text == self.sub_label.fullText():
            return
        self.sub_label.setFullText(text)
        self.sub_label.setVisible(bool(text))

    def set_current(self, is_current):
        """A csatorna 'ez van most lejátszva' kiemelését frissíti ANÉLKÜL,
        hogy a widgetet újra kellene építeni - ez teszi lehetővé, hogy
        csatornaváltáskor csak KÉT sort (a régi és az új aktívat) kelljen
        módosítani a listában, ne az egészet (lásd a teljesítmény-
        megjegyzést a _refresh_menu_items()-nél)."""
        self._is_current = is_current
        self.stripe.setVisible(is_current)
        bg_color = QColor(theme.THEME.ACCENT) if is_current else QColor(255, 255, 255, 26)
        fg_color = QColor("#000000") if is_current else QColor("#FFFFFF")
        self.badge.setColors(bg_color, fg_color)
        self.name_label.setFont(_font(14, QFont.DemiBold if is_current else QFont.Medium))
        self.name_label.setStyleSheet(
            "color: %s; background: transparent;" % ("#FFFFFF" if is_current else theme.THEME.TEXT_DIM)
        )

    def set_focused(self, value):
        if self._focused != value:
            self._focused = value
            self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        if self._focused or self._hover:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            path = QPainterPath()
            path.addRoundedRect(QRectF(self.rect()).adjusted(2, 2, -2, -2), 18, 18)
            if self._focused:
                color = QColor(theme.THEME.ACCENT.red(), theme.THEME.ACCENT.green(), theme.THEME.ACCENT.blue(), 48)
            else:
                color = QColor(255, 255, 255, 16)
            painter.fillPath(path, color)
        super().paintEvent(event)


class CategoryHeaderWidget(QWidget):
    """Nem kiválasztható kategória-fejléc a menüben, "chip" stílusú jelvénnyel."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        set_translucent(self)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 6)

        pill = QLabel(text)
        pill.setFont(_font(12, QFont.Bold))
        pill.setStyleSheet(
            "color: %s; background-color: rgba(%d,%d,%d,36); "
            "border-radius: 14px; padding: 5px 12px;" % (
                theme.THEME.ACCENT.name(), theme.THEME.ACCENT.red(), theme.THEME.ACCENT.green(), theme.THEME.ACCENT.blue(),
            )
        )
        layout.addWidget(pill)
        layout.addStretch()


class SettingsRowWidget(QWidget):
    """Egy sor a Beállítások panelen: bal oldalt a beállítás neve, jobb
    oldalt az aktuális érték egy jelvényben. Fel/le mozgás a sorok között,
    balra/jobbra (vagy Enter) az érték léptetéséhez - ugyanaz a mintázat,
    mint a csatornalistánál (fókusz-kiemelést maga a widget rajzolja)."""

    def __init__(self, label, value_text, parent=None, height=46, name_pt=14, badge_pt=12):
        super().__init__(parent)
        set_translucent(self)
        self._focused = False
        self.setFixedHeight(height)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 8, 18, 8)
        layout.setSpacing(14)

        self.name_label = _label(label, size=name_pt, weight=QFont.Medium, color=theme.THEME.TEXT)
        layout.addWidget(self.name_label, 1)

        self.value_badge = TintedLabel(
            value_text, bg_color=QColor(theme.THEME.ACCENT.red(), theme.THEME.ACCENT.green(),
                                         theme.THEME.ACCENT.blue(), 60),
            text_color=QColor(theme.THEME.TEXT), font=_font(badge_pt, QFont.Bold),
            padding=(16, 7),
        )
        layout.addWidget(self.value_badge, 0, Qt.AlignRight)

    def set_focused(self, value):
        if self._focused != value:
            self._focused = value
            self.update()

    def set_value_text(self, text):
        self.value_badge.setText(text)

    def paintEvent(self, event):
        if self._focused:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            path = QPainterPath()
            path.addRoundedRect(QRectF(self.rect()).adjusted(2, 2, -2, -2), 16, 16)
            color = QColor(theme.THEME.ACCENT.red(), theme.THEME.ACCENT.green(), theme.THEME.ACCENT.blue(), 44)
            painter.fillPath(path, color)
        super().paintEvent(event)


class SourceTile(QWidget):
    """Egy nagy, kattintható "csempe" a forrásváltó ('B') menüben - a
    források most EGYMÁS MELLETT (vízszintesen), nem lista formájában
    jelennek meg, kifejezett kérésre."""

    clicked = pyqtSignal(str)

    def __init__(self, mode_key, icon, label, description, parent=None):
        super().__init__(parent)
        self.mode_key = mode_key
        self._selected = False
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(150, 172)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.icon_label = QLabel(icon)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFont(_font(32))
        self.icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.icon_label)

        self.name_label = QLabel(label)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setFont(_font(15, QFont.Bold))
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)

        self.desc_label = QLabel(description)
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setFont(_font(11, QFont.Medium))
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        self.set_selected(False)

    def set_selected(self, selected):
        self._selected = selected
        if selected:
            bg, border, text_color, desc_color = (
                theme.THEME.MODE_TILE_SELECTED_BG, theme.THEME.MODE_TILE_SELECTED_BG,
                theme.THEME.MODE_TILE_SELECTED_TEXT, theme.THEME.MODE_TILE_SELECTED_TEXT,
            )
        else:
            bg, border, text_color, desc_color = (
                theme.THEME.MODE_TILE_BG, theme.THEME.MODE_TILE_BORDER,
                theme.THEME.MODE_TILE_TEXT, theme.THEME.MODE_TILE_DESC,
            )
        self.setStyleSheet(
            "SourceTile { background-color: %s; border: 2px solid %s; border-radius: 24px; }"
            % (bg, border)
        )
        self.name_label.setStyleSheet("color: %s; background: transparent;" % text_color)
        self.desc_label.setStyleSheet("color: %s; background: transparent;" % desc_color)

    def mousePressEvent(self, event):
        self.clicked.emit(self.mode_key)
        super().mousePressEvent(event)


class PillButton(QWidget):
    """Vízszintesen teljes szélességű, pirula alakú gomb - ezzel jelenik meg
    a "Beállítások" a forrásváltó menüben: KÜLÖN elválasztva (saját sor, a
    csempék alatt, elválasztó vonallal), de mégis ugyanabban a menüben,
    ugyanazokkal a nyíl/Enter billentyűkkel elérhetően, mint a TV/Rádió/
    YouTube csempék."""

    clicked = pyqtSignal()

    def __init__(self, icon, label, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(56)
        self._selected = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel(icon)
        self.icon_label.setFont(_font(18))
        self.icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.icon_label)

        self.name_label = QLabel(label)
        self.name_label.setFont(_font(14, QFont.Bold))
        layout.addWidget(self.name_label)

        self.set_selected(False)

    def set_selected(self, selected):
        self._selected = selected
        if selected:
            bg, border, text_color = (
                theme.THEME.MODE_TILE_SELECTED_BG, theme.THEME.MODE_TILE_SELECTED_BG,
                theme.THEME.MODE_TILE_SELECTED_TEXT,
            )
        else:
            bg, border, text_color = (
                "transparent", theme.THEME.MODE_TILE_BORDER, theme.THEME.MODE_TILE_TEXT,
            )
        self.setStyleSheet(
            "PillButton { background-color: %s; border: 2px solid %s; border-radius: 28px; }"
            % (bg, border)
        )
        self.name_label.setStyleSheet("color: %s; background: transparent;" % text_color)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
