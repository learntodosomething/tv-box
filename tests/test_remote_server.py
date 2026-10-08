"""A telefonos távirányító HTTP-szervere: hitelesítés, ellenőrzés, korlátozás (Qt nélkül)."""
import sys, os, json, time, threading, urllib.request, urllib.error
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tvbox import remote
from tvbox.remote_page import PAGE

TOKEN = "tok_Abc123xyz"
CATALOG = {"modes": [{"key": "tv"}, {"key": "radio"}, {"key": "youtube"}], "channels": {"tv": []}}

def make(port=0):
    got = []
    srv = remote.RemoteServer(TOKEN, got.append, lambda: {"mode": "tv", "volume": 50},
                              lambda: CATALOG, PAGE, host="127.0.0.1", port=port)
    srv.start(); return srv, got

def call(srv, method, path, body=None, token=TOKEN, raw=None, headers=None):
    h = dict(headers or {})
    if token is not None: h["X-Token"] = token
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (srv.port, path), data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=5) as r: return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, e.read()

def test_page_served_without_token_api_requires_it():
    srv, _ = make()
    try:
        st, body = call(srv, "GET", "/", token=None)
        assert st == 200 and b"TV Box" in body
        assert call(srv, "GET", "/api/state", token=None)[0] == 401
        assert call(srv, "GET", "/api/state", token="rossz")[0] == 401
        st, body = call(srv, "GET", "/api/state")
        assert st == 200 and json.loads(body)["volume"] == 50
        assert call(srv, "GET", "/api/channels")[0] == 200
        assert call(srv, "GET", "/nincs")[0] == 404
    finally: srv.stop()

def test_power_and_setting_commands_are_validated():
    v = remote.validate_command
    assert v({"cmd": "power", "state": "off", "held": 2000}, []) == {"cmd": "power", "state": "off"}
    assert v({"cmd": "power", "state": "on", "held": 1800}, []) == {"cmd": "power", "state": "on"}
    for bad in ({"cmd": "power", "state": "off"},                           # nincs nyomva tartás
                {"cmd": "power", "state": "off", "held": 500},              # túl rövid
                {"cmd": "power", "state": "off", "held": True},
                {"cmd": "power", "state": "off", "held": "2000"},
                {"cmd": "power", "state": "reboot", "held": 3000},
                {"cmd": "power", "held": 3000}):
        assert v(bad, []) is None, bad
    keys = ["brightness", "theme"]
    assert v({"cmd": "setting", "key": "theme", "dir": 1}, [], keys) == {"cmd": "setting", "key": "theme", "dir": 1}
    for bad in ({"cmd": "setting", "key": "nincs", "dir": 1}, {"cmd": "setting", "key": "theme", "dir": 2},
                {"cmd": "setting", "key": "theme", "dir": True}, {"cmd": "setting", "key": "theme"},
                {"cmd": "setting", "key": ["theme"], "dir": 1}):
        assert v(bad, [], keys) is None, bad
    assert v({"cmd": "setting", "key": "theme", "dir": 1}, []) is None       # kulcslista nélkül nem fogadja el


def test_power_and_setting_over_http():
    got = []
    cat = dict(CATALOG); cat["settings"] = [{"k": "theme", "l": "Téma", "o": ["a", "b"]}]
    srv = remote.RemoteServer(TOKEN, got.append, lambda: {}, lambda: cat, PAGE, host="127.0.0.1", port=0)
    srv.start()
    try:
        assert call(srv, "POST", "/api/cmd", {"cmd": "power", "state": "off", "held": 100})[0] == 400
        assert call(srv, "POST", "/api/cmd", {"cmd": "power", "state": "off", "held": 2000})[0] == 200
        assert call(srv, "POST", "/api/cmd", {"cmd": "setting", "key": "theme", "dir": -1})[0] == 200
        assert call(srv, "POST", "/api/cmd", {"cmd": "setting", "key": "hacker", "dir": 1})[0] == 400
        assert got == [{"cmd": "power", "state": "off"}, {"cmd": "setting", "key": "theme", "dir": -1}], got
    finally: srv.stop()


def test_epg_endpoint_requires_token_and_info_key_is_whitelisted():
    got = []
    srv = remote.RemoteServer(TOKEN, got.append, lambda: {}, lambda: CATALOG, PAGE, host="127.0.0.1", port=0,
                              get_epg=lambda: {"rev": 7, "now": {"tv": {"1": "18:00 Híradó"}}})
    srv.start()
    try:
        assert call(srv, "GET", "/api/epg", token=None)[0] == 401
        st, body = call(srv, "GET", "/api/epg")
        assert st == 200 and json.loads(body)["now"]["tv"]["1"] == "18:00 Híradó"
        assert call(srv, "POST", "/api/cmd", {"cmd": "key", "name": "info"})[0] == 200
        assert got and got[-1] == {"cmd": "key", "name": "info"}
    finally: srv.stop()
    # EPG-szolgáltató nélkül (régi hívó): üres, de érvényes válasz
    srv, _ = make()
    try:
        st, body = call(srv, "GET", "/api/epg")
        assert st == 200 and json.loads(body)["now"] == {}
    finally: srv.stop()

def test_commands_are_validated_and_dispatched():
    srv, got = make()
    try:
        ok = [{"cmd": "key", "name": "up"}, {"cmd": "digit", "value": "7"}, {"cmd": "volume", "delta": 5},
              {"cmd": "mute"}, {"cmd": "zap", "dir": -1}, {"cmd": "mode", "mode": "youtube"},
              {"cmd": "channel", "mode": "tv", "key": "12"}, {"cmd": "youtube", "text": "  macskák  "}]
        for c in ok: assert call(srv, "POST", "/api/cmd", c)[0] == 200, c
        assert got[-1] == {"cmd": "youtube", "text": "macskák"} and len(got) == len(ok)
        got.clear()
        bad = [{"cmd": "rm -rf"}, {"cmd": "key", "name": "f12"}, {"cmd": "digit", "value": "12"},
               {"cmd": "volume", "delta": True}, {"cmd": "volume", "delta": 0}, {"cmd": "zap", "dir": 2},
               {"cmd": "mode", "mode": "netflix"}, {"cmd": "channel", "mode": "tv", "key": "../1"},
               {"cmd": "channel", "mode": "tv", "key": "12345"}, {"cmd": "youtube", "text": "   "},
               {"cmd": "youtube", "text": "x" * 201}, {"cmd": "youtube", "text": "a\x00b"}, [1, 2], "str", 5]
        for c in bad: assert call(srv, "POST", "/api/cmd", c)[0] == 400, c
        assert call(srv, "POST", "/api/cmd", raw=b"{nem json", headers={"Content-Length": "9"})[0] == 400
        assert call(srv, "POST", "/api/cmd", raw=b"x" * 5000)[0] == 413
        assert call(srv, "POST", "/api/cmd", {"cmd": "mute"}, token=None)[0] == 401
        assert got == []
        assert call(srv, "POST", "/api/nope", {"cmd": "mute"})[0] == 404
        # a volume túl nagy értéke korlátozódik
        call(srv, "POST", "/api/cmd", {"cmd": "volume", "delta": 999}); assert got[-1]["delta"] == 20
    finally: srv.stop()

def test_bruteforce_lockout_and_recovery():
    srv, _ = make()
    try:
        codes = [call(srv, "GET", "/api/state", token="x%d" % i)[0] for i in range(remote.MAX_FAILS + 3)]
        assert codes[0] == 401 and codes[-1] == 429
        assert call(srv, "GET", "/api/state")[0] == 429          # még a helyes token is tiltott az ablakban
        srv._fails.clear()
        assert call(srv, "GET", "/api/state")[0] == 200
    finally: srv.stop()

def test_dispatch_error_is_500_not_crash():
    srv, _ = make(); srv.dispatch = lambda c: 1 / 0
    try:
        assert call(srv, "POST", "/api/cmd", {"cmd": "mute"})[0] == 500
        assert call(srv, "GET", "/api/state")[0] == 200          # a szerver él
    finally: srv.stop()

def test_clients_tracking_and_stop_frees_port():
    srv, _ = make(); t0 = time.monotonic()
    assert not srv.seen_since(t0)
    call(srv, "GET", "/api/state"); assert srv.seen_since(t0) and srv.recent_clients()
    port = srv.port; srv.stop(); assert not srv.running
    s2 = remote.RemoteServer(TOKEN, lambda c: 0, lambda: {}, lambda: CATALOG, PAGE, host="127.0.0.1", port=port)
    s2.start(); assert s2.port == port; s2.stop()

def test_port_fallback_when_busy():
    a, _ = make(); busy = a.port
    try:
        b = remote.RemoteServer(TOKEN, lambda c: 0, lambda: {}, lambda: CATALOG, PAGE, host="127.0.0.1", port=busy)
        b.start()
        try: assert busy < b.port <= busy + remote.PORT_TRIES
        finally: b.stop()
    finally: a.stop()

def test_concurrent_requests():
    srv, got = make(); errs = []
    def worker():
        for _ in range(25):
            try:
                assert call(srv, "POST", "/api/cmd", {"cmd": "volume", "delta": 5})[0] == 200
                assert call(srv, "GET", "/api/state")[0] == 200
            except Exception as e: errs.append(e)
    ts = [threading.Thread(target=worker) for _ in range(8)]
    try:
        [t.start() for t in ts]; [t.join() for t in ts]
        assert not errs, errs[:2] and errs[0]
        assert len(got) == 200
    finally: srv.stop()

def test_youtube_target_and_url_helpers():
    k, u = remote.youtube_target("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=5s")
    assert k == "watch" and u.endswith("v=dQw4w9WgXcQ")
    assert remote.youtube_target("https://youtu.be/dQw4w9WgXcQ")[0] == "watch"
    assert remote.youtube_target("https://m.youtube.com/shorts/abcDEF12345")[0] == "watch"
    k, u = remote.youtube_target("macskás videók & kutyák")
    assert k == "search" and "macsk%C3%A1s%20vide%C3%B3k%20%26%20kuty%C3%A1k" in u
    assert remote.youtube_target("évil.com/watch?v=dQw4w9WgXcQ")[0] == "search"
    ip = remote.lan_ip(); assert ip.count(".") == 3
    srv = remote.RemoteServer("T0K", lambda c: 0, lambda: {}, lambda: CATALOG, PAGE, port=8765)
    assert srv.url("192.168.1.9") == "http://192.168.1.9:8765/?t=T0K"

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("OK", n)
