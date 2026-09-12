# -*- coding: utf-8 -*-
"""
TV Box - IPTV / Rádió lejátszó (v17 - HU/SK bővítés, v16 képjavítás alapján)
============================================================================
CSATORNALISTA-BŐVÍTÉS (v17, 2026-09-12) - felhasználói kérésre:
  - TV: további HU helyi/közéleti adók (Hír TV, Fix TV, Balaton TV,
    TV Eger, Miskolc TV, Kecskemét TV, Vásárhelyi Televízió) - ezek a
    saját üzemeltetőik közvetlen HLS-stream-jei, nem egy IPTV-
    szolgáltatótól származnak.
  - TV: további szlovák hír-/kereskedelmi csatornák (TA3, JOJ 24,
    JOJ Šport, Wau, Jojko, RTVS Šport) egy közösségi proxy-n
    (sktv.mxnticek.eu) keresztül - kényelmesek, de kicsit kevésbé
    stabilak, mint a közvetlen szolgáltatói URL-ek.
  - RÁDIÓ: új "Szlovák rádióadók" kategória kb. 28-30 adóval, a
    közszolgálati RTVS-csatornáktól (Rádio Slovensko, Devín, Rádio_FM,
    Regina, Patria, Litera, RSI) a legnépszerűbb kereskedelmi
    adókig (Expres, Fun Rádio + al-adói, Europa 2, Vlna, Jemné, Kiss,
    Best FM, Lumen, Anténa Rock, One, SiTy, WOW, Rebeca, Šport, stb.)
  - FONTOS: ezek is nagyrészt ingyenes, harmadik féltől származó
    stream-ek - némelyik időszakosan elérhetetlen lehet.

------------------------------------------------------------------
KORÁBBI (v16) CSATORNALISTA-BŐVÍTÉS (a felhasználó lista.txt fájlja + az
iptv-org közösségi HU/SK gyűjtemény alapján, 2026-09-11):
  - A lista.txt-ben szereplő, korábban a kódba még be nem épített
    csatornák (pl. Ozone TV, Izaura TV, TV7 Békéscsaba, EWTN, Apostol TV,
    UTV, NOE TV, Barrandov, Viasat Explore/History, FB Premium, MTV USA,
    SpongeBob 24/7, Dance Television, valamint több szlovák Markíza-web
    adás) mostantól szerepelnek a CHANNEL_DATA-ban, a "\" elválasztós
    URL-eket "/"-re javítva.
  - A névtelenül szereplő rádió-URL (icast.connectmedia.hu/4738/mr2.mp3)
    a stream-számozás (4724=MR1/Kossuth, 4738=MR2) alapján be lett
    azonosítva Petőfi Rádióként.
  - Új, saját ötletből hozzáadott csatornák (a nyilvánosan elérhető
    iptv-org HU/SK gyűjteményből ellenőrizve): Prime, Super TV2, TV4,
    Sorozat+, Sorozatklub, Story4, Slager TV, Zenebutik, Muzsika TV,
    Kölyökklub, Life TV, M4 Sport, Sport 1/2, Spiler1/2, valamint
    szlovák oldalon Jednotka, Dvojka, :24, Prima Cool/Krimi SK, TV Lux,
    ducktv. Rádióból: Retro Rádió, Kossuth Rádió, Petőfi Rádió,
    MegaDance Rádió, Oxygen Music Radio, Mercy Rádió.
  - FONTOS: ezek nagyrészt ingyenes, harmadik féltől származó stream-ek -
    némelyik időszakosan elérhetetlen lehet, ez a szolgáltatók oldalán
    múlik, nem a lejátszó hibája.

A V16 KÉPJAVÍTÁS:
A v13 volt az utolsó verzió, amelyben a VLC-kép működött. Ezért a
VLC natív videó-kimeneti útvonalát változtatás nélkül visszaállítottuk
a v13-as állapotra. A v14-ben a set_xwindow/set_hwnd/set_nsobject
hívás minden play_channel() előtt újra lefutott; ezt a kísérleti
újrakötést eltávolítottuk. A v14 BrightnessOverlay rétege sincs benne,
így az sem kerülhet a VLC natív videófelülete fölé.

A YouTube/QtWebEngine funkció v13-as állapotban marad.

JAVÍTOTT HIBÁK (v13) - felhasználó által jelentett hibák:

1) ÖSSZEOMLÁS Enter-nyomásra a forrásváltóban a "YouTube" csempén (de
   EGÉR-kattintásra nem). LEGVALÓSZÍNŰBB OK: a `_show_web_app()` a
   QWebEngineView-ra tesz fókuszt, MIKÖZBEN Qt még épp az Enter billentyű-
   esemény kézbesítését végzi a régi fókusz-widgeten - ez egy időzítés-
   érzékeny, natív szintű versenyhelyzetet okozott a Chromium-
   kompozitorral. JAVÍTVA: a webnézet megnyitása most `QTimer.singleShot(0, ...)`-
   tal egy KÖVETKEZŐ eseményhurok-körre van halasztva mind az Enter-, mind
   az egér-úton (utóbbin is, az egységesség és a jövőbeli hibák elkerülése
   végett) - ez strukturálisan kizárja ezt a versenyhelyzetet.

2) "B"-vel meg lehetett nyitni a forrásváltót a YouTube fölött, de UGYANAZZAL
   a "B"-vel nem lehetett bezárni. OK: `_open_mode_menu_from_web_app()`
   feltétel nélkül `open_mode_menu()`-t hívott - mivel ezt egy MINDVÉGIG
   bekapcsolva maradó globális gyorsbillentyű hívja meg (amíg a webnézet
   aktív), minden "B" újra csak MEGNYITOTTA a már nyitva lévő menüt.
   JAVÍTVA: most valódi kapcsoló (toggle) - ha már nyitva van, bezárja.

3) Reklám helyén átmeneti SÖTÉT/BERAGADT képernyő. OK: a beépített YouTube-
   reklámblokkoló bizonyos hirdetés-végpontokat (pl. doubleclick.net,
   /pagead/) hálózati szinten BLOKKOLT - a YouTube Leanback (TV) felülete
   erre nem "reklám nélkül folytatja" választ adott, hanem egy darabig
   hiába várt a (soha meg nem érkező) válaszra, sötét képernyőt mutatva,
   mielőtt felismerte a hibát és továbblépett. A reklámblokkoló tehát
   ZAVARÓBB élményt adott, mint maga a reklám. JAVÍTVA: a "YouTube
   reklámblokkoló" beállítás alapértelmezetten KIKAPCSOLT (a Beállítások
   menüben bármikor visszakapcsolható, de ott számítani kell erre a
   mellékhatásra).

4) YouTube-ról TV-re visszaváltva csak a HANG szólt, a KÉP nem jelent meg -
   és ez utána M/csatornaváltás/hangerő/B megnyomására ÚJRA megismétlődött,
   amíg a felhasználó ki nem kattintott az alkalmazásból (ami kikényszerít
   egy natív újrarajzolást az ablakkezelőnél). ŐSZINTÉN: ez egy MÉLYEN
   GYÖKEREZŐ, driver-/ablakkezelő-függő tünete annak, hogy KÉT FÜGGETLEN
   natív GPU-kompozitor (a VLC saját videó-kimenete ÉS a Chromium/
   QtWebEngine saját kompozitora) osztozik ugyanazon a top-level ablakon -
   ez nem egy "hagyományos" Python-szintű hiba, amit garantáltan meg
   lehetne oldani. BEST-EFFORT MITIGÁCIÓ: minden alkalommal, amikor egy
   overlay (info-kártya, menü, hangerő-kijelző, stb.) megjelenik vagy
   eltűnik, a `_kick_video_repaint()` egy apró (1 pixeles) geometria-
   változtatással "megrugdossa" a VLC natív felületét, kikényszerítve egy
   valódi újrarajzolást. Ez a legtöbb esetben megoldja a tünetet, de NEM
   garantált 100%-osan minden GPU-n/ablakkezelőn - ha ez továbbra is
   jelentkezik, komolyan érdemes megfontolni a YouTube-ot KÜLÖN
   Brave-ablakban futtatni (lásd EXTERNAL_APPS), mert az teljesen
   elkerüli ezt a konfliktust: ott a két natív renderelő sosem osztozik
   egy ablakon.

------------------------------------------------------------------
KORÁBBI (v12) JAVÍTÁSOK
------------------------------------------------------------------

1) Nyilakkal csatornát lehetett váltani, amíg a YouTube-on voltunk.
   OK: a keyPressEvent()-nek fogalma sem volt az `active_web_app`
   állapotról, ezért minden billentyű (nyilak, számok, M, V, Space,
   Backspace) simán átfolyt a normál TV-vezérlő logikába a webnézet
   ALATT. JAVÍTVA: a keyPressEvent() elején (a súgó/Beállítások/
   forrásváltó ellenőrzések UTÁN) most van egy `if self.active_web_app:`
   védőháló, ami amíg a webnézet aktív, KIZÁRÓLAG az Esc/B/S billentyűket
   engedi át, mindent mást elnyel.

2) "M"-mel meg lehetett nyitni a csatornalistát a YouTube fölött.
   Ugyanaz az ok/javítás, mint fent.

3) A beágyazott YouTube néha összeomlott, ha korábban már megnyitották,
   majd a programot újraindították ("crash után ismét jól megy néha").
   LEGVALÓSZÍNŰBB OK: a webnézet az IMPLICIT, megosztott alapértelmezett
   QtWebEngine-profilt használta, aminek lemezen élő Chromium zároló-
   fájljai rendellenes leállás után "beragadhatnak". JAVÍTVA: a webnézet
   most egy SAJÁT, nevesített profilt kap, kontrollált tárolási úttal
   (lásd _prepare_webengine_storage_dir), ami induláskor eltávolítja az
   esetleges beragadt zároló-fájlokat. Emellett visszakerült a
   QApplication.AA_ShareOpenGLContexts beállítás is (ez a VLC natív
   videó-kimenete és a Chromium GPU-folyamata közti kontextus-ütközést
   hivatott elkerülni - ez a másik fő gyanúsított).
   ŐSZINTÉN: ez egy natív (nem Python-szintű) összeomlás volt, amit ebben
   a fejlesztői környezetben nem sikerült 1:1-ben reprodukálni, ezért a
   fenti a legvalószínűbb ok alapján tett, alaposan indokolt javítás -
   nem garantált 100%-os megoldás, de jelentősen csökkenti a kockázatot.

4) "B" megnyomására a YouTube-ról AUTOMATIKUSAN visszaváltott TV-re, még
   mielőtt a felhasználó bármit választott volna a forrásváltóban.
   OK: `_open_mode_menu_from_web_app()` ELŐSZÖR visszaváltott TV/Rádióra,
   és csak UTÁNA nyitotta meg a menüt. JAVÍTVA: most csak megnyitja a
   forrásváltót A YOUTUBE FÖLÖTT (a webnézet aktív marad a háttérben) -
   a tényleges váltás csak akkor történik meg, ha a felhasználó ott
   ténylegesen kiválaszt egy másik forrást.

5) Ezután a TV-n nem jelent meg a kép.
   Ez a 4-es hiba következménye volt (a hibás, elhamarkodott újra-
   lejátszás rossz időzítéssel futott le) - a 4-es javítása után ez a
   tünet is megszűnik; emellett a 3-as pontban leírt GPU-kontextus-
   javítás is közvetlenül ide kapcsolódik.

TOVÁBBI VÁLTOZÁS (v12): a beépített YouTube-nézet URL-je visszaállt a
youtube.com/tv (Leanback, D-pad-navigálható) felületre, Smart TV
user-agenttel - enélkül a Google visszairányít a sima, egérre tervezett
youtube.com-ra.

------------------------------------------------------------------
KORÁBBI (v10) - az "appon belüli" YouTube alapkoncepciója
------------------------------------------------------------------
Ez a verzió a YouTube-ot ténylegesen AZ ALKALMAZÁSON BELÜL nyitja meg
(nem egy külön Brave-ablakban) - ugyanúgy lehet köztük váltani, mint TV
és Rádió között.

ÚJ (v10)
------------------------------------------------------------------
1) A YouTube (és a jövőben bármilyen más web-alkalmazás) most a QtWebEngine
   (Chromium-alapú, Qt-be épített böngésző-motor) segítségével jelenik meg
   közvetlenül a TV Box ablakában, teljes képernyőn - pontosan úgy, ahogy a
   TV/Rádió is. Ehhez egy KÜLÖN csomag telepítése szükséges (lásd a fájl
   elején lévő megjegyzést); ha ez nincs telepítve, a program automatikusan
   visszaesik a korábbi, külön Brave-ablakos módra - semmi nem törik el.
2) A forrásváltó ("B") menüben a YouTube csempe ugyanúgy egy választható
   elem, mint a TV vagy a Rádió - kiválasztásra a teljes ablak azonnal a
   YouTube-ra vált, nem nyílik semmilyen külön ablak.
3) Mivel a beépített böngésző-nézet, amíg fókuszban van, "elnyeli" a
   billentyűket (a Chromium-motor kezeli őket, nem a mi kódunk), az Esc és
   a B billentyű globális gyorsbillentyűként van bekötve, ami AKKOR IS
   működik, ha épp a böngészőé a fókusz - így bármikor egyetlen Esc-kel
   vissza lehet váltani a legutóbb nézett TV/Rádió csatornára, vagy egy
   B-vel egyenesen a forrásváltó menüt lehet megnyitni. Ez a két
   gyorsbillentyű NORMÁL esetben (amíg nincs aktív webnézet) ki van
   kapcsolva, hogy a megszokott Esc/B viselkedés máshol ne változzon.

------------------------------------------------------------------
KORÁBBI (v9) JAVÍTÁSOK
------------------------------------------------------------------
1) A YouTube-csempe korábban csak a Linuxon szokásos 'brave-browser' /
   'brave-browser-stable' / 'brave' parancsneveket próbálta a PATH-on -
   ez WINDOWS-on tipikusan sosem talál rá a Brave-re, mert a telepítője
   nem teszi fel magát a PATH-ra. A keresés most három lépcsős:
     1. PATH-on elérhető parancsnevek (`commands`) - ez működik a legtöbb
        Linux csomagból (apt/deb) telepített Brave-nél, és flatpakos
        telepítésnél is (`flatpak run com.brave.Browser`).
     2. Operációs rendszerenkénti, jól ismert ABSZOLÚT elérési utak
        (`_brave_common_paths()`) - ez fedi le a tipikus Windows-telepítést
        (Program Files / %LOCALAPPDATA%), illetve a Linuxon snap/opt alá
        telepített eseteket.
     3. Ha ezek sem találják meg, a felhasználó saját kezűleg beírhatja a
        pontos elérési útját az `EXTERNAL_APPS["youtube"]["extra_paths"]`
        lista végére - a fájl elején lévő megjegyzés lépésről lépésre
        leírja, hogyan találja meg ezt Windows-on és Linuxon is.
   (A "Telepítés alkalmazásként" / PWA funkció a Brave-ben nem hoz létre
   külön futtatható fájlt - ugyanazt a brave.exe/brave-browser programot
   indítja el speciális argumentumokkal. Ezért elég magát a Brave-et
   megtalálnunk, és `--app=https://www.youtube.com`-mal indítanunk - ez
   ugyanolyan keret nélküli ablakot ad, mint a telepített PWA.)

A v7-ben bevezetett javítások mind érvényben maradtak - lásd alább.

------------------------------------------------------------------
KORÁBBI (v7) JAVÍTÁSOK
------------------------------------------------------------------
1) FUNKCIONÁLIS HIBA - a billentyűzetes navigáció megállt a kategória-
   fejléceken. A `_move_menu_selection()` tévesen `Qt.ItemIsEnabled`-t
   vizsgált `Qt.ItemIsSelectable` helyett - mivel a fejléc-sorok is
   "enabled"-ek (csak nem kiválaszthatók), a kurzor minden fejlécen
   megállt ahelyett, hogy továbbugrott volna. Kategóriánként egyszer,
   egy 9 kategóriás listán gyakorlatilag minden görgetésnél jelentkezett.

2) Induláskori versenyhelyzet (400 ms-os ablak). A lejátszó esemény-
   callbackjei (Playing/Error/Buffering) korábban egy 400 ms-mal
   késleltetett `init_vlc()`-ben kötődtek be - ha a felhasználó ezalatt
   csatornát váltott, a callbackek hiánya miatt a töltés-jelző örökre
   "beragadhatott". A callbackek bekötése most szinkron módon, már a
   konstruktorban megtörténik, a videó-kimenet beágyazása és az első
   lejátszás pedig közvetlenül a `showFullScreen()` után, nem egy
   külön időzítőn keresztül.

3) Nem volt "watchdog" az elakadt (nem válaszoló) adásokhoz. Egy új,
   12 másodperces időzítő minden csatornaváltáskor újraindul; ha ennyi
   időn belül sem "lejátszás elindult", sem "hiba" jelzés nem érkezik a
   lejátszótól, a program magától hibaállapotba vált, hogy a töltés-
   jelző sose maradjon a végtelenségig a képernyőn.

4) Az Esc/Q azonnal, megerősítés nélkül bezárta a teljes alkalmazást.
   Most az első lenyomás egy megerősítő kártyát mutat ("Nyomd meg újra
   a kilépéshez"), és csak a második, néhány másodpercen belüli lenyomás
   zár be ténylegesen.

5) Nem volt beépített billentyű-súgó. A "H" vagy "?" gomb egy automatikusan
   eltűnő (de bármelyik gombra azonnal bezáródó) áttekintést mutat az
   összes elérhető billentyűparancsról.

6) Az egérgörgős hangerő fix ±5%-os lépésközzel dolgozott, ami egy
   érintőpad/nagy felbontású görgő sok apró eseményénél könnyen
   túllőhetett. A lépésköz most a tényleges görgetés-mértékkel arányos
   (max. ±15%/esemény), ami finomabb, "debounce"-szerű vezérlést ad.

7) Apróbb pontosítások: a csatornaszám-beírás mostantól elfogadja a
   vezető nullát is (pl. "01" -> "1" csatorna), és ha a beírt szám
   EGYÉRTELMŰEN egy létező csatornára utal (nincs hosszabb, ugyanezekkel
   a számjegyekkel kezdődő csatornaszám), azonnal vált - nem kell
   végigvárni a 3 másodperces türelmi időt. A korábbi néma
   `except Exception: pass` blokkok most naplóznak (`logging` modul),
   hogy hibakereséskor ne tűnjön el nyomtalanul egy induló hiba. Új:
   egyetlen-példány védelem (`QSharedMemory`) - ha a program véletlenül
   kétszer indulna el, a második példány szépen kilép ahelyett, hogy
   versenyhelyzetben írná felül a beállításfájlt.

A v6-ban bevezetett javítások (lásd alább) mind érvényben maradtak és a
stressz-teszt is helyesnek találta őket (koncentrikus árnyékgyűrűk,
forrásonként független állapot, hangerő-korlátozás, atomikus mentés stb.).

------------------------------------------------------------------
KORÁBBI (v6) JAVÍTÁSOK
------------------------------------------------------------------

JAVÍTOTT HIBÁK
------------------------------------------------------------------
1) "A lekerekítéseknél még mindig sötét folt/négyzet látszik."
   A v5-ös kézzel rajzolt árnyék EGYMÁSRA (nem egymás mellé) rajzolt,
   részben átfedő, félig átlátszó rétegekből állt - ez azt eredményezte,
   hogy a kártya pereme közelében az átfedő rétegek összeadódó alfa-
   értéke egy jól látható, kemény szélű, sötét "gyűrűt" rajzolt ki
   (pont ez látszott a képen). MEGOLDÁS: az árnyék most koncentrikus,
   EGYMÁST NEM ÁTFEDŐ gyűrűkből épül fel (mindegyik gyűrű csak egyszer,
   a saját, önálló, alacsony alfa-értékével fest), így tényleg sima,
   fokozatosan elhalványuló árnyékot ad, nem egy tömör karikát.

2) "Az óra túl nagy és le van vágva alul."
   Az info-kártya korábban túl alacsony volt (88px) ahhoz a betűmérethez
   képest, amit az óra használt - a szöveg emiatt túlnyúlt a kártya
   (és az újonnan bevezetett maszk) szélén, ezért vágódott le. Az óra
   betűmérete csökkent, a kártya pedig magasabb lett, bőséges hellyel.

3) "A forrásváltó (TV/Rádió) ne legyen átlátszó, legyen világoskék
   háttéren, és az opciók egymás mellett legyenek, ne egymás alatt."
   A menü most egy tömör, világoskék kártya, amin a források nagy,
   egymás melletti "csempékként" jelennek meg (nem lista), bal-jobb
   nyilakkal választhatók.

4) "A csatornamenü kijelölése eltorzul görgetés után, majd újranyitáskor
   furcsa helyen jelenik meg."
   Ez a Qt beépített `QListWidget::item:selected` stílusának egy ismert
   hibája volt: egyedi méretű sorokkal (fejléc vs. csatorna) és egyedi
   item-widgetekkel kombinálva a beépített kijelölő téglalap görgetés
   közben "elszakadhat" a valós sortól. MEGOLDÁS: a Qt beépített
   kijelölés-rajzolását teljesen kikapcsoltam, és a kiemelést maga a
   csatorna-sor widget rajzolja meg saját magának (mindig pontosan ott,
   ahol ténylegesen van) - ez a hibaosztály strukturálisan megszűnik.

5) "A menü és minden widget legyen szebb, modernebb, a betűtípus csúnya,
   a háttér túl egyszerű - és legyen felkészítve arra, hogy idővel a
   felhasználó több kinézet közül választhasson."
   - Bővebb, modernebb betűtípus-lista (Inter / Poppins / Roboto / Noto
     Sans / Ubuntu / ... - amelyik éppen elérhető a gépen).
   - A kártyák finom színátmenetes szegélyt is kaptak a lapos szín
     helyett, a kategória-fejlécek "chip" stílusú, halvány jelvényt
     kaptak, a menü fejlécében pedig egy kis ikon-jelvény jelzi az
     aktív forrást (TV/Rádió).
   - ÚJ: a színvilág mostantól egy `THEMES` regiszterből jön (lásd
     lejjebb). Jelenleg két teljes, kész téma van megadva ("Midnight
     Blue" - az alapértelmezett, és "Aurora Amber" - egy meleg
     alternatíva); az aktív témát az `ACTIVE_THEME_KEY` konstans
     választja ki. Ez az architektúra van felkészítve arra, hogy a
     jövőben egy beállítás-menüben a felhasználó válthasson köztük -
     ehhez csak egy UI-t kell majd rákötni erre a már kész rendszerre.
"""

import os
import sys
import json
import glob
import shutil
import logging
import tempfile
import subprocess
from types import SimpleNamespace
from datetime import datetime

import vlc

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QProgressBar, QAbstractItemView, QShortcut,
)
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QRectF, QSize,
    QObject, pyqtSignal, pyqtProperty, QSharedMemory, QUrl, QEvent,
)
from PyQt5.QtGui import (
    QColor, QFont, QPainter, QPen, QBrush, QPainterPath, QRegion, QLinearGradient,
    QKeySequence,
)

# A beépített, teljes képernyős YouTube-nézet a QtWebEngine (Chromium-alapú,
# Qt-be épített böngésző-motor) modult igényli - ez NEM települ a sima
# PyQt5-tel, külön csomag kell hozzá:
#   Windows / Linux (x86_64):  pip install PyQtWebEngine
#   Raspberry Pi / ARM Linux:  sudo apt install python3-pyqt5.qtwebengine
#     (ARM-re nincs kész pip-csomag, forrásból fordítani nagyon nehézkes -
#      ezért ott mindenképp az apt-os csomagot használd)
#
# HA NINCS TELEPÍTVE: a program ettől még elindul, csak a YouTube-csempe
# ilyenkor a KORÁBBI, külön Brave-ablakos módra esik vissza (lásd
# EXTERNAL_APPS lejjebb) - tehát semmi nem törik el, csak nem lesz "appon
# belüli" élmény, amíg fel nem teszed a fenti csomagot.
# A WebEngine komponenseket külön importáljuk. Fontos: egyes régebbi
# PyQtWebEngine kiadásokban a QWebEngineScript nem érhető el, miközben
# maga a QWebEngineView és az URL-interceptor tökéletesen működik.
# Egy opcionális komponens hiánya ezért NEM jelentheti azt, hogy az egész
# beépített böngésző "nincs telepítve".
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
    WEBENGINE_AVAILABLE = True
except ImportError:
    QWebEngineView = None
    QWebEngineProfile = None
    QWebEnginePage = None
    WEBENGINE_AVAILABLE = False

try:
    from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
except ImportError:
    QWebEngineUrlRequestInterceptor = None

try:
    from PyQt5.QtWebEngineCore import QWebEngineScript
except ImportError:
    QWebEngineScript = None

# A korábban néma `except Exception: pass` blokkok most ide naplóznak -
# fejlesztői hibakereséskor ez segít kideríteni, ha pl. a VLC-példány
# létrehozása vagy egy platform-specifikus videó-beágyazás meghiúsul,
# anélkül, hogy a felhasználó felé bármilyen technikai hibaüzenetet mutatnánk.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [tvbox] %(levelname)s: %(message)s")
logger = logging.getLogger("tvbox")

if not WEBENGINE_AVAILABLE:
    logger.warning(
        "A QtWebEngine nincs telepítve - a YouTube egyelőre külön Brave-"
        "ablakban fog megnyílni, nem az alkalmazáson belül. Telepítéshez "
        "lásd a fájl elején lévő megjegyzést (pip install PyQtWebEngine, "
        "vagy Raspberry Pi-n: sudo apt install python3-pyqt5.qtwebengine)."
    )


# ===========================================================================
# Beállítások mentése / betöltése
# ===========================================================================
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".tvbox_settings.json")


def load_settings():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.warning("Nem sikerült beolvasni a beállításfájlt (%s): %s", CONFIG_PATH, e)
        return {}


def save_settings(data):
    """Atomikus mentés: előbb egy ideiglenes fájlba írunk, majd átnevezzük,
    hogy egy esetleges leállás ne hagyjon félig megírt beállításfájlt."""
    try:
        folder = os.path.dirname(CONFIG_PATH) or "."
        fd, tmp_path = tempfile.mkstemp(prefix=".tvbox_settings_", dir=folder)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp_path, CONFIG_PATH)
    except Exception as e:
        logger.warning("Nem sikerült elmenteni a beállításokat: %s", e)


# ===========================================================================
# Csatorna- / adólisták
# ===========================================================================
CHANNEL_DATA = [
    ("Közszolgálati", [
        ("M1", "http://88.212.15.19/live/test_m_1_hungary_1200_atk/playlist.m3u8"),
        ("M2 / Petőfi TV", "http://88.212.15.19/live/m2_hun/index.m3u8"),
        ("M5", "http://88.212.15.19/live/test_m_5_hun_atk_1200/playlist.m3u8"),
        ("Duna TV", "http://88.212.15.19/live/duna_hun/index.m3u8"),
        ("Duna World", "http://88.212.15.19/live/duna_world_hun/index.m3u8"),
    ]),
    ("Fő kereskedelmi csatornák", [
        ("RTL", "http://88.212.15.19/live/test_rtl_klub_hungary_1200_atk/playlist.m3u8"),
        ("TV2", "http://88.212.15.19/live/test_tv_2_hungary_1200_atk/playlist.m3u8"),
        ("ATV", "http://88.212.15.19/live/test_atv_hungary_1200_atk/playlist.m3u8"),
        ("Viasat 6", "http://88.212.15.19/live/viasat6/index.m3u8"),
        ("AMC", "http://88.212.15.19/live/amc_hun/index.m3u8"),
        ("Dikh TV", "http://88.212.15.19/live/dikh/index.m3u8"),
        # --- ÚJ (v16): további fő kereskedelmi csatornák ---
        ("Prime", "http://88.212.15.19/live/prime/index.m3u8"),
        ("Super TV2", "http://88.212.15.19/live/test_super_tv2_hungary_1200_atk/playlist.m3u8"),
        ("TV4", "http://88.212.15.19/live/test_tv_4_hun_atk_1200/playlist.m3u8"),
    ]),
    ("Mese / Gyerek", [
        ("ducktv HD", "https://dash3.antik.sk/live/duck_tv/index.m3u8"),
        ("Minimax", "http://88.212.15.19/live/minimax_hun/index.m3u8"),
        ("JimJam", "http://88.212.15.19/live/jim_jam_hun/index.m3u8"),
        ("Nick Jr.", "http://88.212.15.19/live/nick_junior_hun/index.m3u8"),
        ("Nicktoons", "http://88.212.15.19/live/nicktoons_hungary/index.m3u8"),
        ("Nickelodeon", "http://88.212.15.19/live/test_nickelodeon_hu_1200_atk/playlist.m3u8"),
        ("Disney Channel", "http://88.212.15.19/live/disney_channel_hun/index.m3u8"),
        ("TV2 Kids", "http://88.212.15.19/live/tv2_kids/index.m3u8"),
        # --- ÚJ (v16) ---
        ("Kölyökklub", "http://88.212.15.19/live/kolyokklub_atk/index.m3u8"),
    ]),
    ("Film", [
        ("Film+", "http://88.212.15.19/live/film_plus_hun_atk/index.m3u8"),
        ("Mozi+", "http://88.212.15.19/live/mozi_plusz/index.m3u8"),
        ("Film Café", "http://88.212.15.19/live/film_cafe/index.m3u8"),
        ("Film4", "http://88.212.15.19/live/film4_hun/index.m3u8"),
        ("Magyar Mozi TV", "http://88.212.15.19/live/mozi/index.m3u8"),
        ("Moziklub", "http://88.212.15.19/live/moziklub_atk/index.m3u8"),
        ("Moziverzum", "http://88.212.15.19/live/moziverzum/index.m3u8"),
    ]),
    ("Tudomány / Dokumentum / Bűnügyi", [
        ("Crime + Investigation", "http://88.212.15.19/live/test_cai_hevc/playlist.m3u8"),
        ("National Geographic", "http://88.212.15.19/live/ngc_hun/index.m3u8"),
        ("National Geographic Wild", "http://88.212.15.19/live/ngw_hun/index.m3u8"),
        ("Spektrum", "http://88.212.15.19/live/spektrum_hun/index.m3u8"),
        ("Spektrum Home", "http://88.212.15.19/live/spektrum_home_hun/index.m3u8"),
        ("History", "http://88.212.15.19/live/history_hun/index.m3u8"),
        ("BBC Earth Hungary", "http://88.212.15.19/live/bbce_hun/index.m3u8"),
        # --- ÚJ (v16): további dokumentum / valóság ---

        ("Life TV", "http://88.212.15.19/live/lifetv/index.m3u8"),
    ]),
    ("Szórakoztató / Sorozat", [
        ("Viasat 2", "http://88.212.15.19/live/viasat2/index.m3u8"),
        ("Viasat 3", "http://88.212.15.19/live/viasat3/index.m3u8"),
        ("AXN", "http://88.212.15.19/live/axn_hun/index.m3u8"),
        ("TV2 Comedy", "http://88.212.15.19/live/tv2_comedy/index.m3u8"),
        ("FEM3", "http://88.212.15.19/live/test_fem3_atktv/playlist.m3u8"),
        ("RTL Kettő", "http://88.212.15.19/live/test_rtl2_hungary_1200_atk/playlist.m3u8"),
        ("RTL+ / RTL Három", "http://88.212.15.19/live/test_rtl_plus_hungary_1200_atk/playlist.m3u8"),
        ("RTL Otthon", "http://88.212.15.19/live/rtl_otthon_atk/index.m3u8"),
        # --- ÚJ (v16): sorozatcsatornák ---
        ("Izaura TV", "http://88.212.15.19/live/izaura/index.m3u8"),
        ("Sorozat+", "http://88.212.15.19/live/test_sorozat_hungary_1200_atk/playlist.m3u8"),
        ("Sorozatklub", "http://88.212.15.19/live/sorozatklub_atk/index.m3u8"),
        ("Story4", "http://88.212.15.19/live/test_story_4_atk_1200/playlist.m3u8"),
    ]),
    ("Életmód / Gasztro", [
        ("TV Paprika", "http://88.212.15.19/live/parpika_hun/index.m3u8"),
    ]),
    ("Zene", [
        ("Music Box Hits", "http://88.212.15.19/live/mb_hits/index.m3u8"),
        ("Music Box Classic", "http://88.212.15.19/live/mb_classic/index.m3u8"),
        ("Music Box Dance", "http://88.212.15.19/live/mb_dance/index.m3u8"),
        # --- ÚJ (v16) ---
        ("Slager TV", "http://88.212.15.19/live/test_slager_tv_hungary_1200_atk/playlist.m3u8"),
        ("Zenebutik", "http://88.212.15.19/live/zenebutik/index.m3u8"),
        ("Muzsika TV", "http://88.212.15.19/live/test_muzsika_hungary_1200_atk/playlist.m3u8"),
        ("Dance Television", "https://m1b2.worldcast.tv/dancetelevisionone/2/dancetelevisionone.m3u8"),
    ]),
    ("24/7 csatornák", [
        ("Mr. Bean Animation",
         "https://amg00627-amg00627c29-rakuten-it-3989.playouts.now.amagi.tv/playlist/"
         "amg00627-banijayfast-mrbeanitcc-rakutenit/playlist.m3u8"),
        ("Mr. Bean Live Action",
         "https://amg00627-amg00627c40-rakuten-uk-5725.playouts.now.amagi.tv/playlist/"
         "amg00627-banijayfast-mrbeanpopupcc-rakutenuk/playlist.m3u8"),
        ("SpongeBob", "https://jmp2.uk/plu-63f87d057533d80008ab9549.m3u8"),
    ]),
    # --- ÚJ (v16): sport csatornák ---
    ("Sport", [
        ("Sport 1", "http://88.212.15.19/live/sport1_hun/index.m3u8"),
        ("Sport 2", "http://88.212.15.19/live/sport2_hun/index.m3u8"),
        ("Spiler1", "http://88.212.15.19/live/spiler1/index.m3u8"),
        ("Spiler2", "http://88.212.15.19/live/spiler2/index.m3u8"),
    ]),
    # --- ÚJ (v16): egyéb / regionális / külföldi ---
    ("Egyéb / Regionális", [
        ("Ozone TV", "http://88.212.15.19/live/ozone/index.m3u8"),
        ("TV7 Békéscsaba", "https://stream.y5.hu/stream/stream_bekescsaba/stream.m3u8"),
        ("Kanal1 (SK)", "https://dash.antik.sk/live/test_upnetwork/playlist.m3u8"),
        ("NOE TV", "https://n105.quickmedia.tv/noetv/live/noetv/Ifd4_1_4/chunks_dvr_timeshift-0-7200.m3u8"),
        ("TV Barrandov (cseh)", "http://88.212.15.19/live/test_barrandov/playlist.m3u8"),
        # A "fb_premium_hungary" elnevezés a forrás-URL-ből lett kikövetkeztetve,
        # a pontos csatornanevet érdemes ellenőrizni lejátszás közben.
        ("FB Premium (HU)", "http://88.212.15.19/live/fb_premium_hungary/index.m3u8"),
        ("MTV (USA)", "http://23.237.104.106:8080/USA_MTV/index.m3u8"),
        # --- ÚJ (v17): további HU közéleti / helyi TV-k (nem IPTV-szolgáltatói,
        # hanem a saját üzemeltetőik által közvetlenül nyújtott HLS-stream-ek) ---
        ("Balaton TV", "https://stream.iptvservice.eu/hls/balatontv.m3u8"),
    ]),
    ("Szlovák csatornák", [
        ("Markíza KRIMI", "http://88.212.15.19/live/test_markiza_krimi_hevc/playlist.m3u8"),
        ("Markíza KLASIK", "https://cdnsk003.panaccess.com/local/Markiza_Klasik/index.m3u8"),
        ("JOJ", "http://88.212.15.19/live/test_joj_25p/playlist.m3u8"),
        ("JOJ Plus", "http://88.212.15.19/live/test_pluska_25p/playlist.m3u8"),
        ("Doma", "http://88.212.15.19/live/test_doma_hd_hevc/playlist.m3u8"),
        ("Dajto", "http://88.212.15.19/live/test_dajto_25p/playlist.m3u8"),
        # --- ÚJ (v16): további szlovák csatornák (RTVS közszolgálati + kereskedelmi) ---
        ("Jednotka (RTVS)", "http://88.212.15.19/live/test_jednotka_25p/playlist.m3u8"),
        ("Dvojka (RTVS)", "http://88.212.15.19/live/test_dvojka_25p/playlist.m3u8"),
        ("Prima Cool SK", "http://88.212.15.19/live/prima_cool_avc_25p/playlist.m3u8"),
        ("Prima Krimi SK", "http://88.212.15.19/live/prima_krimi_avc_25p/playlist.m3u8"),
    ]),
]

RADIO_DATA = [
    ("Rádióadók", [
        ("Klubrádió", "https://stream.klubradio.hu:8443/bpstream"),
        ("Rádió 1", "https://icast.connectmedia.hu/5201/live.mp3"),
        # --- ÚJ (v16): további magyar rádióadók ---
        ("Retro Rádió", "https://icast.connectmedia.hu/5001/live.mp3"),
        ("Kossuth Rádió", "https://icast.connectmedia.hu/4724/mr1ex.aac"),
        # A lista.txt végén szereplő, névtelen "mr2.mp3" adó azonosítása
        # alapján ez a Petőfi Rádió (MR2) hivatalos adása.
        ("Petőfi Rádió", "https://icast.connectmedia.hu/4738/mr2.mp3"),
        ("MegaDance Rádió", "https://gamershouse.hu:8080/livemega.mp3"),
        ("Oxygen Music Radio", "https://oxygenmusic.hu:8443/oxygenmusic_128"),
        ("Mercy Rádió", "http://stream.mercyradio.eu:80/mercyradio.mp3"),
    ]),
    # --- ÚJ (v17): szlovák rádióadók, kb. 28 db, a legnépszerűbb
    # közszolgálati (RTVS/Rádio a Rozhlas Slovenska) és kereskedelmi
    # adóktól. Forrás: a szlovák rádiók saját (RTVS, Bauer Media, Radio
    # Group stb.) nyilvános icecast/shoutcast stream-ei. ---
    ("🇸🇰 Szlovák rádióadók", [
        ("Rádio Slovensko (RTVS)", "http://live.slovakradio.sk:8000/Slovensko_128.mp3"),
        ("Rádio Devín (RTVS)", "http://live.slovakradio.sk:8000/Devin_256.mp3"),
        ("Rádio_FM (RTVS)", "http://live.slovakradio.sk:8000/FM_128.mp3"),
        ("Rádio Regina Západ (RTVS)", "http://icecast.stv.livebox.sk/regina-ba_128.mp3"),
        ("Rádio Slovakia International", "http://icecast.stv.livebox.sk/rsi_128.mp3"),
        ("Rádio Patria (RTVS)", "http://icecast.stv.livebox.sk/patria_128.mp3"),
        ("Rádio Litera (RTVS)", "http://icecast.stv.livebox.sk/litera_128.mp3"),
        ("Fun Rádio", "http://stream.funradio.sk:8000/fun128.mp3"),
        ("Fun Rádio Dance", "http://stream.funradio.sk:8000/dance128.mp3"),
        ("Fun Rádio 80-90 roky", "http://stream.funradio.sk:8000/80-90-128.mp3"),
        ("Rádio Vlna", "http://stream.radiovlna.sk/vlna-hi.mp3"),
        ("Rádio Lumen", "http://audio.lumen.sk:8000/live128.mp3"),
        ("Rádio Viva Metropol", "http://stream.sepia.sk:8000/viva128.mp3"),
    ]),
]

# Elérhető FORRÁSOK, ebben a sorrendben jelennek meg a "B" menüben.
# Tuple: (mode_key, ikon, megjelenített név, menü-cím, mértékegység-szó, adatok)
# Új forrás (pl. YouTube, böngésző) hozzáadásához csak ide kell egy új sort
# írni - a menü, a számbeírás, a mentés/betöltés mind automatikusan kezeli.
SOURCES = [
    ("tv", "📺", "Televízió", "TV csatornák", "csatorna", CHANNEL_DATA),
    ("radio", "📻", "Rádió", "Rádióadók", "adó", RADIO_DATA),
]

# ===========================================================================
# KÜLSŐ ALKALMAZÁSOK ("csempeként" jelennek meg a TV/Rádió mellett a forrás-
# váltóban, de NEM a beépített VLC-lejátszóval indulnak, hanem egy külön
# folyamatként - pl. a Brave-be telepített YouTube-alkalmazás "app módban").
#
# HOGYAN TALÁLJUK MEG A BRAVE-ET?
# --------------------------------------------------------------------------
# A "Telepítés alkalmazásként" (PWA) funkció a Brave-ben NEM hoz létre egy
# külön "youtube.exe"-t vagy hasonlót - ugyanazt a brave.exe/brave-browser
# programot indítja el, csak titkos, speciális argumentumokkal (egy saját
# profillal és app-azonosítóval), amit egy asztali/Start menü parancsikon
# rejt el. Ezért NEKÜNK is elég magát a Brave-et megtalálnunk, és azt
# `--app=https://www.youtube.com` argumentummal elindítanunk - ez
# UGYANOLYAN keret nélküli, különálló ablakot ad, mint a telepített PWA.
#
# A keresés három lépcsős, sorban próbálkozva:
#   1) `commands`  - ha a program neve elérhető a PATH-on (ez a legtöbb
#      Linux-csomagból telepített Brave-nél eleve igaz).
#   2) `extra_paths` - ha a PATH-on nem található, ezeket a jól ismert,
#      operációs rendszerenként eltérő telepítési helyeket próbáljuk
#      (ez a leggyakoribb eset WINDOWS-on, mert a Brave telepítője nem
#      teszi fel magát a PATH-ra).
#   3) Ha SEMMI sem talál rá, a program egy hibaüzenetet mutat, és ide,
#      az `extra_paths` lista VÉGÉRE kell beírnod a saját, pontos elérési
#      utadat (lásd lejjebb a `_brave_common_paths()` utáni megjegyzést
#      arról, hogyan találod meg Windows-on és Linuxon).
# ===========================================================================
def _brave_common_paths():
    """Gyakori Brave-telepítési helyek operációs rendszerenként. Ezeket
    PRÓBÁLJUK, de nem minden gépen létezik mindegyik - ha egy fájl nem
    létezik, egyszerűen kihagyjuk, nincs vele probléma."""
    if sys.platform == "win32":
        # A Brave telepítője Windows-on NEM teszi fel magát a PATH-ra,
        # ezért itt a három legjellemzőbb telepítési helyet nézzük végig:
        # "gépre" telepítve (Program Files, 64 és 32 bites), illetve a
        # rendszergazda-jogosultság NÉLKÜLI, felhasználói telepítés esetén
        # használt %LOCALAPPDATA% mappát.
        bases = [
            os.environ.get("PROGRAMFILES"),
            os.environ.get("PROGRAMFILES(X86)"),
            os.environ.get("LOCALAPPDATA"),
        ]
        return [
            os.path.join(base, "BraveSoftware", "Brave-Browser", "Application", "brave.exe")
            for base in bases if base
        ]
    # Linuxon a legtöbb telepítési mód (apt, .deb, snap, flatpak-mentes
    # tarball) ezek közül valamelyik útra teszi a végrehajtható fájlt.
    return [
        "/usr/bin/brave-browser",
        "/usr/bin/brave-browser-stable",
        "/usr/bin/brave",
        "/snap/bin/brave",
        "/opt/brave.com/brave/brave",
        os.path.expanduser("~/.local/bin/brave-browser"),
    ]


EXTERNAL_APPS = {
    "youtube": {
        "icon": "▶️",
        "label": "YouTube",
        "description": "",
        # 1. lépés: ezeket a PARANCSNEVEKET próbáljuk a PATH-on (Linuxon
        # ez a leggyakoribb eset - apt/deb-ből telepített Brave-nél a
        # 'brave-browser' parancs simán elérhető bármelyik terminálból).
        # A flatpakos telepítés is ide tartozik: ott a program neve
        # 'flatpak', a Brave-et pedig a 'run com.brave.Browser'
        # argumentumokkal indítjuk el.
        "commands": [
            ["brave-browser"],
            ["brave-browser-stable"],
            ["brave"],
            ["flatpak", "run", "com.brave.Browser"],
        ],
        # 2. lépés: ha a fentiek egyike sem található a PATH-on, ezeket a
        # jól ismert, abszolút elérési útvonalakat próbáljuk (ez tipikusan
        # a WINDOWS-os eset, lásd a _brave_common_paths() fenti magyarázatát).
        #
        # HA A GÉPEDEN EZEK SEM TALÁLJÁK MEG A BRAVE-ET, ide, a lista
        # VÉGÉRE írd be a saját, pontos elérési utadat (nyers r"..." string-
        # ként, hogy a Windows-os backslash-eket ne kelljen escape-elni):
        #
        #   Windows példa:
        #     r"D:\Programok\BraveSoftware\Brave-Browser\Application\brave.exe",
        #   Linux példa:
        #     "/home/pi/.local/share/brave/brave",
        #
        # HOGYAN TALÁLD MEG A SAJÁT ELÉRÉSI UTADAT?
        #   Windows: kattints jobb gombbal a Brave/YouTube parancsikonra
        #     (Start menü vagy asztal) -> "Fájl helyének megnyitása" ->
        #     az így megnyíló mappában lévő parancsikonra ismét jobb
        #     gomb -> Tulajdonságok -> a "Cél" mezőben látod a teljes
        #     elérési utat (az idézőjelek közötti rész, aszóköz UTÁNI
        #     esetleges extra argumentumok nélkül).
        #   Linux: nyiss egy terminált, és írd be: `which brave-browser`
        #     (vagy `whereis brave-browser`) - ez kiírja a pontos utat,
        #     ha egyáltalán telepítve van és a PATH-on elérhető.
        "extra_paths": _brave_common_paths(),
        # --kiosk: valódi, keret NÉLKÜLI teljes képernyő (nincs címsor,
        # nincs cím/eszköztár) - ugyanolyan élményt ad, mint amikor a
        # program maga vált TV és Rádió között. A korábbi
        # "--start-maximized" csak egy normál, kereteres ablakot adott
        # volna maximalizálva, ami nem ugyanaz. Kilépés: Alt+F4 (Windows
        # és a legtöbb Linux ablakkezelő is), ekkor a TV Box automatikusan
        # visszaáll teljes képernyőre - lásd _check_external_processes().
        "args": ["--kiosk", "--app=https://www.youtube.com"],
    },
}

# ===========================================================================
# BEÉPÍTETT ("appon belüli") web-alkalmazások - QtWebEngine-nel jelennek meg,
# UGYANÚGY teljes képernyőn, ahogy a TV/Rádió is, és UGYANÚGY lehet köztük
# váltani a forrásváltó ("B") menüben. Ez az ELSŐDLEGES mód, ha a QtWebEngine
# telepítve van; ha nincs, az adott alkalmazás az EXTERNAL_APPS-beli, külön
# ablakos módra esik vissza (lásd feljebb).
# ===========================================================================
WEB_APPS = {
    "youtube": {
        "icon": "▶️",
        "label": "YouTube",
        "description": "Beépítve, teljes képernyőn",
        # A youtube.com/tv a "Leanback" (Chromecast/okostévé-optimalizált,
        # nyilakkal+Enterrel navigálható) felület - EZ illik egy mini-
        # billentyűzettel vezérelt TV Box-hoz, nem a sima, egérre tervezett
        # youtube.com. A Google viszont csak akkor szolgálja ki ezt a
        # felületet, ha a böngésző egy okostévé/konzol eszköznek adja ki
        # magát - EZÉRT van szükség a lenti user_agent beállításra. Enélkül
        # a youtube.com/tv egyszerűen visszairányítana a sima, asztali
        # oldalra (ami ettől még működik, csak nem D-pad-barát).
        "url": "https://www.youtube.com/tv",
        "user_agent": (
            "Mozilla/5.0 (PlayStation 4 3.11) AppleWebKit/537.73 "
            "(KHTML, like Gecko) Version/8.0 Safari/537.73"
        ),
    },
}
# Csak akkor jelenik meg "appon belüli" csempeként, ha a QtWebEngine
# ténylegesen telepítve van - egyébként a lenti EXTERNAL_ORDER veszi át
# a helyét (külön Brave-ablakos mód).
# A beépített QtWebEngine és a libVLC natív videófelülete ugyanazon
# top-level ablakban natív GPU-kompozitort használ. A felhasználó gépén ez
# ismételt crash-t okozott, ezért a YouTube-ot stabilitás miatt KIZÁRÓLAG
# külön Brave kiosk-ablakban futtatjuk. A VLC TV-kép útvonala ettől teljesen
# érintetlen marad.
WEB_APP_ORDER = []

# Ebben a sorrendben jelennek meg a forrásváltóban a beépített (VLC-s)
# források UTÁN. Egy alkalmazás SOSEM jelenik meg egyszerre mindkét
# listában - ha a WEB_APP_ORDER (appon belüli) már lefedi, itt kimarad.
EXTERNAL_ORDER = [key for key in EXTERNAL_APPS if key not in WEB_APP_ORDER]


def _resolve_app_command(app):
    """Megkeresi az első elérhető parancsot egy külső alkalmazáshoz, a
    fájl elején lévő 1-2. lépés sorrendjében. Visszaadja a teljes argv-
    listát (a program + az esetleges extra argumentumok, pl. flatpaknál
    'run', 'com.brave.Browser'), vagy None-t, ha semmi nem található."""
    for command in app.get("commands", []):
        program = command[0]
        found = shutil.which(program)
        if found:
            return [found] + list(command[1:])

    for path in app.get("extra_paths", []):
        if path and os.path.isfile(path):
            return [path]

    return None


# ===========================================================================
# BEÁLLÍTÁSOK SÉMA
#
# A forrásváltó ("B") menüben elérhető, külön elválasztott "Beállítások"
# menüpont innen épül fel. Minden sor egy önálló, Balra/Jobbra nyíllal
# (vagy Enterrel) léptethető opció - lásd SettingsRowWidget / SettingsPanel.
# `kind`:
#   "choice"     - `options` listából választ, `labels` a megjelenő szöveg
#   "bool"       - Be/Ki kapcsoló (két "choice" opció "Be"/"Ki" címkével)
#   "brightness" - kijelző-fényerő, `options` egész % értékek listája
#   "theme"      - `options` a THEMES kulcsai, `labels` a téma neve
# ===========================================================================
SETTINGS_SCHEMA = [
    {
        "key": "brightness", "label": "Fényerő", "kind": "brightness",
        "options": [20, 30, 40, 50, 60, 70, 80, 90, 100],
        "labels": ["20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%"],
        "default": 100,
    },
    {
        "key": "theme", "label": "Téma", "kind": "theme",
        "options": ["midnight", "aurora"],
        "labels": ["Midnight Blue", "Aurora Amber"],
        "default": "midnight",
    },
    {
        "key": "confirm_exit", "label": "Kilépés megerősítése", "kind": "bool",
        "options": [True, False], "labels": ["Be", "Ki"], "default": True,
    },
    {
        "key": "menu_autoclose_ms", "label": "Menü automatikus bezárása", "kind": "choice",
        "options": [3000, 6000, 10000, None],
        "labels": ["3 mp", "6 mp", "10 mp", "Soha"], "default": 6000,
    },
    {
        "key": "animations", "label": "Animációk", "kind": "bool",
        "options": [True, False], "labels": ["Be", "Ki"], "default": True,
    },
    {
        "key": "digit_timeout_ms", "label": "Számbeírás türelmi ideje", "kind": "choice",
        "options": [2000, 3000, 5000],
        "labels": ["2 mp", "3 mp", "5 mp"], "default": 3000,
    },
    {
        "key": "info_card_ms", "label": "Info kártya ideje", "kind": "choice",
        "options": [3000, 5000, 8000, None],
        "labels": ["3 mp", "5 mp", "8 mp", "Mindig látszik"], "default": 5000,
    },
    {
        "key": "youtube_adblock", "label": "YouTube reklámblokkoló", "kind": "bool",
        "options": [True, False], "labels": ["Be", "Ki"], "default": False,
    },
]

# Azon kijelző-háttérvilágítás sysfs-mappáinak keresési mintája, amikre a
# "Fényerő" beállítás írni próbál. Raspberry Pi-n hivatalos érintő-kijelzőnél
# (pl. `rpi_backlight`) ez általában létezik; egy sima HDMI-monitornál
# tipikusan NINCS szoftveresen vezérelhető háttérvilágítás - ilyenkor a
# beállítás a kártyán megjelenik, de csendben hatástalan marad (naplózott
# figyelmeztetéssel), nem okoz hibát.
BACKLIGHT_GLOB = "/sys/class/backlight/*/"


def _build_source_state(data):
    """Egy forrás (pl. CHANNEL_DATA) kategóriákra bontott, sorszámozott
    csatorna-állapotát építi fel."""
    channels = {}
    categories = []
    counter = 1
    for category_name, entries in data:
        keys = []
        for name, url in entries:
            key = str(counter)
            channels[key] = (name, url)
            keys.append(key)
            counter += 1
        categories.append((category_name, keys))
    return {"channels": channels, "categories": categories, "keys": list(channels.keys())}


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
        self._bg = QColor(bg) if bg is not None else QColor(THEME.SOLID_BG)
        self._border = QColor(border) if border is not None else QColor(THEME.SOLID_BORDER)
        self._shadow = shadow
        self._margin = margin
        self._glass = glass
        self._opacity = 1.0

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
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setOpacity(self._opacity)

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
        painter.fillPath(path, THEME.ACCENT)


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
        self._angle = (self._angle + 6) % 360
        self.update()

    def showEvent(self, event):
        self._timer.start(16)
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

        pen = QPen(THEME.ACCENT)
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
            color = QColor(THEME.ACCENT) if i % 2 == 0 else QColor(THEME.ACCENT_2)
            painter.fillPath(path, color)


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

        self.name_label = _label(name, size=14, weight=QFont.Medium,
                                  color=THEME.TEXT_DIM, wrap=True)
        layout.addWidget(self.name_label, 1)

        self.set_current(is_current)

    def set_current(self, is_current):
        """A csatorna 'ez van most lejátszva' kiemelését frissíti ANÉLKÜL,
        hogy a widgetet újra kellene építeni - ez teszi lehetővé, hogy
        csatornaváltáskor csak KÉT sort (a régi és az új aktívat) kelljen
        módosítani a listában, ne az egészet (lásd a teljesítmény-
        megjegyzést a _refresh_menu_items()-nél)."""
        self._is_current = is_current
        self.stripe.setVisible(is_current)
        bg_color = QColor(THEME.ACCENT) if is_current else QColor(255, 255, 255, 26)
        fg_color = QColor("#000000") if is_current else QColor("#FFFFFF")
        self.badge.setColors(bg_color, fg_color)
        self.name_label.setFont(_font(14, QFont.DemiBold if is_current else QFont.Medium))
        self.name_label.setStyleSheet(
            "color: %s; background: transparent;" % ("#FFFFFF" if is_current else THEME.TEXT_DIM)
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
                color = QColor(THEME.ACCENT.red(), THEME.ACCENT.green(), THEME.ACCENT.blue(), 48)
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
                THEME.ACCENT.name(), THEME.ACCENT.red(), THEME.ACCENT.green(), THEME.ACCENT.blue(),
            )
        )
        layout.addWidget(pill)
        layout.addStretch()


class SettingsRowWidget(QWidget):
    """Egy sor a Beállítások panelen: bal oldalt a beállítás neve, jobb
    oldalt az aktuális érték egy jelvényben. Fel/le mozgás a sorok között,
    balra/jobbra (vagy Enter) az érték léptetéséhez - ugyanaz a mintázat,
    mint a csatornalistánál (fókusz-kiemelést maga a widget rajzolja)."""

    def __init__(self, label, value_text, parent=None):
        super().__init__(parent)
        set_translucent(self)
        self._focused = False
        self.setFixedHeight(46)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        self.name_label = _label(label, size=14, weight=QFont.Medium, color=THEME.TEXT)
        layout.addWidget(self.name_label, 1)

        self.value_badge = TintedLabel(
            value_text, bg_color=QColor(THEME.ACCENT.red(), THEME.ACCENT.green(),
                                         THEME.ACCENT.blue(), 60),
            text_color=QColor(THEME.TEXT), font=_font(12, QFont.Bold),
            padding=(12, 5),
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
            color = QColor(THEME.ACCENT.red(), THEME.ACCENT.green(), THEME.ACCENT.blue(), 44)
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
                THEME.MODE_TILE_SELECTED_BG, THEME.MODE_TILE_SELECTED_BG,
                THEME.MODE_TILE_SELECTED_TEXT, THEME.MODE_TILE_SELECTED_TEXT,
            )
        else:
            bg, border, text_color, desc_color = (
                THEME.MODE_TILE_BG, THEME.MODE_TILE_BORDER,
                THEME.MODE_TILE_TEXT, THEME.MODE_TILE_DESC,
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
                THEME.MODE_TILE_SELECTED_BG, THEME.MODE_TILE_SELECTED_BG,
                THEME.MODE_TILE_SELECTED_TEXT,
            )
        else:
            bg, border, text_color = (
                "transparent", THEME.MODE_TILE_BORDER, THEME.MODE_TILE_TEXT,
            )
        self.setStyleSheet(
            "PillButton { background-color: %s; border: 2px solid %s; border-radius: 28px; }"
            % (bg, border)
        )
        self.name_label.setStyleSheet("color: %s; background: transparent;" % text_color)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# ===========================================================================
# libVLC eseményeket biztonságosan a Qt GUI-szálra továbbító jelzések
# ===========================================================================
class PlayerSignals(QObject):
    playing = pyqtSignal()
    error = pyqtSignal()
    buffering = pyqtSignal(float)


# ===========================================================================
# YouTube reklám- és követésblokkoló a beépített QtWebEngine-hez
#
# Ez nem a Brave Shields teljes klónja. A QtWebEngine URL-szinten tud
# kéréseket blokkolni, ezért biztosan reklámhoz/követéshez tartozó domaineket
# és ismert YouTube reklám-végpontokat tiltunk, majd JS-sel eltüntetjük a
# reklám UI-elemeket. A YouTube időről időre változtat, ezért 100%-os,
# örökös garancia nem adható.
#
# FONTOS, FELHASZNÁLÓ ÁLTAL JELENTETT PROBLÉMA MIATTI VÁLTOZÁS: amikor egy
# videóreklám következett volna, a fenti végpontok BLOKKOLÁSA miatt a
# YouTube lejátszója egy ideig SÖTÉT/BERAGADT képernyőt mutatott, mielőtt
# felismerte a hibát és továbblépett a tényleges tartalomra - vagyis a
# reklámblokkoló ebben a konkrét, Leanback/TV-felületen ROSSZABB, zavaróbb
# felhasználói élményt adott, mint maga a reklám. EZÉRT ez a funkció
# alapértelmezetten KI van kapcsolva (lásd SETTINGS_SCHEMA fent,
# "youtube_adblock": default False) - a Beállítások menüben bármikor
# visszakapcsolható, de ott a fenti sötét-képernyős mellékhatással kell
# számolni.
# ===========================================================================
if QWebEngineUrlRequestInterceptor is not None:
    class YouTubeAdBlockInterceptor(QWebEngineUrlRequestInterceptor):
        BLOCKED_HOSTS = {
            # Klasszikus Google/YouTube hirdetési infrastruktúra.
            "doubleclick.net",
            "googlesyndication.com",
            "googleadservices.com",
            "adservice.google.com",
            "pagead2.googlesyndication.com",
            "ads.youtube.com",
            "ads.google.com",
            "googleads.g.doubleclick.net",
            "securepubads.g.doubleclick.net",
            "tpc.googlesyndication.com",
            "pagead2.googleadservices.com",
        }

        BLOCKED_URL_PARTS = (
            "/pagead/",
            "/api/stats/ads",
            "/ptracking",
            "googleads.g.doubleclick.net",
            "doubleclick.net/pagead",
            "googlesyndication.com/pagead",
        )

        def __init__(self, parent=None):
            super().__init__(parent)
            self.enabled = True

        def set_enabled(self, enabled):
            self.enabled = bool(enabled)

        def interceptRequest(self, info):
            if not self.enabled:
                return
            try:
                url = info.requestUrl().toString()
                host = info.requestUrl().host().lower().rstrip(".")
                if any(host == h or host.endswith("." + h) for h in self.BLOCKED_HOSTS):
                    info.block(True)
                    return
                lower_url = url.lower()
                if any(part in lower_url for part in self.BLOCKED_URL_PARTS):
                    info.block(True)
            except Exception:
                return
else:
    YouTubeAdBlockInterceptor = None


YOUTUBE_ADBLOCK_JS = r"""
(function() {
    const STYLE_ID = 'tvbox-adblock-style';
    const HIDDEN_ATTR = 'data-tvbox-ad-hidden';
    const PLAYER_GUARD_STYLE_ID = 'tvbox-adblock-player-guard';

    // Ezek kifejezetten YouTube-reklám elemek. Nem használunk általános
    // "class contains ad" szabályt, mert az könnyen valódi videó/UI elemeket
    // is elrejthetne.
    const selectors = [
        '#masthead-ad',
        '#player-ads',
        'ytd-display-ad-renderer',
        'ytd-promoted-sparkles-web-renderer',
        'ytd-ad-slot-renderer',
        'ytd-in-feed-ad-layout-renderer',
        'ytd-banner-promo-renderer',
        'ytd-statement-banner-renderer',
        'ytm-promoted-sparkles-web-renderer',
        'ytd-action-companion-ad-renderer',
        '.ytp-ad-overlay-container',
        '.ytp-ad-text-overlay',
        '.ytp-ad-message-container',
        '.ytp-ad-player-overlay',
        '.ytp-ad-skip-button',
        '.ytp-ad-preview-container',
        '.ytp-ad-image-overlay',
        '.ytp-ad-action-interstitial',
        '.ytp-ad-skip-button-modern',
        '.ytp-ad-skip-button-slot',
        '.video-ads'
    ];

    // A CSS azonnal, már a dokumentum létrehozásakor bekerül. Ez sokkal
    // kevésbé engedi, hogy a reklám egyetlen pillanatra felvillanjon.
    function installStyle() {
        if (document.getElementById(STYLE_ID)) return;
        const style = document.createElement('style');
        style.id = STYLE_ID;
        style.textContent = selectors.map(s =>
            s + ' { display:none !important; visibility:hidden !important; opacity:0 !important; }'
        ).join('\n');
        (document.head || document.documentElement).appendChild(style);

        // A reklám első képkockáját se engedjük kirajzolódni. Amíg a YouTube
        // "ad-showing/ad-interrupting" állapotban van, a lejátszó fekete.
        // Ez jobb UX, mint egy 100-300 ms-os reklámvillanás.
        const guard = document.createElement('style');
        guard.id = PLAYER_GUARD_STYLE_ID;
        guard.textContent = `
            #movie_player.ad-showing video,
            #movie_player.ad-interrupting video,
            .html5-video-player.ad-showing video,
            .html5-video-player.ad-interrupting video {
                visibility: hidden !important;
                opacity: 0 !important;
            }
            #movie_player.ad-showing .html5-video-container,
            #movie_player.ad-interrupting .html5-video-container {
                background: #000 !important;
            }
        `;
        (document.head || document.documentElement).appendChild(guard);
    }

    function hideAdNode(el) {
        if (!el || el.nodeType !== 1) return;

        // Elsőként magát a reklámot rejtjük el.
        el.style.setProperty('display', 'none', 'important');
        el.style.setProperty('visibility', 'hidden', 'important');
        el.style.setProperty('opacity', '0', 'important');
        el.setAttribute(HIDDEN_ATTR, '1');

        // A főoldali rácsban a reklám gyakran egy "rich item" belsejében van.
        // A teljes kártyát is elrejtjük, így nem marad lyuk a rácsban.
        const item = el.closest && el.closest(
            'ytd-rich-item-renderer, ytd-grid-video-renderer, ytd-video-renderer'
        );
        if (item) {
            item.style.setProperty('display', 'none', 'important');
            item.setAttribute(HIDDEN_ATTR, '1');
        }

        // In-feed hirdetésnél a teljes ad-layout konténert is eltüntetjük.
        const layout = el.closest && el.closest(
            'ytd-in-feed-ad-layout-renderer, ytd-ad-slot-renderer'
        );
        if (layout) {
            layout.style.setProperty('display', 'none', 'important');
            layout.setAttribute(HIDDEN_ATTR, '1');
        }
    }

    function removeEmptyAdContainers() {
        // Ha egy teljes rich-grid-row csak reklámkártyákból/üres helyekből áll,
        // az egész sort elrejtjük. Így nem marad üres sor a kezdőlapon.
        document.querySelectorAll('ytd-rich-grid-row').forEach(row => {
            const items = Array.from(row.querySelectorAll(':scope > #contents > ytd-rich-item-renderer'));
            if (!items.length) return;
            const visible = items.filter(item => {
                const st = window.getComputedStyle(item);
                return st.display !== 'none' && item.getAttribute(HIDDEN_ATTR) !== '1';
            });
            if (visible.length === 0) {
                row.style.setProperty('display', 'none', 'important');
                row.setAttribute(HIDDEN_ATTR, '1');
            }
        });
    }

    function cleanAds() {
        installStyle();

        for (const selector of selectors) {
            document.querySelectorAll(selector).forEach(hideAdNode);
        }

        // A YouTube SPA újrarenderelheti az oldalt és újra létrehozhatja a
        // reklámkártyát, ezért a gombot mindig megkeressük.
        document.querySelectorAll(
            '.ytp-ad-skip-button, .ytp-ad-skip-button-modern, .ytp-ad-skip-button-slot'
        ).forEach(btn => {
            try { btn.click(); } catch (e) {}
        });

        // Ha mégis elindul egy reklámvideó, azonnal a végére ugrunk, amikor a
        // YouTube már megadta a tényleges duration értéket.
        const video = document.querySelector('video');
        const adShowing = document.querySelector('.ad-showing, .ad-interrupting');
        if (video && adShowing) {
            try {
                // Némítsük el az esetlegesen már elindult reklámot, majd
                // amint a duration ismert, azonnal ugorjunk a végére.
                video.muted = true;
                const duration = Number(video.duration);
                if (Number.isFinite(duration) && duration > 0) {
                    video.currentTime = Math.max(0, duration - 0.05);
                    try { video.play(); } catch (e) {}
                }
            } catch (e) {}
        }

        removeEmptyAdContainers();
    }

    installStyle();
    cleanAds();

    // A YouTube egy SPA: navigációkor nincs teljes oldalbetöltés, csak DOM-
    // változás. Ezért MutationObserver figyeli a frissen létrejövő elemeket.
    if (!window.__tvboxAdBlockObserver) {
        window.__tvboxAdBlockObserver = new MutationObserver(function() {
            if (window.__tvboxAdBlockSweep) return;
            window.__tvboxAdBlockSweep = true;
            requestAnimationFrame(function() {
                window.__tvboxAdBlockSweep = false;
                cleanAds();
            });
        });
        window.__tvboxAdBlockObserver.observe(document.documentElement, {
            subtree: true,
            childList: true
        });
    }

    if (!window.__tvboxAdBlockInterval) {
        // 700 ms túl lassú: ennyi idő alatt egy reklám már látható lehet.
        // 120 ms gyors sweep + MutationObserver adja a két védelmi réteget.
        window.__tvboxAdBlockInterval = setInterval(cleanAds, 120);
    }
})();
"""

# ===========================================================================
# Fő ablak
# ===========================================================================
def _prepare_webengine_storage_dir():
    """A beépített böngésző-nézet (pl. YouTube) SAJÁT, ehhez az
    alkalmazáshoz kötött tárolási mappáját készíti elő - lásd a
    _build_web_view()-nél lévő bővebb magyarázatot arról, miért NEM a
    QtWebEngine implicit "alapértelmezett" profilját használjuk.

    Rendellenes leállás után (összeomlás, kényszerített bezárás, áram-
    kimaradás egy Raspberry Pi-n) a Chromium néha "beragadt" zároló-
    fájlokat hagyhat ebben a mappában, amik a KÖVETKEZŐ indításkor
    megakadályozzák a profil rendes megnyitását - ez a legvalószínűbb
    magyarázat arra, hogy a beépített YouTube-nézet néha összeomlott, ha
    korábban már egyszer megnyitották, majd a programot újraindították
    ("crash után ismét jól megy néha" - pont ez a fajta, zároló-fájltól
    függő, nem-determinisztikus viselkedés jellemző rá). Ezért induláskor
    itt előre eltávolítjuk a jól ismert zároló-fájlokat, MIELŐTT a profil
    egyáltalán létrejönne."""
    storage_dir = os.path.join(os.path.expanduser("~"), ".tvbox", "webengine_profile")
    try:
        os.makedirs(storage_dir, exist_ok=True)
        for lock_name in ("SingletonLock", "SingletonCookie", "SingletonSocket", "lockfile"):
            lock_path = os.path.join(storage_dir, lock_name)
            try:
                if os.path.lexists(lock_path):
                    os.remove(lock_path)
            except OSError as e:
                logger.debug("Nem sikerült eltávolítani a zároló-fájlt (%s): %s", lock_path, e)
    except OSError as e:
        logger.warning("Nem sikerült előkészíteni a webnézet tárolási mappáját: %s", e)
        return None
    return storage_dir


class TVBox(QMainWindow):

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
        vlc_args = ["--quiet", "--no-video-title-show", "--network-caching=1200"]
        try:
            self.instance = vlc.Instance(vlc_args)
        except Exception as e:
            logger.warning("Nem sikerült a megadott VLC beállításokkal indítani, alapértelmezettel próbálkozom: %s", e)
            self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # A libVLC event_attach callbackjei NEM a Qt GUI-szálon futnak -
        # csak Qt jelet küldünk, a tényleges UI-módosítás a GUI-szálon történik.
        self.player_signals = PlayerSignals()
        self.player_signals.playing.connect(self._on_stream_playing)
        self.player_signals.error.connect(self._on_stream_error)
        self.player_signals.buffering.connect(self._on_stream_buffering)

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
        self.external_watch_timer.start(1000)

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
        if WEBENGINE_AVAILABLE:
            QTimer.singleShot(1800, self._prewarm_web_engine)

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
            "1", bg_color=QColor(THEME.ACCENT), text_color=QColor("#000000"),
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
        self.date_label = _label("", size=10, weight=QFont.Medium, color=THEME.TEXT_DIM,
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
            bg=THEME.MENU_BG, border=THEME.MENU_BORDER, glass=True,
        )
        layout = panel.contentLayout()
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        self.menu_icon_label = TintedLabel(
            "📺", bg_color=QColor(THEME.ACCENT.red(), THEME.ACCENT.green(), THEME.ACCENT.blue(), 42),
            text_color=QColor("#FFFFFF"), font=_font(15), fixed_size=(34, 34),
        )
        header_row.addWidget(self.menu_icon_label)

        self.menu_title_label = _label("Csatornák", size=18, weight=QFont.Bold, color="#FFFFFF")
        header_row.addWidget(self.menu_title_label)
        header_row.addStretch()
        self.menu_count_label = _label("", size=12, weight=QFont.Medium, color=THEME.TEXT_FAINT)
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
                       size=10, weight=QFont.Medium, color=THEME.TEXT_FAINT)
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
            bg=THEME.MODE_PANEL_BG, border=THEME.MODE_PANEL_BORDER, glass=False,
        )
        layout = panel.contentLayout()
        layout.setSpacing(14)

        title = _label("Forrás váltása", size=18, weight=QFont.Bold, color=THEME.MODE_TILE_TEXT)
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
                       size=10, weight=QFont.Medium, color=THEME.MODE_TILE_DESC)
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
            bg=THEME.MENU_BG, border=THEME.MENU_BORDER, glass=True,
        )
        layout = panel.contentLayout()
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        icon = TintedLabel(
            "⚙️", bg_color=QColor(THEME.ACCENT.red(), THEME.ACCENT.green(), THEME.ACCENT.blue(), 42),
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
            size=10, weight=QFont.Medium, color=THEME.TEXT_FAINT,
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
                                   color=THEME.TEXT_DIM, align=Qt.AlignCenter)
        layout.addWidget(self.number_hint)
        panel.setFixedSize(180, 110)
        panel.hide()
        self.number_osd = panel

    def _build_volume_osd(self):
        panel = GlassPanel(self.central, radius=20, margin=14, glass=True)
        layout = panel.contentLayout()
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        self.volume_caption = _label("Hangerő", size=13, weight=QFont.DemiBold, color="#FFFFFF")
        self.volume_value = _label("80%", size=13, weight=QFont.DemiBold, color=THEME.TEXT_DIM,
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
        self.volume_bar.setStyleSheet(VOLUME_BAR_STYLE)
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
            bg=THEME.ERROR_BG, border=THEME.ERROR_BORDER,
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
                       size=11, weight=QFont.Medium, color=THEME.TEXT_DIM,
                       align=Qt.AlignCenter, wrap=True)
        layout.addWidget(hint)

        panel.setFixedSize(360, 110)
        panel.hide()
        self.exit_confirm_card = panel

    def _build_help_card(self):
        panel = GlassPanel(
            self.central, radius=28, margin=20,
            bg=THEME.MENU_BG, border=THEME.MENU_BORDER, glass=True,
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
            ("← / →", "Előző / következő csatorna"),
            ("↑ / ↓", "Hangerő fel / le"),
            ("0-9", "Csatornaszám beírása"),
            ("Enter", "Kiválasztás / megerősítés"),
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
            desc_label = _label(desc, size=12, weight=QFont.Medium, color=THEME.TEXT_DIM, wrap=True)
            row.addWidget(desc_label, 1)
            layout.addLayout(row)

        hint = _label("Bármelyik gomb becsukja ezt az ablakot", size=10,
                       weight=QFont.Medium, color=THEME.TEXT_FAINT, align=Qt.AlignCenter)
        layout.addWidget(hint)

        # Bőkezű magasság, hogy a 10 billentyű-sor semmiképp se lógjon bele
        # a lekerekített sarok-maszkba (lásd a GlassPanel elején lévő
        # magyarázatot arról, hogy a tartalom sosem nyúlhat a maszkon túlra).
        panel.setFixedSize(380, 600)
        panel.hide()
        self.help_card = panel

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

    def play_channel(self, key):
        if key not in self.channels:
            return

        # Ha épp egy beépített webnézet (pl. YouTube) volt aktív, most
        # eltüntetjük, mielőtt a videó/rádió újra megjelenne.
        self._leave_web_app_if_active()

        if key != self.current_key:
            self.previous_key = self.current_key
        self.current_key = key
        name, url = self.channels[key]

        self._hide_widget(self.error_card)
        self.loading_caption.setText("Csatlakozás a csatornához...")
        self._show_widget(self.loading_card)
        # "Watchdog": ha ennyi időn belül nem érkezik sem "lejátszás elindult",
        # sem "hiba" jelzés a lejátszótól (pl. mert az URL egyszerűen nem
        # válaszol - holt szerver, DNS-timeout, tűzfal), automatikusan
        # hibaállapotba kapcsolunk, hogy a töltés-jelző sose ragadjon be
        # a végtelenségig. Minden play_channel()-hívás újraindítja.
        self.watchdog_timer.start(12000)

        try:
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()
        except Exception as e:
            logger.warning("Nem sikerült elindítani a lejátszást (%s): %s", url, e)
            self._on_stream_error()
            return

        self.channel_badge.setText(key)
        self.channel_name_label.setText(name)
        self.update_time()

        if self.mode == "radio":
            self.radio_station_label.setText(name)
            self._show_widget(self.radio_visualizer)
        else:
            self._hide_widget(self.radio_visualizer)

        self._show_widget(self.info_card)
        info_ms = self.settings_data.get("info_card_ms", 4500)
        self.hide_timer.stop()
        if info_ms:  # None = "Mindig látszik" -> nincs automatikus elrejtés
            self.hide_timer.start(info_ms)

        self._refresh_menu_items()
        self.close_menu()
        self.save_timer.start(400)

    def _play_previous(self):
        if self.previous_key:
            self.play_channel(self.previous_key)

    def _retry_current_channel(self):
        if self.current_key:
            self.play_channel(self.current_key)

    def _on_stream_playing(self):
        self.watchdog_timer.stop()
        self._hide_widget(self.loading_card)

    def _on_stream_error(self):
        self.watchdog_timer.stop()
        self._hide_widget(self.loading_card)
        self.error_card_label.setText("⚠  Nem sikerült elérni a csatornát")
        self._show_widget(self.error_card)

    def _on_stream_buffering(self, percent):
        try:
            pct = int(percent)
        except (TypeError, ValueError):
            pct = 100

        # A libVLC élő adásoknál menet közben is küldhet Buffering eseményt,
        # de a "Playing" esemény ilyenkor nem tűzik újra - ezért ITT, a 100%-os
        # állapotnál kell elrejteni a kártyát, nem szabad megvárni a Playing-et.
        if pct >= 100:
            self.watchdog_timer.stop()
            self._hide_widget(self.loading_card)
            return

        self.loading_caption.setText("Pufferelés... %d%%" % pct)
        if not self.loading_card.isVisible():
            self._show_widget(self.loading_card)

    def _on_watchdog_timeout(self):
        """Ha ennyi idő alatt sem "lejátszás elindult", sem "hiba" jelzés nem
        érkezett a lejátszótól, feltételezzük, hogy az adás nem válaszol, és
        magunktól hibaállapotba váltunk - lásd a play_channel()-nél lévő
        magyarázatot."""
        if self.loading_card.isVisible():
            logger.warning("Watchdog időtúllépés - a csatorna (%s) nem válaszolt időben.", self.current_key)
            self._on_stream_error()

    # ------------------------------------------------------------------
    # Hangerő
    # ------------------------------------------------------------------
    def _change_volume(self, delta):
        self.muted = False
        self.player.audio_set_mute(False)
        self.volume = max(0, min(100, self.volume + delta))
        self.player.audio_set_volume(self.volume)
        self._show_volume_osd()
        self.save_timer.start(400)

    def _toggle_mute(self):
        self.muted = not self.muted
        self.player.audio_set_mute(self.muted)
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
        for i in range(self.menu.count()):
            item = self.menu.item(i)
            widget = self.menu.itemWidget(item)
            if isinstance(widget, ChannelItemWidget):
                widget.set_focused(i == row)

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

    def open_menu(self):
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
            anim.finished.connect(self.menu_panel.hide)
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
        idx = self.channel_keys.index(self.current_key)
        new_idx = (idx + direction) % len(self.channel_keys)
        self.play_channel(self.channel_keys[new_idx])

    # ------------------------------------------------------------------
    # Forrásváltó menü ("B" billentyű: TV / Rádió / YouTube / Beállítások)
    # ------------------------------------------------------------------
    def _on_mode_tile_clicked(self, mode_key):
        self.close_mode_menu()
        if mode_key in WEB_APPS:
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
            if tile.mode_key in WEB_APPS:
                # A natív VLC felület és a QtWebEngine ugyanazon top-level
                # ablakban időzítésérzékeny lehet. Enter eseményből ne
                # közvetlenül indítsuk a Chromium nézetet.
                self.setFocus()
                QTimer.singleShot(150, lambda k=tile.mode_key: self._show_web_app(k))
            elif tile.mode_key in EXTERNAL_APPS:
                self._launch_external_app(tile.mode_key)
            else:
                self.switch_mode(tile.mode_key)

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
        if not WEBENGINE_AVAILABLE:
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
                self.youtube_adblock_interceptor.set_enabled(
                    self.settings_data.get("youtube_adblock", False)
                )
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
        if not self.settings_data.get("youtube_adblock", False):
            return
        if self.active_web_app != "youtube":
            return
        try:
            self.web_view.page().runJavaScript(YOUTUBE_ADBLOCK_JS)
        except Exception as e:
            logger.warning("Nem sikerült betölteni a YouTube reklámblokkoló JS-t: %s", e)


    def _show_web_app(self, key):
        app = WEB_APPS.get(key)
        if not app:
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
        try:
            self.player.stop()
        except Exception as e:
            logger.warning("Nem sikerült leállítani a lejátszást webnézetre váltáskor: %s", e)
        self.watchdog_timer.stop()
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

        try:
            proc = subprocess.Popen(command + app["args"])
            self._external_processes[key] = proc
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

    def _restore_after_external_app(self):
        # A showNormal() -> showFullScreen() sorrend azért kell, mert egy
        # minimalizált ablakot néhány ablakkezelő nem hoz vissza helyesen
        # közvetlenül teljes képernyőre showFullScreen()-nel egyedül.
        self.showNormal()
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def switch_mode(self, new_mode):
        if new_mode not in self.sources:
            return
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
        global VOLUME_BAR_STYLE
        VOLUME_BAR_STYLE = _volume_bar_stylesheet()
        self.volume_bar.setStyleSheet(VOLUME_BAR_STYLE)

        self.info_card.set_colors(THEME.SOLID_BG, THEME.SOLID_BORDER)
        self.menu_panel.set_colors(THEME.MENU_BG, THEME.MENU_BORDER)
        self.mode_menu.set_colors(THEME.MODE_PANEL_BG, THEME.MODE_PANEL_BORDER)
        self.settings_panel.set_colors(THEME.MENU_BG, THEME.MENU_BORDER)
        self.radio_visualizer.set_colors(THEME.SOLID_BG, THEME.SOLID_BORDER)
        self.number_osd.set_colors(THEME.SOLID_BG, THEME.SOLID_BORDER)
        self.volume_osd.set_colors(THEME.SOLID_BG, THEME.SOLID_BORDER)
        self.loading_card.set_colors(THEME.SOLID_BG, THEME.SOLID_BORDER)
        self.exit_confirm_card.set_colors(THEME.SOLID_BG, THEME.SOLID_BORDER)
        self.help_card.set_colors(THEME.MENU_BG, THEME.MENU_BORDER)
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
                       self.radio_visualizer, self.number_osd, self.volume_osd,
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
        if not self.isVisible() or self.isMinimized():
            return
        geo = self.video_frame.geometry()
        if geo.width() < 2:
            return
        self.video_frame.resize(geo.width() - 1, geo.height())
        QTimer.singleShot(0, lambda: self.video_frame.setGeometry(geo))

    def _show_widget(self, panel):
        panel.show()
        panel.raise_()
        self._kick_video_repaint()
        if not self._animations_enabled():
            panel.opacity = 1.0
            panel.update()
            return
        self._animate_opacity(panel, 0.0, 1.0, 190)

    def _hide_widget(self, panel):
        if not panel.isVisible():
            return
        self._kick_video_repaint()
        if not self._animations_enabled():
            panel.opacity = 0.0
            panel.hide()
            return
        self._animate_opacity(panel, 1.0, 0.0, 190, on_finished=panel.hide)

    def _animate_opacity(self, panel, start, end, duration, on_finished=None):
        anim = QPropertyAnimation(panel, b"opacity", self)
        anim.setDuration(duration)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        if on_finished:
            anim.finished.connect(on_finished)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        panel._fade_anim = anim  # referencia megtartása, amíg fut

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

        self._write_settings()
        try:
            self.player.stop()
        except Exception:
            pass

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

        lw, lh = self.loading_card.width(), self.loading_card.height()
        self.loading_card.move((w - lw) // 2, (h - lh) // 2)

        ew, eh = self.error_card.width(), self.error_card.height()
        self.error_card.move((w - ew) // 2, (h - eh) // 2)

        xw, xh = self.exit_confirm_card.width(), self.exit_confirm_card.height()
        self.exit_confirm_card.move((w - xw) // 2, (h - xh) // 2)

        hcw, hch = self.help_card.width(), self.help_card.height()
        self.help_card.move((w - hcw) // 2, (h - hch) // 2)

        super().resizeEvent(event)

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


def main():
    # A Qt dokumentáció kifejezetten javasolja, hogy ez az attribútum MÁR a
    # QApplication létrehozása ELŐTT be legyen állítva, ha QtWebEngine-t
    # használunk (a beépített YouTube-nézethez) EGYÜTT egy natív videó-
    # kimenettel (a VLC saját X11/EGL-alapú megjelenítésével). Enélkül a
    # kettő GPU-kontextusa ütközhet - ez a legvalószínűbb magyarázat arra,
    # hogy YouTube-ról visszaváltva néha nem jelent meg a kép a TV-n, és
    # valószínűleg hozzájárult a beágyazott böngésző ismételt megnyitásakor
    # tapasztalt összeomláshoz is.
    if WEBENGINE_AVAILABLE:
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
    if not shared_mem.create(1):
        logger.warning("A TV Box már fut egy másik példányban - kilépés.")
        sys.exit(0)

    default_font = QFont(FONT_FALLBACKS[0], 10)
    if hasattr(default_font, "setFamilies"):
        default_font.setFamilies(FONT_FALLBACKS)
    app.setFont(default_font)

    window = TVBox()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
