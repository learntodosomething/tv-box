import sys, os, time, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tvbox.vlcworker import VlcWorker

class FakeMedia:
    def __init__(s, url): s.url, s.opts = url, []
    def add_option(s, o): s.opts.append(o)
class FakeInst:
    def media_new(s, url): return FakeMedia(url)
class FakePlayer:
    def __init__(s, block=0.0): s.block, s.log, s.thread_names = block, [], set()
    def set_media(s, m):
        s.thread_names.add(threading.current_thread().name); time.sleep(s.block); s.log.append(("set", m.url))
    def play(s): s.log.append(("play",))
    def stop(s): s.log.append(("stop",))
    def audio_set_volume(s, v): s.log.append(("vol", v))
    def audio_set_mute(s, m): s.log.append(("mute", m))

def make(block=0.0):
    p = FakePlayer(block); sw, fl = [], []
    w = VlcWorker(FakeInst(), p, sw.append, lambda g, e: fl.append((g, repr(e))))
    w.start(); return w, p, sw, fl

def wait(cond, t=5):
    end = time.time() + t
    while time.time() < end and not cond(): time.sleep(0.01)
    return cond()

def test_caller_never_blocks_and_latest_wins():
    w, p, sw, fl = make(block=1.0)               # minden set_media 1 mp-ig "blokkol"
    t0 = time.perf_counter()
    for i in range(200):
        w.request_play(i, "http://h/%d" % i, [":network-caching=2000"])
        w.request_audio(i % 100, False)
    assert time.perf_counter() - t0 < 0.1, "a hívó blokkolt!"
    assert wait(lambda: sw and sw[-1] == 199, 6), sw
    sets = [x for x in p.log if x[0] == "set"]
    assert len(sets) <= 3, "köztes csatornák nem estek ki: %d" % len(sets)
    assert sets[-1] == ("set", "http://h/199")
    assert p.thread_names == {"vlc-worker"}, "nem a munkaszálon futott"
    assert w.close()

def test_stop_supersedes_play():
    w, p, sw, fl = make(block=0.5)
    w.request_play(1, "http://a", []); time.sleep(0.1)
    w.request_play(2, "http://b", []); w.request_stop(3)
    assert wait(lambda: ("stop",) in p.log)
    time.sleep(0.8)
    assert ("set", "http://b") not in p.log and sw == [1]
    assert w.close()

def test_exception_reported_not_fatal():
    w, p, sw, fl = make()
    def boom(m): raise RuntimeError("x")
    p.set_media = boom
    w.request_play(7, "u", [])
    assert wait(lambda: fl) and fl[0][0] == 7
    p.set_media = lambda m: p.log.append(("set", m.url))
    w.request_play(8, "ok", [])
    assert wait(lambda: sw and sw[-1] == 8) and w.is_alive()
    assert w.close()

def test_no_name_collision_with_thread():
    import threading
    w, p, sw, fl = make()
    assert not isinstance(w, threading.Thread)
    # a saját attribútumok/metódusok egyike sem lehet azonos egy Thread-példány belső nevével
    t = threading.Thread(target=lambda: None)
    mine = {n for n in dir(w) if not n.startswith("__")}
    clash = mine & set(vars(t)) & {n for n in mine if n.startswith("_")}
    assert not clash, clash
    w.request_play(1, "u", [])
    assert wait(lambda: sw == [1]) and not fl, fl      # a 3.13-as hiba itt failed-et adott
    assert w.close()

def test_close_while_idle_stops_player():
    w, p, sw, fl = make()
    assert w.close() and p.log[-1] == ("stop",)

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("OK", n)
