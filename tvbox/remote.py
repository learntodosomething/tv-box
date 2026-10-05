# -*- coding: utf-8 -*-
"""Telefonos távirányító: beépített, függőségmentes HTTP-szerver (Qt-független).

A szerver egy háttérszálon fut. SOHA nem nyúl a GUI-hoz: a parancsokat a
`dispatch` visszahívásnak adja át (a Qt oldalon ez egy signal -> GUI-szál),
az állapotot pedig a `get_state` / `get_catalog` által visszaadott, kész
Python-objektumokból olvassa.

BIZTONSÁG (a szerver a helyi hálózaton hallgat, ezért):
  * minden API-híváshoz titkos token kell (X-Token fejléc; a QR-kód tartalmazza),
    összehasonlítás időzítés-biztosan (hmac.compare_digest);
  * IP-nként korlátozott hibás próbálkozás (10 / perc), utána 429;
  * parancs-lista (whitelist) és bemenet-ellenőrzés, max. 2 KB törzs;
  * nincs CORS-fejléc, a POST egyedi fejlécet igényel -> más weboldalról nem hívható;
  * kikapcsolt állapotban egyáltalán nem hallgat.
"""
import hmac
import json
import logging
import os
import re
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote

log = logging.getLogger("tvbox")

DEFAULT_PORT = 8765
PORT_TRIES = 20
MAX_BODY = 2048
MAX_FAILS = 10
FAIL_WINDOW_S = 60.0

KEY_NAMES = frozenset(["up", "down", "left", "right", "enter", "esc", "back",
                       "menu", "source", "settings", "help"])

# YouTube címsablonok. FIGYELEM: a keresési mélylinket (Leanback/TV felület) nem tudtam
# offline ellenőrizni; ha a keresés nem a találatokra érkezik, itt kell átírni.
# Alternatíva a kereséshez:  "https://www.youtube.com/results?search_query={q}"
YOUTUBE_SEARCH_URL = "https://www.youtube.com/tv#/search?q={q}"
YOUTUBE_WATCH_URL = "https://www.youtube.com/watch?v={v}"

_YT_ID = re.compile(r"(?:youtu\.be/|youtube\.com/(?:watch\?(?:[^#\s]*&)?v=|shorts/|embed/|live/))([A-Za-z0-9_-]{11})")


def youtube_target(text):
    """('watch'|'search', url) - YouTube-linket megnyit, bármi mást keresésként kezel."""
    m = _YT_ID.search(text)
    if m:
        return "watch", YOUTUBE_WATCH_URL.format(v=m.group(1))
    return "search", YOUTUBE_SEARCH_URL.format(q=quote(text, safe=""))


def lan_ip():
    """A géphez tartozó helyi hálózati IP (nem küld csomagot)."""
    ip = ""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except OSError:
        ip = ""
    finally:
        s.close()
    if not ip or ip.startswith("127."):
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except OSError:
            ip = "127.0.0.1"
    return ip


def validate_command(obj, modes):
    """A telefonról érkező JSON ellenőrzése. Visszaad egy tisztított dict-et vagy None-t."""
    if not isinstance(obj, dict):
        return None
    cmd = obj.get("cmd")
    if cmd == "key":
        name = obj.get("name")
        return {"cmd": "key", "name": name} if isinstance(name, str) and name in KEY_NAMES else None
    if cmd == "digit":
        v = obj.get("value")
        return {"cmd": "digit", "value": v} if isinstance(v, str) and len(v) == 1 and v in "0123456789" else None
    if cmd == "volume":
        d = obj.get("delta")
        if isinstance(d, bool) or not isinstance(d, int) or d == 0:
            return None
        return {"cmd": "volume", "delta": max(-20, min(20, d))}
    if cmd == "mute":
        return {"cmd": "mute"}
    if cmd == "zap":
        d = obj.get("dir")
        return {"cmd": "zap", "dir": d} if d in (-1, 1) and not isinstance(d, bool) else None
    if cmd == "mode":
        m = obj.get("mode")
        return {"cmd": "mode", "mode": m} if isinstance(m, str) and m in modes else None
    if cmd == "channel":
        m, k = obj.get("mode"), obj.get("key")
        if isinstance(m, str) and m in modes and isinstance(k, str) and k.isdigit() and 1 <= len(k) <= 4:
            return {"cmd": "channel", "mode": m, "key": k}
        return None
    if cmd == "youtube":
        t = obj.get("text")
        if isinstance(t, str):
            t = t.strip()
            if 1 <= len(t) <= 200 and all(ch >= " " for ch in t):
                return {"cmd": "youtube", "text": t}
        return None
    return None


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    # Windowson a SO_REUSEADDR más folyamattal is engedne ugyanarra a portra kötni.
    allow_reuse_address = (os.name != "nt")

    def server_bind(self):
        if os.name == "nt" and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class RemoteServer:
    def __init__(self, token, dispatch, get_state, get_catalog, page_html,
                 host="0.0.0.0", port=DEFAULT_PORT):
        self.token = token
        self.dispatch = dispatch
        self.get_state = get_state
        self.get_catalog = get_catalog
        self.page = page_html.encode("utf-8") if isinstance(page_html, str) else page_html
        self.host, self.port = host, port
        self.httpd = None
        self.thread = None
        self._lock = threading.Lock()
        self._seen = {}     # ip -> utolsó hitelesített kérés ideje (monotonic)
        self._fails = {}    # ip -> (hibák száma, ablak kezdete)

    # -- életciklus -------------------------------------------------------
    def start(self):
        ports = [0] if self.port == 0 else range(self.port, self.port + PORT_TRIES)
        handler = self._make_handler()
        last_err = None
        for p in ports:
            try:
                self.httpd = _Server((self.host, p), handler)
                break
            except OSError as e:
                last_err = e
        if self.httpd is None:
            raise last_err or OSError("nincs szabad port")
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever,
                                       kwargs={"poll_interval": 0.25},
                                       name="remote-http", daemon=True)
        self.thread.start()
        return self.port

    def stop(self):
        httpd, self.httpd = self.httpd, None
        if httpd is not None:
            try:
                httpd.shutdown()
                httpd.server_close()
            except Exception as e:  # noqa
                log.warning("A távirányító leállítása közben hiba: %s", e)
        if self.thread is not None:
            self.thread.join(2.0)
            self.thread = None

    @property
    def running(self):
        return self.httpd is not None

    def url(self, ip=None):
        return "http://%s:%d/?t=%s" % (ip or lan_ip(), self.port, self.token)

    # -- kliens-nyilvántartás ----------------------------------------------
    def note_client(self, ip):
        with self._lock:
            self._seen[ip] = time.monotonic()
            self._fails.pop(ip, None)

    def recent_clients(self, window=6.0):
        now = time.monotonic()
        with self._lock:
            return [ip for ip, t in self._seen.items() if now - t <= window]

    def seen_since(self, ts):
        """Volt-e hitelesített kérés `ts` (monotonic) óta?"""
        with self._lock:
            return any(t >= ts for t in self._seen.values())

    def _note_fail(self, ip):
        now = time.monotonic()
        with self._lock:
            n, start = self._fails.get(ip, (0, now))
            if now - start > FAIL_WINDOW_S:
                n, start = 0, now
            self._fails[ip] = (n + 1, start)

    def _blocked(self, ip):
        now = time.monotonic()
        with self._lock:
            n, start = self._fails.get(ip, (0, now))
            return n >= MAX_FAILS and now - start <= FAIL_WINDOW_S

    # -- HTTP --------------------------------------------------------------
    def _make_handler(self):
        srv = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "TVBoxRemote"
            protocol_version = "HTTP/1.0"
            timeout = 5

            def log_message(self, fmt, *args):  # nincs konzol-zaj
                pass

            def _send(self, code, body=b"", ctype="application/json; charset=utf-8"):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                if body:
                    self.wfile.write(body)

            def _json(self, code, obj):
                self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

            def _auth(self):
                ip = self.client_address[0]
                if srv._blocked(ip):
                    self._json(429, {"error": "túl sok hibás próbálkozás"})
                    return False
                supplied = self.headers.get("X-Token", "")
                if not supplied or not hmac.compare_digest(supplied.encode("utf-8"),
                                                           srv.token.encode("utf-8")):
                    srv._note_fail(ip)
                    self._json(401, {"error": "érvénytelen token"})
                    return False
                srv.note_client(ip)
                return True

            def do_GET(self):
                path = self.path.split("?", 1)[0]
                if path in ("/", "/index.html"):
                    self._send(200, srv.page, "text/html; charset=utf-8")
                elif path == "/api/state":
                    if self._auth():
                        self._json(200, srv.get_state())
                elif path == "/api/channels":
                    if self._auth():
                        self._json(200, srv.get_catalog())
                elif path == "/favicon.ico":
                    self._send(204)
                else:
                    self._json(404, {"error": "nincs ilyen oldal"})

            def do_POST(self):
                path = self.path.split("?", 1)[0]
                if path != "/api/cmd":
                    self._json(404, {"error": "nincs ilyen oldal"})
                    return
                if not self._auth():
                    return
                try:
                    length = int(self.headers.get("Content-Length", "-1"))
                except ValueError:
                    length = -1
                if length <= 0 or length > MAX_BODY:
                    self._json(413 if length > MAX_BODY else 400, {"error": "hibás törzs"})
                    return
                try:
                    obj = json.loads(self.rfile.read(length).decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    self._json(400, {"error": "hibás JSON"})
                    return
                modes = [m["key"] for m in srv.get_catalog().get("modes", [])]
                clean = validate_command(obj, modes)
                if clean is None:
                    self._json(400, {"error": "ismeretlen vagy hibás parancs"})
                    return
                try:
                    srv.dispatch(clean)
                except Exception as e:  # noqa
                    log.warning("Távirányító-parancs hiba: %s", e)
                    self._json(500, {"error": "belső hiba"})
                    return
                self._json(200, {"ok": True})

        return Handler
