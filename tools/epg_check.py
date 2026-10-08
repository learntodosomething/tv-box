#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EPG-ellenőrző: megmutatja, hogy egy XMLTV-forrásban mely csatornák találtak párt a
csatornalistával, és mit érdemes az EPG_ALIASES táblába (tvbox/epg_core.py) felvenni.
Csak Python kell hozzá (se Qt, se VLC).

    python tools/epg_check.py                       # a beállított forrás (TVBOX_EPG / beállításfájl / ~/.tvbox/epg.xml)
    python tools/epg_check.py http://szerver/epg.xml.gz
    python tools/epg_check.py ~/epg.xml --all       # a megtalált csatornák műsorát is kiírja
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tvbox import epg_core as E
from tvbox.channels import CHANNEL_DATA, RADIO_DATA
from tvbox.config import load_settings


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", help="XMLTV URL vagy fájl (alapból a beállított forrás)")
    ap.add_argument("--all", action="store_true", help="a talált csatornák most/következő műsorát is kiírja")
    args = ap.parse_args()

    source = args.source or E.resolve_epg_source((load_settings().get("settings") or {}))
    if not source:
        sys.exit("Nincs EPG-forrás. Adj meg egyet argumentumként, a TVBOX_EPG változóban, vagy tedd a fájlt ide: %s"
                 % E.EPG_LOCAL_CANDIDATES[0])
    names = [n for _, entries in CHANNEL_DATA + RADIO_DATA for n, _u in entries]
    wanted = set()
    for n in names:
        wanted.update(E.name_candidates(n))

    print("Forrás:", source)
    t0 = time.time()
    try:
        data = E.load_epg(source, wanted, force=True)
    except Exception as e:
        sys.exit("Nem sikerült betölteni: %s: %s" % (type(e).__name__, e))
    print("Feldolgozva %.1f mp alatt, %d használható EPG-csatorna.\n" % (time.time() - t0, data.channel_count))

    found = [n for n in names if data.has_channel(n)]
    missing = [n for n in names if not data.has_channel(n)]
    print("TALÁLT csatornák: %d / %d" % (len(found), len(names)))
    for n in found:
        if args.all:
            cur, nxt = data.now_next(n)
            print("  ✓ %-28s most: %s | következő: %s" % (
                n, "%s %s" % (E.fmt_clock(cur.start), cur.title) if cur else "-",
                "%s %s" % (E.fmt_clock(nxt.start), nxt.title) if nxt else "-"))
    if not args.all and found:
        print("  " + ", ".join(found))
    print("\nNINCS PÁRJA (%d): %s" % (len(missing), ", ".join(missing) or "-"))
    if missing:
        print("Ha ezeknek van EPG-je a forrásban, írd fel az XMLTV-beli nevüket az EPG_ALIASES táblába "
              "(tvbox/epg_core.py), pl.:  \"%s\": [\"az XMLTV-beli név\"]," % missing[0])


if __name__ == "__main__":
    main()
