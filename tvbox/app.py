# -*- coding: utf-8 -*-
"""A TVBox főablak és a program belépési pontja."""
import sys
import vlc
from PyQt5.QtWidgets import (QApplication, QMainWindow, QShortcut, QWidget)
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtCore import (QSharedMemory, QTimer, QUrl, Qt)
from datetime import datetime
from tvbox.channels import SOURCES, _build_source_state
from tvbox.compat import WEBENGINE_AVAILABLE, logger
from tvbox.config import SETTINGS_SCHEMA, load_settings, save_settings, VLC_BASE_ARGS, VLC_OPTIONAL_ARGS
from tvbox.external_apps import WEB_APP_ORDER
from tvbox.player import PlayerSignals
from tvbox.theme import (FONT_FALLBACKS, HU_MONTHS, HU_WEEKDAYS, _set_active_theme)
from tvbox.ui_build import UIBuildMixin
from tvbox.player import PlayerMixin
from tvbox.menus import MenuMixin
from tvbox.webapps import WebAppMixin
from tvbox.panels import PanelMixin
from tvbox.input import InputMixin


# A beépített (QtWebEngine) YouTube jelenleg ki van kapcsolva (WEB_APP_ORDER
# üres), a YouTube külön Brave-ablakban fut. Ilyenkor a Chromium-t sem
# előmelegítjük, és a GL-kontextus megosztást sem kapcsoljuk be: kevesebb
# RAM, gyorsabb indulás, és nincs két natív kompozitor egy ablakban.
EMBEDDED_WEB_ENABLED = bool(WEBENGINE_AVAILABLE and WEB_APP_ORDER)


def main():
    # A Qt dokumentáció kifejezetten javasolja, hogy ez az attribútum MÁR a
    # QApplication létrehozása ELŐTT be legyen állítva, ha QtWebEngine-t
    # használunk (a beépített YouTube-nézethez) EGYÜTT egy natív videó-
    # kimenettel (a VLC saját X11/EGL-alapú megjelenítésével). Enélkül a
    # kettő GPU-kontextusa ütközhet - ez a legvalószínűbb magyarázat arra,
    # hogy YouTube-ról visszaváltva néha nem jelent meg a kép a TV-n, és
    # valószínűleg hozzájárult a beágyazott böngésző ismételt megnyitásakor
    # tapasztalt összeomláshoz is.
    if EMBEDDED_WEB_ENABLED:
        QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)

    # Egyetlen-példány védelem: ha véletlenül kétszer indulna el a program
    # (pl. egy indítószkript hibásan duplán hívja meg), a második példány
    # itt szépen kilép ahelyett, hogy megosztott versenyhelyzetben írná
    # ugyanazt a beállításfájlt az elsővel. A `shared_mem` objektumot
    # életben kell tartani a program teljes futása alatt (ezért nem egy
    # lokális, azonnal eldobott változó) - amíg `app.exec_()` fut, ez a
    # `main()` hívási keret nem szűnik meg, tehát a hivatkozás megmarad.
    shared_mem = QSharedMemory("HU.TVBox.SingleInstanceLock.v1")
    # JAVÍTVA: Linuxon egy összeomlás után a szegmens "árván" megmarad, és a
    # következő indítás hibásan azt hitte, hogy a program már fut. Ha senki
    # nem használja, az attach+detach törli; ha tényleg fut egy példány,
    # a create() ettől még helyesen elbukik.
    if shared_mem.attach():
        shared_mem.detach()
    if not shared_mem.create(1):
        logger.warning("A TV Box már fut egy másik példányban - kilépés.")
        sys.exit(0)

    default_font = QFont(FONT_FALLBACKS[0], 10)
    if hasattr(default_font, "setFamilies"):
        default_font.setFamilies(FONT_FALLBACKS)
    app.setFont(default_font)

    window = TVBox()
    sys.exit(app.exec_())


class TVBox(UIBuildMixin, PlayerMixin, MenuMixin, WebAppMixin, PanelMixin, InputMixin, QMainWindow):

    PANEL_WIDTH = 380

    def __init__(self):
        super().__init__()

        # --- Források (TV, Rádió, ...) felépítése ---
        self.sources = {}
        self.mode_order = []
        for mode_key, icon, label, menu_title, unit, data in SOURCES:
            state = _build_source_state(data)
            state.update(icon=icon, label=label, menu_title=menu_title, unit=unit,
                         current_key=None, previous_key=None)
            self.sources[mode_key] = state
            self.mode_order.append(mode_key)

        if not self.mode_order:
            raise RuntimeError("A SOURCES lista üres - nincs egyetlen forrás sem megadva.")

        # --- Elmentett beállítások betöltése ---
        settings = load_settings()
        self.mode = settings.get("last_mode") if settings.get("last_mode") in self.sources \
            else self.mode_order[0]

        for mode_key, state in self.sources.items():
            saved_key = settings.get("last_channel_%s" % mode_key)
            keys = state["keys"]
            state["current_key"] = saved_key if saved_key in state["channels"] \
                else (keys[0] if keys else None)

        try:
            self.volume = int(settings.get("volume", 80))
        except (TypeError, ValueError):
            self.volume = 80
        self.volume = max(0, min(100, self.volume))
        self.muted = bool(settings.get("muted", False))

        # --- Beállítások (Fényerő / Téma / stb.) betöltése, a SETTINGS_SCHEMA
        # alapértékeivel kiegészítve, ha egy kulcs még hiányzik a mentett
        # fájlból (pl. első indítás, vagy egy régebbi mentés egy korábbi
        # verzióból). ÉRVÉNYESSÉG-ELLENŐRZÉS: ha egy mentett érték már nem
        # szerepel az adott opció listájában (pl. a séma bővült/szűkült),
        # az alapértékre esünk vissza ahelyett, hogy érvénytelen állapotot
        # engednénk be.
        self.settings_data = {}
        saved_settings_block = settings.get("settings") or {}
        for spec in SETTINGS_SCHEMA:
            value = saved_settings_block.get(spec["key"], spec["default"])
            if value not in spec["options"]:
                value = spec["default"]
            self.settings_data[spec["key"]] = value
        learned = saved_settings_block.get("_stream_cache")
        if isinstance(learned, dict):
            self.settings_data["_stream_cache"] = learned

        # A mentett témát MÁR ITT, a UI felépítése ELŐTT aktiváljuk, hogy
        # minden widget rögtön a helyes színekkel épüljön fel (ne kelljen
        # induláskor egy "utólagos" retintelést végrehajtani).
        _set_active_theme(self.settings_data["theme"])

        self.menu_visible = False
        self.mode_menu_visible = False
        self.settings_visible = False
        self.channel_buffer = ""
        self.mode_tiles = []
        self._mode_cursor = 0
        self._settings_cursor = 0

        # Elindított külső alkalmazások (pl. YouTube/Brave) folyamat-
        # objektumai, kulcsuk szerint - lásd _launch_external_app() és
        # _check_external_processes() lejjebb.
        self._external_processes = {}

        # Beépített ("appon belüli") web-alkalmazás állapota - lásd
        # _show_web_app() és a körülötte lévő metódusokat lejjebb.
        self.active_web_app = None
        self.web_view = None
        self.youtube_adblock_interceptor = None

        # --- Csatornalista-gyorsítótár (teljesítmény) ---
        # Korábban MINDEN csatornaváltáskor (nem csak menünyitáskor) a teljes
        # lista törlődött és 50+ egyedi widgetből újraépült - ez egy
        # Raspberry Pi-n érezhető lassulást/akadást okozhat, főleg gyors,
        # egymás utáni csatornaváltásoknál (pl. a nyílgombot nyomva tartva).
        # Most módonként (TV / Rádió / ...) EGYSZER épül fel a lista, utána
        # csatornaváltáskor csak a két érintett sor (a régi és az új aktív)
        # frissül - lásd _ensure_menu_built() / _update_current_highlight().
        self.menu_lists = {}          # mode_key -> QListWidget
        self._menu_row_widgets = {}   # mode_key -> {csatorna_kulcs: (sor, ChannelItemWidget)}
        self._menu_highlighted_key = {}  # mode_key -> jelenleg kiemelt csatorna kulcsa
        self._menu_current_row = {}   # mode_key -> jelenlegi sor index

        self.setWindowTitle("TV Box")
        self.setStyleSheet("background-color: #000000;")

        self.central = QWidget()
        self.setCentralWidget(self.central)

        self._build_video_frame()
        self._build_info_card()
        self._build_menu_panel()
        self._build_mode_menu()
        self._build_settings_panel()
        self._build_radio_visualizer()
        self._build_number_osd()
        self._build_preview_osd()
        self._build_volume_osd()
        self._build_loading_card()
        self._build_error_card()
        self._build_exit_confirm_card()
        self._build_help_card()

        # A mentett fényerőt is alkalmazzuk (ha a kijelző támogatja - lásd
        # _apply_brightness() a részletekért és a hiba-tűrésről).
        self._apply_brightness(self.settings_data["brightness"])

        # --- VLC előkészítése ---
        # FONTOS: az esemény-callbackeket (Playing/Error/Buffering) MÁR ITT,
        # szinkron módon bekötjük - nem egy késleltetett init_vlc()-ben.
        # Egy korábbi verzióban ez 400 ms-mal később történt, ami egy valódi
        # versenyhelyzetet okozott: ha a felhasználó ez alatt a rövid ablak
        # alatt csatornát váltott (pl. beírt egy számot), a lejátszás úgy
        # indult el, hogy MÉG NEM voltak bekötve a callbackek - így sem a
        # "lejátszás elindult", sem a "hiba történt" jelzés nem érkezett meg
        # soha, és a töltés-jelző örökre "beragadt". A callbackek bekötése
        # önmagában nem igényli, hogy az ablak már látható legyen, ezért ezt
        # biztonságos itt, a konstruktorban elvégezni.
        self.instance = self._create_vlc_instance()
        self.player = self.instance.media_player_new()

        # A libVLC event_attach callbackjei NEM a Qt GUI-szálon futnak -
        # csak Qt jelet küldünk, a tényleges UI-módosítás a GUI-szálon történik.
        self.player_signals = PlayerSignals()
        self.player_signals.playing.connect(self._on_stream_playing)
        self.player_signals.error.connect(self._on_stream_error)
        self.player_signals.buffering.connect(self._on_stream_buffering)
        self.player_signals.ended.connect(self._on_stream_ended)
        self._init_playback_helpers()

        try:
            em = self.player.event_manager()
            em.event_attach(
                vlc.EventType.MediaPlayerPlaying,
                lambda e: self.player_signals.playing.emit()
            )
            em.event_attach(
                vlc.EventType.MediaPlayerEncounteredError,
                lambda e: self.player_signals.error.emit()
            )
            em.event_attach(
                vlc.EventType.MediaPlayerEndReached,
                lambda e: self.player_signals.ended.emit()
            )
            em.event_attach(
                vlc.EventType.MediaPlayerBuffering,
                lambda e: self.player_signals.buffering.emit(getattr(e.u, "new_cache", 100.0))
            )
        except Exception as e:
            logger.warning("Nem sikerült bekötni a VLC esemény-callbackeket: %s", e)

        self.player.audio_set_volume(self.volume)
        self.player.audio_set_mute(self.muted)

        # Ide kerül majd az elakadt (soha nem válaszoló) adásokat figyelő
        # "watchdog" időzítő - lásd lejjebb a play_channel()-nél.
        self.watchdog_timer = QTimer(self)
        self.watchdog_timer.setSingleShot(True)
        self.watchdog_timer.timeout.connect(self._on_watchdog_timeout)

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._write_settings)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_time)
        self.clock_timer.start(1000)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(lambda: self._hide_widget(self.info_card))

        self.menu_hide_timer = QTimer(self)
        self.menu_hide_timer.setSingleShot(True)
        self.menu_hide_timer.timeout.connect(self.close_menu)

        self.digit_timer = QTimer(self)
        self.digit_timer.setSingleShot(True)
        self.digit_timer.timeout.connect(self._confirm_digit_buffer)

        self.volume_hide_timer = QTimer(self)
        self.volume_hide_timer.setSingleShot(True)
        self.volume_hide_timer.timeout.connect(lambda: self._hide_widget(self.volume_osd))

        # Kilépés-megerősítés ("Esc / Q kétszer") és a billentyű-súgó állapota
        self._exit_confirm_pending = False
        self.exit_confirm_timer = QTimer(self)
        self.exit_confirm_timer.setSingleShot(True)
        self.exit_confirm_timer.timeout.connect(self._cancel_exit_confirm)

        self.help_visible = False
        self.help_hide_timer = QTimer(self)
        self.help_hide_timer.setSingleShot(True)
        self.help_hide_timer.timeout.connect(self.close_help)

        # Másodpercenként megnézi, lezárult-e már egy elindított külső
        # alkalmazás (pl. a YouTube-ot mutató Brave-ablak) - ha igen,
        # automatikusan visszaállítja a TV Box-ot teljes képernyőre,
        # ugyanúgy, ahogy TV/Rádió váltásnál is azonnal átvált a kép.
        self.external_watch_timer = QTimer(self)
        self.external_watch_timer.timeout.connect(self._check_external_processes)
        # Csak külső alkalmazás indításakor fut (lásd _launch_external_app).

        # A beépített böngésző-nézet (pl. YouTube) SAJÁT KEZELÉST kap a
        # billentyűzeten: amíg fókuszban van, a normál keyPressEvent nem
        # fut le rá (a Chromium-motor "nyeli el" a billentyűket). Ez a két
        # gyorsbillentyű viszont - mivel a QMainWindow-hoz van kötve, nem
        # egy adott widgethez - AKKOR IS működik, ha épp a böngésző-nézeté
        # a fókusz, így mindig lehet Esc-kel vagy B-vel visszaváltani.
        # NORMÁL esetben (amíg nincs aktív webnézet) KI vannak kapcsolva,
        # hogy ne módosítsák a megszokott Esc/B viselkedést máshol.
        self._web_exit_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._web_exit_shortcut.setEnabled(False)
        self._web_exit_shortcut.activated.connect(self._leave_web_app_and_resume)

        self._web_menu_shortcut = QShortcut(QKeySequence(Qt.Key_B), self)
        self._web_menu_shortcut.setEnabled(False)
        self._web_menu_shortcut.activated.connect(self._open_mode_menu_from_web_app)

        self.setFocusPolicy(Qt.StrongFocus)
        self.showFullScreen()
        # A videó-kimenet (winId) beágyazása és az első csatorna elindítása
        # már NEM késleltetett timerrel történik - lásd a fenti magyarázatot
        # a callback-bekötésnél arról, hogy ez miért szüntet meg egy valódi
        # versenyhelyzetet induláskor.
        self.init_vlc()

        # V26: QtWebEngine előmelegítése még azelőtt, hogy a felhasználó
        # Enterrel megnyithatná a YouTube-ot.
        #
        # A teszt alapján hideg indulás után az első YouTube-nyitás Enterrel
        # natív crash/fagyás, egérkattintással viszont működik, és utána az
        # Enter is működik. Ez arra utal, hogy a QWebEngine/Chromium első
        # inicializálása történik rossz időpillanatban, miközben az Enter
        # esemény feldolgozása zajlik.
        #
        # Ezért a WebEngine objektumot egyszer, nyugodt állapotban létrehozzuk.
        # Nem mutatjuk meg és nem töltjük be a YouTube-ot, így a VLC-képhez
        # nem nyúlunk hozzá. A későbbi YouTube-nyitáskor már nem kell
        # QWebEngineView-t létrehozni.
        if EMBEDDED_WEB_ENABLED:
            QTimer.singleShot(1800, self._prewarm_web_engine)

    def _create_vlc_instance(self):
        """VLC-példány létrehozása lépcsőzetes visszaeséssel. Ismeretlen
        kapcsolónál a libvlc_new() NULL-t ad (python-vlc: None), ezért nem
        elég a try/except - az eredményt is ellenőrizzük."""
        attempts = [VLC_BASE_ARGS + VLC_OPTIONAL_ARGS, VLC_BASE_ARGS, []]
        for args in attempts:
            try:
                inst = vlc.Instance(args) if args else vlc.Instance()
            except Exception as e:
                logger.warning("VLC indítás sikertelen (%s): %s", args, e)
                continue
            if inst is not None:
                if args != attempts[0]:
                    logger.warning("VLC a szűkített kapcsolókkal indult: %s", args)
                return inst
        raise RuntimeError("A libVLC nem indítható - ellenőrizd a VLC telepítését "
                           "(a python-vlc és a VLC bitszámának egyeznie kell).")

    def _prewarm_web_engine(self):
        """V26: a QtWebEngine első inicializálását ne az Enter esemény közben
        végezzük el. A nézet rejtve marad; csak a Chromium/QtWebEngine objektum-
        láncot hozzuk létre egyszer, indulás után nyugodt állapotban."""
        if not WEBENGINE_AVAILABLE:
            return
        if getattr(self, "web_view", None) is not None:
            return
        try:
            self._build_web_view()
            if self.web_view is not None:
                self.web_view.setUrl(QUrl("about:blank"))
                self.web_view.hide()
                logger.info("V26: QtWebEngine előmelegítve; YouTube Enter-indításra kész.")
        except Exception as e:
            logger.warning("V26: QtWebEngine előmelegítés sikertelen: %s", e)

    # ------------------------------------------------------------------
    # Az aktív forrás (TV / Rádió / ...) adatai - mindig a self.mode
    # szerinti állapotra mutatnak. Forrásváltáskor csak a self.mode
    # változik, minden más automatikusan követi.
    # ------------------------------------------------------------------
    @property
    def channels(self):
        return self.sources[self.mode]["channels"]

    @property
    def categories(self):
        return self.sources[self.mode]["categories"]

    @property
    def channel_keys(self):
        return self.sources[self.mode]["keys"]

    @property
    def current_key(self):
        return self.sources[self.mode]["current_key"]

    @current_key.setter
    def current_key(self, value):
        self.sources[self.mode]["current_key"] = value

    @property
    def previous_key(self):
        return self.sources[self.mode]["previous_key"]

    @previous_key.setter
    def previous_key(self, value):
        self.sources[self.mode]["previous_key"] = value

    # ------------------------------------------------------------------
    # Óra
    # ------------------------------------------------------------------
    def update_time(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M"))
        weekday = HU_WEEKDAYS[now.weekday()]
        self.date_label.setText("%s, %s %d." % (weekday, HU_MONTHS[now.month - 1], now.day))

    # ------------------------------------------------------------------
    # Beállítások mentése
    # ------------------------------------------------------------------
    def _write_settings(self):
        data = {
            "last_mode": self.mode,
            "volume": self.volume,
            "muted": self.muted,
            "settings": dict(self.settings_data),
        }
        for mode_key, state in self.sources.items():
            data["last_channel_%s" % mode_key] = state["current_key"]
        save_settings(data)

    def closeEvent(self, event):
        # Bezáráskor ne hívjunk setPage(None)-t a QWebEngineView-on:
        # a Chromium processz és a QtWebEngine page leválasztása a Qt
        # natív komponenseinek leállása közben összeomlást okozhat.
        self._exit_confirm_pending = False
        try:
            self.exit_confirm_timer.stop()
        except Exception:
            pass

        self._web_exit_shortcut.setEnabled(False)
        self._web_menu_shortcut.setEnabled(False)

        if self.web_view is not None:
            try:
                self.web_view.hide()
            except Exception:
                pass
        self.active_web_app = None

        for name in ("play_debounce_timer", "stall_timer", "retry_timer",
                     "buffer_card_timer", "watchdog_timer", "external_watch_timer"):
            try:
                getattr(self, name).stop()
            except Exception:
                pass

        self._write_settings()
        # A leállítást és a felszabadítást a munkaszál végzi/előzi meg. Ha egy
        # VLC-hívás épp beragadt (nem válaszoló szerver), NEM szabadítunk fel
        # semmit alatta - a folyamat kilépésével úgyis megszűnik, és így nincs
        # összeomlás a kilépéskor.
        try:
            stopped = self.worker.close(timeout=4.0)
        except Exception:
            stopped = False
        if stopped:
            try:
                self.player.release()
                self.instance.release()
            except Exception:
                pass
        else:
            logger.warning("A VLC munkaszál nem állt le időben - felszabadítás kihagyva.")

        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Elrendezés
    # ------------------------------------------------------------------
    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        self.video_frame.setGeometry(0, 0, w, h)

        if self.web_view is not None:
            self.web_view.setGeometry(0, 0, w, h)

        card_w, card_h, margin = 480, 100, 28
        self.info_card.setGeometry(margin, h - card_h - margin, card_w, card_h)

        panel_w = self.PANEL_WIDTH
        if self.menu_visible:
            self.menu_panel.setGeometry(w - panel_w, 0, panel_w, h)
        else:
            self.menu_panel.setGeometry(w, 0, panel_w, h)

        mw, mh = self.mode_menu.width(), self.mode_menu.height()
        self.mode_menu.move((w - mw) // 2, (h - mh) // 2)

        sw, sh = self.settings_panel.width(), self.settings_panel.height()
        self.settings_panel.move((w - sw) // 2, (h - sh) // 2)

        rw, rh = self.radio_visualizer.width(), self.radio_visualizer.height()
        self.radio_visualizer.move((w - rw) // 2, (h - rh) // 2)

        nw, nh = self.number_osd.width(), self.number_osd.height()
        self.number_osd.move((w - nw) // 2, h - nh - 50)

        self.volume_osd.move((w - self.volume_osd.width()) // 2, 40)
        self.preview_osd.move(w - self.preview_osd.width() - 28, 28)

        lw, lh = self.loading_card.width(), self.loading_card.height()
        self.loading_card.move((w - lw) // 2, (h - lh) // 2)

        ew, eh = self.error_card.width(), self.error_card.height()
        self.error_card.move((w - ew) // 2, (h - eh) // 2)

        xw, xh = self.exit_confirm_card.width(), self.exit_confirm_card.height()
        self.exit_confirm_card.move((w - xw) // 2, (h - xh) // 2)

        hcw, hch = self.help_card.width(), self.help_card.height()
        self.help_card.move((w - hcw) // 2, (h - hch) // 2)

        super().resizeEvent(event)


if __name__ == "__main__":
    main()
