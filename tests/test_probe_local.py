"""A stream_probe önellenőrzése helyi, szándékosan lassított HLS-szerverrel."""
import sys, os, threading, time, http.server, socketserver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import stream_probe as sp

SEG = b"x" * 200_000          # 4 s-os szegmens, 200 kB
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/fast/p.m3u8" or self.path == "/slow/p.m3u8":
            seq = int(time.time() // 2)
            body = ("#EXTM3U\n#EXT-X-TARGETDURATION:4\n#EXT-X-MEDIA-SEQUENCE:%d\n" % seq +
                    "".join("#EXTINF:4.0,\nseg%d.ts\n" % (seq + i) for i in range(3))).encode()
            self.send_response(200); self.end_headers(); self.wfile.write(body)
        elif self.path.startswith("/fast/seg"):
            self.send_response(200); self.end_headers(); self.wfile.write(SEG)
        elif self.path.startswith("/slow/seg"):     # 200 kB ~ 6 s alatt => RT ~0.66
            self.send_response(200); self.end_headers()
            for i in range(20):
                self.wfile.write(SEG[:10_000]); self.wfile.flush(); time.sleep(0.3)
        else:
            self.send_response(404); self.end_headers()

class S(socketserver.ThreadingMixIn, http.server.HTTPServer): daemon_threads = True

def test_parsers():
    master = "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=800000\nlow.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=2400000\nhi.m3u8\n"
    v = sp.parse_master(master, "http://h/a/m.m3u8")
    assert v == [(800000, "http://h/a/low.m3u8"), (2400000, "http://h/a/hi.m3u8")], v
    td, seq, segs = sp.parse_media("#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXT-X-MEDIA-SEQUENCE:7\n#EXTINF:5.9,\ns1.ts\n", "http://h/x/p.m3u8")
    assert (td, seq, segs) == (6.0, 7, [(5.9, "http://h/x/s1.ts")])

def test_live_server():
    srv = S(("127.0.0.1", 0), H); port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    fast = sp.probe(("tv", "1", "fast", "http://127.0.0.1:%d/fast/p.m3u8" % port))
    slow = sp.probe(("tv", "2", "slow", "http://127.0.0.1:%d/slow/p.m3u8" % port))
    dead = sp.probe(("tv", "3", "dead", "http://127.0.0.1:%d/nope.m3u8" % port))
    print(fast["realtime_x"], sp.verdict(fast)); print(slow["realtime_x"], sp.verdict(slow)); print(dead["error"], sp.verdict(dead))
    assert sp.verdict(fast) == "OK"
    assert sp.verdict(slow).startswith("LASSÚ")
    assert sp.verdict(dead) == "HALOTT"
    srv.shutdown()

if __name__ == "__main__":
    test_parsers(); print("OK parsers")
    test_live_server(); print("OK live server")
