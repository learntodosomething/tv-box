# -*- coding: utf-8 -*-
"""EPG (XMLTV) mag: névegyeztetés, időbélyegek, feldolgozás, hibás/rosszindulatú fájlok,
gyorsítótár és letöltés (Qt és VLC nélkül futtatható)."""
import gzip, http.server, os, sys, tempfile, threading, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xml.etree.ElementTree as ET
from tvbox import epg_core as E
from epg_fixture import make_xmltv, xmltv_time

TMP = tempfile.mkdtemp()
E.EPG_DIR = os.path.join(TMP, "cache")          # a valódi ~/.tvbox-ot ne bántsuk


def wanted(*names):
    out = set()
    for n in names:
        out.update(E.name_candidates(n))
    return out


def test_norm_and_candidates():
    assert E.norm_name("Petőfi TV") == E.norm_name("PETOFI tv") == "petofitv"
    assert E.norm_name("RTL+") == "rtlplus" and E.norm_name("RTL+") != E.norm_name("RTL")
    assert E.norm_name("M1 HD") == "m1" and E.norm_name("ducktv HD") == "ducktv"
    assert E.norm_name("HD") == "hd"             # túl rövid: nem csonkoljuk
    assert E.norm_name(None) == "" and E.norm_name("") == ""
    c = E.name_candidates("M2 / Petőfi TV")
    assert "m2" in c and "petofitv" in c
    assert "jednotka" in E.name_candidates("Jednotka (RTVS)")
    assert "natgeo" in E.name_candidates("National Geographic")


def test_parse_time():
    t = E.parse_xmltv_time
    assert t("20261003180000 +0200") == t("20261003160000 +0000") == t("20261003160000Z")
    assert t("20261003180000 -0130") - t("20261003180000 +0000") == 5400
    assert t("202610031800") is not None and t("2026") is not None
    for bad in (None, "", "abc", "20261340180000 +0000", "20261003256100 +0000", "99999999999999"):
        assert t(bad) is None, bad


def _write(name, text, gz=False):
    p = os.path.join(TMP, name)
    data = text.encode("utf-8")
    if gz:
        data = gzip.compress(data)
    open(p, "wb").write(data)
    return p


def test_now_next_edges():
    now = 1_800_000_000
    def ts(off): return xmltv_time(now + off, 0)
    xml = ('<tv><channel id="a"><display-name>Híradó TV</display-name></channel>'
           '<programme start="%s" stop="%s" channel="a"><title>Egy</title></programme>'
           '<programme start="%s" stop="%s" channel="a"><title>Kettő</title></programme>'
           '<programme start="%s" channel="a"><title>Három (nincs stop)</title></programme>'
           '</tv>') % (ts(-3600), ts(-60), ts(60), ts(1800), ts(3600))
    d = E.parse_xmltv(_write("a.xml", xml), wanted("Híradó TV"), now=now)
    cur, nxt = d.now_next("Híradó TV", now)
    assert cur is None and nxt.title == "Kettő"                   # lyuk a két műsor között
    cur, nxt = d.now_next("Híradó TV", now + 61)
    assert cur.title == "Kettő" and nxt.title.startswith("Három")
    cur, nxt = d.now_next("Híradó TV", now + 1800)               # pontosan a határon: az újabb kezdődik
    assert cur is None or cur.title != "Kettő"
    cur, nxt = d.now_next("Híradó TV", now + 3600 + 5)
    assert cur.title.startswith("Három") and nxt is None
    assert cur.stop == cur.start + 1800                          # hiányzó stop pótlása
    assert d.now_next("Nincs ilyen", now) == (None, None)
    assert d.has_channel("hiradó tv") and d.has_channel("HÍRADÓ tv")   # kis/nagybetű, ékezet


def test_window_and_wanted_filter():
    now = time.time()
    p = os.path.join(TMP, "w.xml")
    make_xmltv(p, ["RTL", "TV2"], hours_back=24, hours_fwd=200, extra_channels=3, now=now)
    d = E.parse_xmltv(p, wanted("RTL"), now=now)
    assert d.has_channel("RTL") and not d.has_channel("TV2")     # csak a kért csatorna
    sched = d._schedule_for("RTL")
    assert all(pr.stop > now - E.EPG_PAST_WINDOW_S and pr.start < now + E.EPG_FUTURE_WINDOW_S for pr in sched.items)
    assert len(sched.items) < 24 * 2 + 200 * 2                    # az ablakon kívüli adat eldobva
    d_all = E.parse_xmltv(p, None, now=now)
    assert d_all.has_channel("TV2") and d_all.has_channel("Extra csatorna 1")


def test_match_by_id_and_alias():
    now = time.time()
    p = os.path.join(TMP, "id.xml")
    make_xmltv(p, ["RTL Klub"], use_ids_only=True, now=now)       # nincs display-name, az id "ch0.hu"
    d = E.parse_xmltv(p, None, now=now)
    assert d.has_channel("ch0.hu")
    make_xmltv(p, ["RTL Klub"], now=now)
    d = E.parse_xmltv(p, wanted("RTL"), now=now)                  # "RTL" alias: "RTL Klub"
    assert d.has_channel("RTL")
    cur, nxt = d.now_next("RTL")
    assert cur is not None and nxt is not None


def test_gz_and_timezones():
    now = time.time()
    p1, p2 = os.path.join(TMP, "tz1.xml.gz"), os.path.join(TMP, "tz2.xml")
    make_xmltv(p1, ["Duna TV"], gz=True, tz_hours=2, now=now)
    make_xmltv(p2, ["Duna TV"], tz_hours=-5, now=now)
    a = E.parse_xmltv(p1, wanted("Duna TV"), now=now).now_next("Duna TV", now)
    b = E.parse_xmltv(p2, wanted("Duna TV"), now=now).now_next("Duna TV", now)
    assert a[0].start == b[0].start and a[0].stop == b[0].stop    # más időzóna, ugyanaz az időpont


def test_bad_inputs_raise_cleanly_and_never_hang():
    for name, text in [("trunc.xml", '<tv><channel id="a"><display-name>X</disp'),
                       ("empty.xml", ""), ("notxml.xml", "ez nem xml"),
                       ("wrongroot.xml", "<html><body>404</body></html>")]:
        p = _write(name, text)
        try:
            d = E.parse_xmltv(p, None)
            assert d.channel_count == 0                           # üres, de nem dob (pl. html)
        except ET.ParseError:
            pass
    # hibás gzip
    p = os.path.join(TMP, "bad.gz"); open(p, "wb").write(b"\x1f\x8b" + os.urandom(200))
    try:
        E.parse_xmltv(p, None); assert False, "hibás gz-nek kivételt kell dobnia"
    except Exception as e:
        assert not isinstance(e, AssertionError)
    # hibás elemek: üres cím, hiányzó csatorna-attribútum, érvénytelen idő
    xml = ('<tv><channel id="a"><display-name>X1</display-name></channel>'
           '<programme start="xx" stop="yy" channel="a"><title>Rossz idő</title></programme>'
           '<programme start="%s" channel="a"><title></title></programme>'
           '<programme start="%s"><title>Nincs csatorna</title></programme>'
           '<programme channel="a"><title>Nincs start</title></programme></tv>') % ((xmltv_time(time.time(), 0),) * 2)
    d = E.parse_xmltv(_write("junk.xml", xml), None)
    assert d.channel_count == 0


def test_decompression_bomb_limit():
    old = E.EPG_MAX_XML_BYTES
    E.EPG_MAX_XML_BYTES = 200 * 1024
    try:
        p = os.path.join(TMP, "bomb.xml.gz")
        with gzip.open(p, "wb") as f:
            f.write(b"<tv>")
            for _ in range(2000):
                f.write(b"<!-- " + b"A" * 1000 + b" -->")
            f.write(b"</tv>")
        try:
            E.parse_xmltv(p, None); assert False, "a túl nagy kicsomagolt fájlt el kell utasítani"
        except ValueError:
            pass
    finally:
        E.EPG_MAX_XML_BYTES = old


def test_entity_expansion_attack_is_safe():
    # "billion laughs": a Python/expat új verziói korlátozzák; mindenképp gyorsan és kivétellel/üresen kell végezni.
    xml = ('<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol">'
           '<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">'
           '<!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">'
           '<!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">'
           '<!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">'
           '<!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">'
           '<!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">'
           '<!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">'
           '<!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">]>'
           '<tv><channel id="a"><display-name>&lol9;</display-name></channel></tv>')
    t0 = time.time()
    try:
        E.parse_xmltv(_write("lolz.xml", xml), None)
    except Exception:
        pass
    assert time.time() - t0 < 5.0, "az entitás-bővítés túl lassú / memóriazabáló"


def test_resolve_source_priority():
    old_c, old_env = E.EPG_LOCAL_CANDIDATES, os.environ.pop("TVBOX_EPG", None)
    try:
        local = os.path.join(TMP, "epg.xml"); open(local, "w").write("<tv/>")
        E.EPG_LOCAL_CANDIDATES = (local,)
        assert E.resolve_epg_source({}) == local
        assert E.resolve_epg_source({"_epg_source": " http://x/e.xml "}) == "http://x/e.xml"
        os.environ["TVBOX_EPG"] = "/env/path.xml"
        assert E.resolve_epg_source({"_epg_source": "http://x"}) == "/env/path.xml"
        del os.environ["TVBOX_EPG"]
        E.EPG_LOCAL_CANDIDATES = (os.path.join(TMP, "nincs.xml"),)
        assert E.resolve_epg_source({}) == "" and E.resolve_epg_source({"_epg_source": 5}) == ""
    finally:
        E.EPG_LOCAL_CANDIDATES = old_c
        os.environ.pop("TVBOX_EPG", None)
        if old_env is not None: os.environ["TVBOX_EPG"] = old_env


class _Handler(http.server.BaseHTTPRequestHandler):
    hits = 0
    mode = "ok"
    body = b""
    def log_message(self, *a): pass
    def do_GET(self):
        type(self).hits += 1
        if self.mode == "500":
            self.send_response(500); self.end_headers(); return
        if self.mode == "empty":
            self.send_response(200); self.send_header("Content-Length", "0"); self.end_headers(); return
        if self.mode == "hang":
            time.sleep(3); return
        if self.mode == "drip":                      # csepegtető szerver: mindig érkezik egy kis adat
            self.send_response(200); self.send_header("Content-Length", "100000"); self.end_headers()
            try:
                for _ in range(100):
                    self.wfile.write(b"x" * 10); self.wfile.flush(); time.sleep(0.1)
            except OSError:
                pass
            return
        self.send_response(200); self.send_header("Content-Length", str(len(self.body))); self.end_headers()
        self.wfile.write(self.body)


def _serve():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_download_cache_and_fallback():
    p = os.path.join(TMP, "dl.xml.gz")
    make_xmltv(p, ["TV2"], gz=True)
    _Handler.body, _Handler.mode, _Handler.hits = open(p, "rb").read(), "ok", 0
    srv = _serve(); url = "http://127.0.0.1:%d/epg.xml.gz" % srv.server_address[1]
    try:
        d = E.load_epg(url, wanted("TV2"))
        assert d.has_channel("TV2") and _Handler.hits == 1
        E.load_epg(url, wanted("TV2"))                            # friss gyorsítótár: nincs új letöltés
        assert _Handler.hits == 1
        _Handler.mode = "500"
        d = E.load_epg(url, wanted("TV2"), force=True)            # szerverhiba -> gyorsítótár
        assert d.has_channel("TV2") and _Handler.hits == 2
        _Handler.mode = "empty"
        assert E.load_epg(url, wanted("TV2"), force=True).has_channel("TV2")
        # gyorsítótár nélkül a hiba kivétel (a hívó kezeli)
        os.remove(E._cache_path_for(url))
        try:
            E.load_epg(url, wanted("TV2")); assert False
        except AssertionError: raise
        except Exception: pass
        # a sikertelen letöltés nem hagy ideiglenes fájlt
        leftovers = [f for f in os.listdir(E.EPG_DIR) if f.startswith(".epg_dl_")]
        assert not leftovers, leftovers
    finally:
        srv.shutdown()


def test_download_size_limit_and_timeout():
    old_lim, old_to = E.EPG_MAX_DOWNLOAD_BYTES, E.EPG_DOWNLOAD_TIMEOUT_S
    _Handler.body, _Handler.mode = b"x" * 300000, "ok"
    srv = _serve(); url = "http://127.0.0.1:%d/big.xml" % srv.server_address[1]
    try:
        E.EPG_MAX_DOWNLOAD_BYTES = 100000
        try: E.load_epg(url, set()); assert False
        except AssertionError: raise
        except ValueError: pass
        E.EPG_DOWNLOAD_TIMEOUT_S = 1
        _Handler.mode = "hang"
        t0 = time.time()
        try: E.load_epg(url + "2", set()); assert False
        except AssertionError: raise
        except Exception: pass
        assert time.time() - t0 < 2.5, "a letöltési időkorlát nem működik"
    finally:
        E.EPG_MAX_DOWNLOAD_BYTES, E.EPG_DOWNLOAD_TIMEOUT_S = old_lim, old_to
        srv.shutdown()


def test_slow_drip_download_hits_total_deadline():
    old = E.EPG_DOWNLOAD_TOTAL_S
    E.EPG_DOWNLOAD_TOTAL_S = 1
    _Handler.mode = "drip"
    srv = _serve(); url = "http://127.0.0.1:%d/drip.xml" % srv.server_address[1]
    try:
        t0 = time.time()
        try: E.load_epg(url, set()); assert False
        except AssertionError: raise
        except Exception: pass
        assert time.time() - t0 < 4, "a csepegtető szerver blokkolja a letöltést"
    finally:
        E.EPG_DOWNLOAD_TOTAL_S = old
        srv.shutdown()


def test_missing_local_file():
    try: E.load_epg(os.path.join(TMP, "nincs_ilyen.xml"), set()); assert False
    except FileNotFoundError: pass


def test_large_file_speed_and_memory():
    p = os.path.join(TMP, "big.xml")
    n = make_xmltv(p, ["RTL", "TV2", "M1"], hours_back=6, hours_fwd=72, step_minutes=10, extra_channels=150)
    size = os.path.getsize(p) / 1048576
    t0 = time.time()
    d = E.parse_xmltv(p, wanted("RTL", "TV2", "M1"))
    dt = time.time() - t0
    print("   %d műsor, %.1f MB, feldolgozás %.2f s, csatorna: %d" % (n, size, dt, d.channel_count))
    assert d.channel_count == 3 and dt < 20
    t0 = time.time()
    for _ in range(20000):
        d.now_next("RTL"); d.now_next("Ismeretlen csatorna")
    assert time.time() - t0 < 2.0, "a lekérdezésnek gyorsnak kell lennie"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("OK", n)
