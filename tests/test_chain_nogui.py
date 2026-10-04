"""Qt nélküli lánc-teszt: Supervisor + Worker + kapu együtt, szimulált VLC-vel.
Azt ellenőrzi, hogy a régi adás késői eseményei nem indítanak téves újrapróbát."""
import sys, os, time, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tvbox.vlcworker import VlcWorker
from tvbox.buffering import StreamSupervisor

class Ctl:
    """A PlayerMixin kapu-logikájának (Qt nélküli) tükre."""
    def __init__(s):
        s.gen, s.open, s.retries_scheduled, s.q = 0, False, 0, []
        s.sup = StreamSupervisor(); s.sup.reset("u", False)
    def switched(s, g):
        if g == s.gen: s.open = True
    def error(s):
        if s.open: s.retries_scheduled += 1
    def start(s, w, url):
        s.gen += 1; s.open = False; w.request_play(s.gen, url, [])

class Player:
    def __init__(s, ctl): s.ctl = ctl; s.stale_fired = 0
    def set_media(s, m):
        time.sleep(0.2)
        s.ctl.error()          # a régi adás "Error" eseménye a lezárás közben
        s.stale_fired += 1
    def play(s): pass
    def stop(s): pass
    def audio_set_volume(s, v): pass
    def audio_set_mute(s, m): pass
class Inst:
    def media_new(s, u):
        class M:
            def add_option(self, o): pass
        return M()

def test_stale_events_ignored():
    c = Ctl(); p = Player(c)
    w = VlcWorker(Inst(), p, c.switched, lambda g, e: None); w.start()
    for i in range(5):
        c.start(w, "u%d" % i); time.sleep(0.05)
    time.sleep(1.5)
    assert p.stale_fired >= 1
    assert c.retries_scheduled == 0, "téves újrapróba a régi adás eseményéből"
    assert c.open
    c.error(); assert c.retries_scheduled == 1   # az ÚJ adás hibája viszont számít
    assert w.close()

if __name__ == "__main__":
    test_stale_events_ignored(); print("OK test_stale_events_ignored")
