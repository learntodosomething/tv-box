# -*- coding: utf-8 -*-
"""Külső alkalmazások és beépített webalkalmazások (YouTube stb.)."""
import os
import shutil
import sys


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
