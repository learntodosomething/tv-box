# -*- coding: utf-8 -*-
"""Beállítások mentése/betöltése és a beállítás-séma."""
import json
import os
import tempfile
from tvbox.compat import logger


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
        "key": "digit_timeout_ms", "label": "Váltás türelmi ideje", "kind": "choice",
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


# ===========================================================================
# VLC hangolás (pufferelés / stabilitás)
#
# VLC_BASE_ARGS: biztosan létező kapcsolók. VLC_OPTIONAL_ARGS: ha a telepített
# VLC valamelyiket nem ismeri, az app automatikusan nélkülük indul újra.
# A csatornánkénti puffer (network/live-caching) NEM itt, hanem lejátszáskor,
# a StreamSupervisor szerint kerül a médiára (lásd tvbox/buffering.py).
# ===========================================================================
VLC_BASE_ARGS = [
    "--quiet", "--no-video-title-show", "--no-osd",
    "--no-snapshot-preview", "--no-sub-autodetect-file",
]
VLC_OPTIONAL_ARGS = ["--no-stats", "--http-reconnect"]
