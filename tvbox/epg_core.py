# -*- coding: utf-8 -*-
"""Egyszerű EPG (műsorújság) támogatás XMLTV forrásból - Qt-mentes mag.

A Qt-s integráció (időzítők, UI-frissítés) a tvbox/epg.py-ban van.

HOGYAN MŰKÖDIK?
--------------------------------------------------------------------------
* Forrás: egy XMLTV fájl (.xml vagy .xml.gz), URL-ként VAGY helyi fájlként.
  A forrás megadása (a sorrend egyben a prioritás):
    1) TVBOX_EPG környezeti változó,
    2) a ~/.tvbox_settings.json fájlban a "settings" blokk "_epg_source" kulcsa,
    3) ha egyik sincs: a ~/.tvbox/epg.xml (vagy epg.xml.gz) helyi fájl,
       ha létezik (pl. egy cron-ból futtatott tv_grab_huro / WebGrab+ /
       iptv-org/epg kimenete).
* A letöltés + feldolgozás HÁTTÉRSZÁLON fut, a felület közben nem akad.
* A letöltött fájl gyorsítótárba kerül (~/.tvbox/epg_<hash>.xml), így
  újraindításkor azonnal van műsorinfó, és hálózathiánál is működik.
  A frissítés alapból 12 óránként történik.
* A csatornák és az XMLTV-csatornák összerendelése NÉV alapján történik
  (ékezet-, kis/nagybetű- és "HD"-függetlenül, az XMLTV display-name és id
  mezői alapján). Ha egy csatorna nem találja a párját, az EPG_ALIASES
  táblába írhatod be a másik nevét.
* Memóriabarát: csak a ténylegesen használt csatornák és a [-6 óra, +72 óra]
  ablakba eső műsorok kerülnek a memóriába.
"""
import gzip
import hashlib
import json
import os
import re
import tempfile
import threading
import time
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from bisect import bisect_right
from collections import namedtuple
from datetime import datetime, timedelta, timezone

from tvbox.compat import logger


EPG_DIR = os.path.join(os.path.expanduser("~"), ".tvbox")
EPG_LOCAL_CANDIDATES = (
    os.path.join(EPG_DIR, "epg.xml"),
    os.path.join(EPG_DIR, "epg.xml.gz"),
)

EPG_REFRESH_S = 12 * 3600          # ennyi után tekintjük elavultnak a gyorsítótárat
EPG_PAST_WINDOW_S = 6 * 3600       # a már lezajlott műsorokból ennyit tartunk meg
EPG_FUTURE_WINDOW_S = 72 * 3600    # ennyivel előre tartjuk meg a műsorokat
EPG_DOWNLOAD_TIMEOUT_S = 25                      # egy hálózati olvasás időkorlátja
EPG_DOWNLOAD_TOTAL_S = 180                       # a teljes letöltés időkorlátja (csepegtető szerver ellen)
EPG_MAX_DOWNLOAD_BYTES = 80 * 1024 * 1024        # letöltött (tömörített) fájl felső határa
EPG_MAX_XML_BYTES = 400 * 1024 * 1024            # kicsomagolt XML felső határa (zip-bomba ellen)
EPG_MAX_PROGRAMMES = 400000                      # ennyi műsor után abbahagyjuk a feldolgozást
EPG_STORE_DESC = False                           # a leírást jelenleg sehol nem mutatjuk: ne foglalja a memóriát
EPG_YIELD_EVERY = 1000                              # >0: ennyi elemenként átadjuk a GIL-t (mérés szerint nem kell: a feldolgozás magában <20 ms késést okoz)
EPG_YIELD_S = 0.001
EPG_TICK_MS = 30 * 1000

# Ha egy csatorna nevét az XMLTV-ben másképp hívják, itt add meg a lehetséges
# alternatív neveket (a csatornalistabeli név -> alternatív nevek listája).
EPG_ALIASES = {
    "M2 / Petőfi TV": ["M2", "Petőfi TV", "Petofi TV", "M2 HD"],
    "M1": ["M1 HD"],
    "Duna TV": ["Duna", "Duna HD"],
    "RTL": ["RTL Klub", "RTL Klub HD"],
    "RTL+ / RTL Három": ["RTL+", "RTL Plusz", "RTL Három", "RTL Harom", "RTL Plus"],
    "RTL Kettő": ["RTL2", "RTL Ketto", "RTL II"],
    "Super TV2": ["SuperTV2", "Super TV 2"],
    "TV2": ["TV2 HD"],
    "Film+": ["Film Plusz", "FilmPlus"],
    "Mozi+": ["Mozi Plusz", "MoziPlus"],
    "Sport 1": ["Sport1"],
    "Sport 2": ["Sport2"],
    "National Geographic": ["Nat Geo", "NatGeo", "Nat Geo HD"],
    "National Geographic Wild": ["Nat Geo Wild", "NatGeo Wild"],
    "Crime + Investigation": ["Crime and Investigation", "Crime Investigation"],
    "Nick Jr.": ["Nick Junior", "Nick Jr"],
    "TV Paprika": ["Paprika", "Paprika TV"],
    "Magyar Mozi TV": ["Magyar Mozi"],
    "Viasat 6": ["Viasat6"],
    "Viasat 2": ["Viasat2"],
    "Viasat 3": ["Viasat3"],
}


Programme = namedtuple("Programme", "start stop title desc")


# ===========================================================================
# Névnormalizálás és időbélyeg-értelmezés
# ===========================================================================
def norm_name(text):
    """Ékezet-, kis/nagybetű- és írásjel-független összehasonlítási kulcs.
    A "+" jel "plus"-szá alakul (RTL+ != RTL), a végén álló "HD" elmarad."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = text.replace("+", " plus ").replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "", text)
    if text.endswith("hd") and len(text) > 3:
        text = text[:-2]
    return text


def name_candidates(name):
    """Egy csatornanévhez tartozó összes elfogadható normalizált kulcs:
    a teljes név, a "/" és "(" mentén szétvágott részek, valamint az
    EPG_ALIASES-beli alternatív nevek."""
    raw_names = [name] + list(EPG_ALIASES.get(name, ()))
    result = []
    for raw in raw_names:
        parts = [raw]
        for piece in re.split(r"\s*/\s*|\s*\(", raw):
            piece = piece.strip(" )")
            if piece and piece != raw:
                parts.append(piece)
        for part in parts:
            key = norm_name(part)
            if len(key) >= 2 and key not in result:
                result.append(key)
    return result


_TS_RE = re.compile(
    r"^\s*(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?\s*([+-]\d{4}|Z)?\s*$"
)


def parse_xmltv_time(text):
    """XMLTV időbélyeg ("20261003180000 +0200") -> epoch másodperc, vagy None.
    Időzóna nélküli érték helyi időnek számít."""
    if not text:
        return None
    m = _TS_RE.match(text)
    if not m:
        return None
    y, mo, d, h, mi, s, tz = m.groups()
    try:
        dt = datetime(int(y), int(mo or 1), int(d or 1), int(h or 0), int(mi or 0), int(s or 0))
        if tz == "Z":
            dt = dt.replace(tzinfo=timezone.utc)
        elif tz:
            offset = timedelta(hours=int(tz[1:3]), minutes=int(tz[3:5]))
            dt = dt.replace(tzinfo=timezone(-offset if tz[0] == "-" else offset))
        return dt.timestamp()
    except (ValueError, OverflowError, OSError):
        return None


def fmt_clock(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M")


# ===========================================================================
# Az EPG adat és a lekérdezés
# ===========================================================================
class _Schedule:
    __slots__ = ("starts", "items")

    def __init__(self, items):
        self.items = items
        self.starts = [p.start for p in items]


class EpgData:
    """Egy betöltött EPG pillanatképe. A betöltés után NEM módosul (a háttér-
    szál egy újat épít, és a főszálon cseréljük le), ezért szálbiztos az
    olvasása."""

    def __init__(self, by_norm, source, loaded_at=None):
        self._by_norm = by_norm            # normalizált név -> _Schedule
        self.source = source
        self.loaded_at = loaded_at or time.time()
        self._name_cache = {}              # csatornanév -> _Schedule | None

    @property
    def channel_count(self):
        return len({id(s) for s in self._by_norm.values()})

    def _schedule_for(self, name):
        if name in self._name_cache:
            return self._name_cache[name]
        found = None
        for key in name_candidates(name):
            found = self._by_norm.get(key)
            if found is not None:
                break
        self._name_cache[name] = found
        return found

    def has_channel(self, name):
        return self._schedule_for(name) is not None

    def now_next(self, name, now=None):
        """(jelenlegi, következő) Programme-pár; bármelyik lehet None."""
        sched = self._schedule_for(name)
        if sched is None:
            return None, None
        now = time.time() if now is None else now
        j = bisect_right(sched.starts, now)
        current = None
        if j > 0 and sched.items[j - 1].stop > now:
            current = sched.items[j - 1]
        nxt = sched.items[j] if j < len(sched.items) else None
        return current, nxt


# ===========================================================================
# XMLTV feldolgozás
# ===========================================================================
class _LimitedReader:
    """Olvasás-korlátozó burkoló: egy kicsomagolt fájl nem nőhet a végtelenségig."""

    def __init__(self, raw, limit):
        self._raw = raw
        self._left = limit

    def read(self, size=-1):
        if size is None or size < 0:
            size = 1 << 20
        chunk = self._raw.read(min(size, 1 << 20))
        self._left -= len(chunk)
        if self._left < 0:
            raise ValueError("Az EPG fájl a megengedettnél nagyobb")
        return chunk


def _open_xml_stream(path):
    f = open(path, "rb")
    magic = f.read(2)
    f.seek(0)
    if magic == b"\x1f\x8b":
        return _LimitedReader(gzip.GzipFile(fileobj=f), EPG_MAX_XML_BYTES), f
    return _LimitedReader(f, EPG_MAX_XML_BYTES), f


def parse_xmltv(path, wanted_norms, now=None):
    """Egy XMLTV fájl feldolgozása. `wanted_norms`: a ténylegesen használt
    csatornák normalizált neveinek halmaza (üres/None = minden csatorna).
    Visszaad: EpgData."""
    now = time.time() if now is None else now
    win_lo = now - EPG_PAST_WINDOW_S
    win_hi = now + EPG_FUTURE_WINDOW_S

    chan_norms = {}     # xmltv id -> {normalizált nevek}
    ok_cache = {}       # xmltv id -> bool (kell-e nekünk)
    progs = {}          # xmltv id -> [ [start, stop|None, title, desc], ... ]
    count = 0
    seen = 0

    reader, fileobj = _open_xml_stream(path)
    try:
        root = None
        for event, el in ET.iterparse(reader, events=("start", "end")):
            if root is None:
                root = el
                continue
            if event != "end":
                continue
            tag = el.tag
            if tag == "channel":
                cid = el.get("id")
                if cid:
                    names = {norm_name(cid)}
                    for dn in el.findall("display-name"):
                        names.add(norm_name(dn.text))
                    names.discard("")
                    chan_norms[cid] = names
                    ok_cache.pop(cid, None)
                el.clear()
            elif tag == "programme":
                cid = el.get("channel")
                if cid is not None:
                    ok = ok_cache.get(cid)
                    if ok is None:
                        names = chan_norms.get(cid) or {norm_name(cid)}
                        ok = (not wanted_norms) or bool(names & wanted_norms)
                        ok_cache[cid] = ok
                    if ok:
                        start = parse_xmltv_time(el.get("start"))
                        stop = parse_xmltv_time(el.get("stop"))
                        if start is not None and start < win_hi and (stop is None or stop > win_lo):
                            title_el = el.find("title")
                            title = (title_el.text or "").strip() if title_el is not None else ""
                            if title:
                                desc = ""
                                if EPG_STORE_DESC:
                                    desc_el = el.find("desc")
                                    desc = (desc_el.text or "").strip() if desc_el is not None else ""
                                progs.setdefault(cid, []).append(
                                    [start, stop, title[:120], desc[:400]]
                                )
                                count += 1
                el.clear()
                seen += 1
                if EPG_YIELD_EVERY and seen % EPG_YIELD_EVERY == 0:
                    time.sleep(EPG_YIELD_S)     # a háttérszál ne éheztesse ki a GUI-szálat (GIL)
                if count >= EPG_MAX_PROGRAMMES:
                    logger.warning("EPG: elértük a %d műsoros korlátot, a maradékot kihagyom.",
                                   EPG_MAX_PROGRAMMES)
                    break
                if root is not None and len(root) > 500:
                    root.clear()        # a már feldolgozott gyerekek eldobása
            # (egyéb elemeket - pl. display-name, title - a szülő törlése takarítja)
    finally:
        try:
            fileobj.close()
        except Exception:
            pass

    by_norm = {}
    for cid, items in progs.items():
        items.sort(key=lambda r: r[0])
        # hiányzó "stop" pótlása a következő műsor kezdetével
        for i, row in enumerate(items):
            if row[1] is None or row[1] <= row[0]:
                row[1] = items[i + 1][0] if i + 1 < len(items) else row[0] + 1800
        sched = _Schedule([Programme(*row) for row in items if row[1] > row[0]])
        if not sched.items:
            continue
        for key in (chan_norms.get(cid) or {norm_name(cid)}):
            if key and key not in by_norm:
                by_norm[key] = sched
    return EpgData(by_norm, path)


# ===========================================================================
# Letöltés + gyorsítótár (háttérszálon fut)
# ===========================================================================
def _is_url(source):
    return source.lower().startswith(("http://", "https://"))


def _cache_path_for(source):
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:10]
    return os.path.join(EPG_DIR, "epg_%s.xml" % digest)


def _download(url, dest):
    """Atomikus letöltés: előbb ideiglenes fájlba, aztán átnevezés."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".epg_dl_", dir=os.path.dirname(dest))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TVBox-EPG/1.0"})
        total = 0
        deadline = time.monotonic() + EPG_DOWNLOAD_TOTAL_S
        with urllib.request.urlopen(req, timeout=EPG_DOWNLOAD_TIMEOUT_S) as resp, \
                os.fdopen(fd, "wb") as out:
            while True:
                # read1(): azonnal visszatér, amint van adat (a read(n) n bájtig blokkolna,
                # így a határidőt egy csepegtető szerver ki tudná játszani)
                chunk = resp.read1(1 << 16) if hasattr(resp, "read1") else resp.read(1 << 14)
                if not chunk:
                    break
                if time.monotonic() > deadline:
                    raise TimeoutError("Az EPG letöltés túl sokáig tart")
                total += len(chunk)
                if total > EPG_MAX_DOWNLOAD_BYTES:
                    raise ValueError("Az EPG letöltés a megengedettnél nagyobb")
                out.write(chunk)
        if total == 0:
            raise ValueError("Az EPG letöltés üres")
        os.replace(tmp, dest)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def load_epg(source, wanted_norms, force=False, refresh_s=EPG_REFRESH_S):
    """A teljes betöltési folyamat (szinkron - háttérszálból hívandó).
    Hibánál kivételt dob; letöltési hibánál a meglévő gyorsítótárat használja."""
    if not _is_url(source):
        path = os.path.expanduser(source)
        if not os.path.isfile(path):
            raise FileNotFoundError("Az EPG fájl nem található: %s" % path)
        data = parse_xmltv(path, wanted_norms)
        data.source = source
        return data

    cache = _cache_path_for(source)
    fresh = (os.path.isfile(cache)
             and (time.time() - os.path.getmtime(cache)) < refresh_s)
    if force or not fresh:
        try:
            _download(source, cache)
        except Exception as e:
            if not os.path.isfile(cache):
                raise
            logger.warning("EPG letöltés sikertelen (%s) - a gyorsítótárat használom.", e)
    data = parse_xmltv(cache, wanted_norms)
    data.source = source
    try:
        data.loaded_at = os.path.getmtime(cache)
    except OSError:
        pass
    return data


def resolve_epg_source(settings):
    """A beállítások/környezet alapján megállapítja az EPG-forrást ('' = nincs)."""
    env = os.environ.get("TVBOX_EPG", "").strip()
    if env:
        return env
    saved = settings.get("_epg_source") if isinstance(settings, dict) else None
    if isinstance(saved, str) and saved.strip():
        return saved.strip()
    for candidate in EPG_LOCAL_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    return ""
