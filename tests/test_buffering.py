import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tvbox.buffering import *

def test_escalation_and_persist():
    s = StreamSupervisor()
    s.reset("http://x/a.m3u8", False)
    assert s.cache_ms() == 2000
    a, d, c = s.next_action("stalled")
    assert (a, c) == ("retry", 3500) and d == 1.0
    a, d, c = s.next_action("stalled")
    assert c == 6000 and d == 2.0
    # megtanult szint új csatornaválasztásnál is megmarad
    learned = dict(s.learned)
    s2 = StreamSupervisor(learned); s2.reset("http://x/a.m3u8", False)
    assert s2.cache_ms() == 6000
    s2.reset("http://x/other", False)
    assert s2.cache_ms() == 2000

def test_giveup():
    s = StreamSupervisor(); s.reset("u", True)
    acts = [s.next_action("error")[0] for _ in range(6)]
    assert acts[:MAX_AUTO_RETRIES] == ["retry"] * MAX_AUTO_RETRIES
    assert acts[MAX_AUTO_RETRIES] == "giveup"
    # hiba (nem stall) nem emeli a cache-t
    s.reset("v", True); assert s.next_action("error")[2] == 3000

def test_stall_detection():
    s = StreamSupervisor(); s.reset("u", False)
    assert s.check(5, 0) == "ok"
    assert s.check(19, 0) == "stalled"          # sosem indult el
    s.on_playing(2); s.on_buffering(30, 10)
    assert s.check(15, 0) == "ok"
    assert s.check(23, 0) == "stalled"          # 13 s pufferelés
    s.on_buffering(100, 24)
    assert s.check(100, 0) == "ok"

def test_ladder_cap():
    s = StreamSupervisor(); s.reset("u", False)
    for _ in range(10): s.escalate()
    assert s.cache_ms() == 9000

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("OK", n)
