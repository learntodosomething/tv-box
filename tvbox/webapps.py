# -*- coding: utf-8 -*-
"""Beépített webnézet (YouTube) és külső alkalmazások indítása, módváltás."""
import subprocess
from PyQt5.QtCore import (QEvent, QTimer, QUrl, Qt)
from tvbox.compat import (QWebEnginePage, QWebEngineProfile, QWebEngineScript, QWebEngineUrlRequestInterceptor, QWebEngineView, WEBENGINE_AVAILABLE, logger)
from tvbox.external_apps import EXTERNAL_APPS, WEB_APPS, WEB_APP_ORDER, _resolve_app_command
from tvbox.youtube import YOUTUBE_ADBLOCK_JS, YouTubeAdBlockInterceptor, _prepare_webengine_storage_dir


class WebAppMixin:

    # ------------------------------------------------------------------
    # Beépített ("appon belüli") web-alkalmazások - QtWebEngine
    #
    # UGYANÚGY lehet köztük és a TV/Rádió között váltani, mint TV és Rádió
    # között: a forrásváltó ("B") menüben egy csempe, a kiválasztásra a
    # teljes ablak azonnal a web-tartalomra vált (nem nyílik külön ablak).
    # ------------------------------------------------------------------
    def _build_web_view(self):
        """Az egyetlen, újrafelhasznált QWebEngineView létrehozása -
        LUSTÁN, csak az első tényleges használatkor (nem induláskor), hogy
        ne lassítsa a program indulását és ne egyen memóriát, ha a
        felhasználó sosem nyitja meg a YouTube-ot."""
        # VÉDŐHÁLÓ: ha nincs beépített webalkalmazás engedélyezve, a Chromium-ot
        # SOHA nem hozzuk létre (hidegindításkor natív access violation volt).
        if not WEBENGINE_AVAILABLE or not WEB_APP_ORDER:
            self.web_view = None
            return
        try:
            view = QWebEngineView(self.central)
            view.setStyleSheet("background-color: black;")

            # SAJÁT, NEVESÍTETT profil - SZÁNDÉKOSAN nem az implicit
            # "alapértelmezett" QtWebEngine-profilt használjuk (amit
            # `view.page().profile()` egy friss QWebEngineView-nál magától
            # visszaadna). Az alapértelmezett profil megosztott, és a hozzá
            # tartozó, lemezen élő Chromium-zároló-fájlok rendellenes
            # kilépés után "beragadhatnak" - ez volt a legvalószínűbb oka
            # annak, hogy a YouTube-nézet néha összeomlott, ha korábban már
            # egyszer megnyitották, majd a programot újraindították. Egy
            # külön, ehhez az alkalmazáshoz kötött, kontrollált tárolási
            # útvonalú profil (lásd _prepare_webengine_storage_dir) ettől
            # a kockázati osztálytól szerkezetileg elszigetel.
            if QWebEngineProfile is not None and QWebEnginePage is not None:
                storage_dir = _prepare_webengine_storage_dir()
                profile = QWebEngineProfile("tvbox_youtube", self)
                if storage_dir:
                    profile.setPersistentStoragePath(storage_dir)
                    profile.setCachePath(storage_dir)
                profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
                # Egy Smart TV böngésző azonosítja magát, hogy a YouTube a
                # nyilakkal/Enterrel navigálható "Leanback" (TV-optimalizált)
                # felületet szolgálja ki a youtube.com/tv címen, NE a sima,
                # egérre tervezett asztali oldalra irányítson át - lásd a
                # WEB_APPS["youtube"]["url"] melletti megjegyzést.
                user_agent = WEB_APPS.get("youtube", {}).get("user_agent")
                if user_agent:
                    profile.setHttpUserAgent(user_agent)
                self._web_profile = profile
                page = QWebEnginePage(profile, view)
                view.setPage(page)
            else:
                self._web_profile = None

            # A kozmetikai blokkolót már DocumentCreation fázisban injektáljuk,
            # nem csak loadFinished után. Így a YouTube reklám UI-ja sokkal
            # kisebb eséllyel villan fel egy pillanatra.
            if QWebEngineScript is not None:
                try:
                    script = QWebEngineScript()
                    script.setName("TVBox YouTube AdBlock")
                    # A DOM műveletekhez a Qt dokumentációja szerint a
                    # DocumentReady a megfelelő pont; DocumentCreation még
                    # túl korai lehet a document/head létrejöttéhez.
                    script.setInjectionPoint(QWebEngineScript.DocumentReady)
                    script.setRunsOnSubFrames(True)
                    script.setWorldId(QWebEngineScript.MainWorld)
                    script.setSourceCode(YOUTUBE_ADBLOCK_JS)
                    view.page().scripts().insert(script)
                    self.youtube_adblock_script = script
                except Exception as e:
                    self.youtube_adblock_script = None
                    logger.warning("Nem sikerült korai YouTube adblock scriptet telepíteni: %s", e)

            if QWebEngineUrlRequestInterceptor is not None:
                self.youtube_adblock_interceptor = YouTubeAdBlockInterceptor()
                self.youtube_adblock_interceptor.set_enabled(True)      # mindig be van kapcsolva
                try:
                    view.page().profile().setUrlRequestInterceptor(
                        self.youtube_adblock_interceptor
                    )
                except AttributeError:
                    view.page().profile().setRequestInterceptor(
                        self.youtube_adblock_interceptor
                    )

            view.loadFinished.connect(self._on_web_load_finished)
            # A billentyűzet-eseményeket ELŐSZÖR nekünk kell látnunk (lásd
            # eventFilter) - ez egy MÁSODIK, a QShortcutokkal párhuzamos
            # védőháló ugyanarra a problémára: a Chromium natív kód szinten
            # fogyasztja el a lenyomott billentyűket, MIELŐTT azok a Qt
            # widget-eseményláncon át a főablak keyPressEvent()-jéhez
            # egyáltalán eljutnának.
            view.installEventFilter(self)
            view.hide()
            self.web_view = view
        except Exception as e:
            logger.warning("Nem sikerült létrehozni a beépített böngésző-nézetet: %s", e)
            self.web_view = None

    def _on_web_load_finished(self, ok):
        if not ok or self.web_view is None:
            return
        if self.active_web_app != "youtube":          # a reklámblokkoló mindig be van kapcsolva
            return
        try:
            self.web_view.page().runJavaScript(YOUTUBE_ADBLOCK_JS)
        except Exception as e:
            logger.warning("Nem sikerült betölteni a YouTube reklámblokkoló JS-t: %s", e)


    def _show_web_app(self, key):
        app = WEB_APPS.get(key)
        if not app:
            return
        # Ha ez az alkalmazás nem beépített módban van engedélyezve, a helyes
        # út a külső (Brave) indítás - nem szabad Chromium-ot létrehozni.
        if key not in WEB_APP_ORDER:
            if key in EXTERNAL_APPS:
                self._launch_external_app(key)
            return

        if self.web_view is None and WEBENGINE_AVAILABLE:
            self._build_web_view()

        if self.web_view is None:
            # A QtWebEngine nem elérhető - ide elvileg nem futhatnánk be,
            # mert ilyenkor a "youtube" már az EXTERNAL_APPS-os, külön
            # ablakos ágon menne (lásd WEB_APP_ORDER fent), de a biztonság
            # kedvéért itt is adunk egy érthető hibaüzenetet.
            self._show_error_message(
                "A beépített böngésző (QtWebEngine) nincs telepítve.\n"
                "Lásd a fájl elején lévő telepítési útmutatót."
            )
            return

        # Kilépünk a jelenlegi TV/Rádió lejátszásból, mielőtt a webnézetre
        # váltanánk - ugyanúgy, ahogy TV<->Rádió váltásnál is csak az egyik
        # forrás "aktív" egyszerre.
        self._stop_playback_for_web_app()

        # A VLC natív video surface-t előbb elrejtjük, és csak utána tesszük
        # láthatóvá a Chromium nézetet. Ez csökkenti a VLC/QtWebEngine
        # kompozitor ütközésének esélyét.
        try:
            self.video_frame.hide()
        except Exception:
            pass

        self.active_web_app = key
        current_url = self.web_view.url().toString()
        if current_url != app["url"]:
            self.web_view.setUrl(QUrl(app["url"]))

        self.web_view.setGeometry(0, 0, self.width(), self.height())
        self.web_view.show()
        self.web_view.raise_()
        # A fókuszváltást is egy külön event-loop körbe tesszük.
        QTimer.singleShot(100, lambda: (
            self.web_view.setFocus()
            if self.web_view is not None and self.active_web_app == key else None
        ))

        # Amíg a webnézet aktív, az Esc és a B billentyű globálisan (a
        # böngésző-nézet fókusza ALATT is) visszahoz a TV Box kezelőfelü-
        # letére - enélkül a beépített böngésző "elnyelné" ezeket a
        # billentyűket, és nem lehetne egyszerűen visszaváltani.
        self._web_exit_shortcut.setEnabled(True)
        self._web_menu_shortcut.setEnabled(True)

    def _stop_playback_for_web_app(self):
        self._halt_playback()
        self.hide_timer.stop()
        self._hide_widget(self.info_card)
        self._hide_widget(self.radio_visualizer)
        self._hide_widget(self.loading_card)
        self._hide_widget(self.error_card)

    def _leave_web_app_if_active(self):
        """Ezt hívja meg minden olyan művelet eleje (csatornaváltás,
        forrásváltás TV/Rádióra), ami a beépített VLC-lejátszást indítaná
        el - így garantált, hogy a webnézet mindig eltűnik, mielőtt a
        videó/rádió újra megjelenne, bármelyik úton is történt a váltás
        (billentyűzet, egér, forrásváltó menü)."""
        if not self.active_web_app:
            return
        self.active_web_app = None
        self._web_exit_shortcut.setEnabled(False)
        self._web_menu_shortcut.setEnabled(False)
        if self.web_view is not None:
            self.web_view.hide()
        try:
            self.video_frame.show()
        except Exception:
            pass

    def eventFilter(self, obj, event):
        """A web_view-ra telepített védőháló (lásd _build_web_view). A
        QShortcut-ok (Esc/B - lásd __init__) a fókusztól függetlenül is
        működnek, de minden MÁS billentyűt (nyilak, számok, M, V stb.) itt,
        közvetlenül a webnézeten fogunk el, MIELŐTT a Chromium natív
        kódja - vagy ami nem várt módon esetleg átszivárogna belőle - bármit
        kezdene velük. Amíg egy beépített webnézet aktív, csak az Esc/B/S -
        egyébként a globális 'menekülő' billentyűk - engedettek; minden mást
        elnyelünk (a lapnak magának kell kezelnie, pl. a youtube.com/tv
        saját nyíl-navigációját), de NEM engedjük át a főablak normál
        csatornaváltó/menünyitó logikájához."""
        if (self.web_view is not None and obj is self.web_view
                and event.type() == QEvent.KeyPress):
            key_code = event.key()
            text = event.text()
            if key_code == Qt.Key_Escape:
                self._leave_web_app_and_resume()
                return True
            if text.lower() == "b":
                self._open_mode_menu_from_web_app()
                return True
            if text.lower() == "s":
                self.toggle_settings()
                return True
            if text.lower() == "h" or text == "?":
                self.open_help()
                return True
            if text.lower() == "m":
                # Szándékosan elnyeljük - amíg a webnézet aktív, ne
                # nyithassa meg a csatornalistát (lásd a hibajelentést).
                return True
        return super().eventFilter(obj, event)

    def _leave_web_app_and_resume(self):
        """Az Esc (böngészőben) globális gyorsbillentyűjéhez: kilép a
        webnézetből, és visszatér a legutóbb lejátszott TV/Rádió
        csatornához - ugyanolyan azonnali váltás-élménnyel, mint TV és
        Rádió közti váltásnál."""
        if not self.active_web_app:
            return
        self._leave_web_app_if_active()
        self.setFocus()
        key = self.current_key or (self.channel_keys[0] if self.channel_keys else None)
        if key:
            self.play_channel(key)

    def _open_mode_menu_from_web_app(self):
        """A B billentyű globális gyorsbillentyűjéhez, amíg egy beépített
        webnézet (pl. YouTube) aktív.

        FONTOS: ennek KAPCSOLÓNAK (toggle) kell lennie, NEM feltétlenül
        "nyissuk meg"-nek. Mivel ez a metódus egy MINDVÉGIG bekapcsolva
        maradó globális QShortcut-on keresztül fut (amíg active_web_app
        igaz), a MÁSODIK "B" lenyomás ugyanide futna be újra - ha itt
        feltétel nélkül open_mode_menu()-t hívnánk, a menüt SOSEM lehetne
        ezzel a gombbal bezárni, mert minden "B" újra megnyitná (még ha
        már nyitva is volt). Ez pontosan az a hiba volt, amit a
        felhasználó jelentett ("B-vel megnyitja, de nem tudom bezárni").
        """
        if self.mode_menu_visible:
            self.close_mode_menu()
        else:
            self.open_mode_menu()

    def _launch_external_app(self, key):
        """Külső alkalmazás (pl. YouTube a Brave-ben) indítása KÜLÖN
        folyamatként, TELJES KÉPERNYŐS ("kiosk") módban - ugyanúgy
        képernyőt betöltve, mint a beépített TV/Rádió lejátszás. Ez
        SZÁNDÉKOSAN nem a beépített VLC-lejátszóval történik - a Brave a
        saját ablakában, a rendszer ablakkezelőjének felügyelete alatt
        fut. Mivel a TV Box fullscreen kiosk-ablakként fut, előtte
        minimalizáljuk, hogy ne takarja el a böngészőt; amikor a
        felhasználó bezárja azt (lásd _check_external_processes lejjebb),
        a TV Box automatikusan visszaáll teljes képernyőre."""
        app = EXTERNAL_APPS.get(key)
        if not app:
            return

        command = _resolve_app_command(app)
        if not command:
            logger.warning(
                "Nem található futtatható a(z) '%s' külső alkalmazáshoz "
                "(sem a PATH-on, sem az extra_paths listában).", key
            )
            self._show_error_message(
                "%s nem található.\nÍrd be az elérési utat: EXTERNAL_APPS." % app["label"]
            )
            return

        # Dupla indítás ellen (Enter-spam): ha már fut, nem indítunk újat.
        running = self._external_processes.get(key)
        if running is not None and running.poll() is None:
            return

        try:
            # JAVÍTVA: eddig a VLC a háttérben tovább játszott (hang + sávszél),
            # amíg a Brave-ben nézték a YouTube-ot.
            self._halt_playback()
            self._hide_widget(self.loading_card)
            proc = subprocess.Popen(command + app["args"])
            self._external_processes[key] = proc
            self.external_watch_timer.start(1000)
            self.showMinimized()
        except Exception as e:
            logger.warning("Nem sikerült elindítani a(z) %s alkalmazást: %s", key, e)
            self._show_error_message("Nem sikerült elindítani: %s" % app["label"])

    def _check_external_processes(self):
        """Másodpercenként lefutó ellenőrzés: lezárult-e már valamelyik,
        korábban elindított külső alkalmazás (pl. a felhasználó Alt+F4-fel
        vagy Esc-kel bezárta a Brave/YouTube kiosk-ablakot)? Ha igen, a TV
        Box automatikusan visszaáll teljes képernyőre - a felhasználónak
        nem kell manuálisan Alt+Tab-oznia, ugyanolyan "azonnal átvált a
        kép" élményt ad, mint a TV/Rádió közti váltás."""
        finished_keys = [key for key, proc in self._external_processes.items()
                          if proc.poll() is not None]
        for key in finished_keys:
            del self._external_processes[key]
            logger.info("A külső alkalmazás (%s) bezárult - visszaállítom a TV Box-ot.", key)
            self._restore_after_external_app()
        if not self._external_processes:
            self.external_watch_timer.stop()

    def _restore_after_external_app(self):
        if getattr(self, "standby", False):
            # Készenlétben bezárt külső alkalmazás: az ablakot visszaállítjuk, de a lejátszást
            # NEM indítjuk el (a bekapcsolás - leave_standby - folytatja).
            self.showNormal()
            self.showFullScreen()
            return
        # A showNormal() -> showFullScreen() sorrend azért kell, mert egy
        # minimalizált ablakot néhány ablakkezelő nem hoz vissza helyesen
        # közvetlenül teljes képernyőre showFullScreen()-nel egyedül.
        self.showNormal()
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        # A kilépéskor leállított lejátszás folytatása a legutóbbi csatornán.
        if self.current_key:
            self.play_channel(self.current_key)

    def switch_mode(self, new_mode):
        if new_mode not in self.sources:
            return
        self._cancel_preview()
        # Ha épp egy webnézet (pl. YouTube) volt aktív, ezt mindenképp el
        # kell hagyni - még akkor is, ha a "mögötte" lévő forrás (self.mode)
        # időközben nem változott, mert enélkül a webnézet a képernyőn
        # ragadna, amikor a felhasználó pl. újra a "TV" csempére kattint.
        was_in_web_app = self.active_web_app is not None
        self._leave_web_app_if_active()

        if new_mode == self.mode and not was_in_web_app:
            return

        self.mode = new_mode
        key = self.current_key or (self.channel_keys[0] if self.channel_keys else None)
        if key:
            self.play_channel(key)
        else:
            # A forrásnak (egyelőre) nincs tartalma - legalább a UI váltson.
            self._hide_widget(self.radio_visualizer)
            self._refresh_menu_items()
        self.save_timer.start(400)
