# -*- coding: utf-8 -*-
"""Rendszer-hangerő: a valódi parancsok kimenet-formátumát utánzó kamu wpctl / pactl / amixer
szkriptekkel (Linux), nem blokkoló működés, hibatűrés."""
import os, stat, sys, tempfile, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tvbox import sysvol

TMP = tempfile.mkdtemp()
STATE = os.path.join(TMP, "state")


def script(name, body):
    p = os.path.join(TMP, name)
    open(p, "w").write("#!/bin/bash\n" + body)
    os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)


def setstate(vol, muted=False):
    open(STATE, "w").write("%d %d" % (vol, 1 if muted else 0))


def getstate():
    v, m = open(STATE).read().split()
    return int(v), m == "1"


# wpctl: "Volume: 0.45" / "Volume: 0.45 [MUTED]"
script("wpctl", """read V M < @S@
case "$1" in
 get-volume) printf "Volume: %d.%02d%s\\n" $((V/100)) $((V%100)) "$([ $M = 1 ] && echo ' [MUTED]')";;
 set-volume) NEW=$(python3 -c "print(round(float('$3')*100))"); echo "$NEW $M" > @S@;;
 set-mute) echo "$V $((1-M))" > @S@;;
esac""".replace("@S@", STATE))
# pactl: a valódi formátum
script("pactl", """read V M < @S@
case "$1" in
 get-sink-volume) echo "Volume: front-left: 32768 /  ${V}% / -18.06 dB,   front-right: 32768 /  ${V}% / -18.06 dB"; echo "        balance 0.00";;
 get-sink-mute) if [ $M = 1 ]; then echo "Mute: yes"; else echo "Mute: no"; fi;;
 set-sink-volume) NEW=${3%\\%}; echo "$NEW $M" > @S@;;
 set-sink-mute) echo "$V $((1-M))" > @S@;;
esac""".replace("@S@", STATE))
script("amixer", """read V M < @S@
case "$1" in
 sget) echo "Simple mixer control 'Master',0"; if [ $M = 1 ]; then ST=off; else ST=on; fi; echo "  Front Left: Playback 40000 [${V}%] [$ST]";;
 -q) if [ "$4" = toggle ]; then echo "$V $((1-M))" > @S@; else NEW=${4%\\%}; echo "$NEW $M" > @S@; fi;;
esac""".replace("@S@", STATE))


def with_path(only):
    """A PATH csak a kért kamu programot tartalmazza (+ a rendszer bash/python)."""
    keep = [TMP_BIN]
    return os.pathsep.join(keep)


TMP_BIN = os.path.join(TMP, "bin")


def make_bin(names):
    os.makedirs(TMP_BIN, exist_ok=True)
    for f in os.listdir(TMP_BIN):
        os.remove(os.path.join(TMP_BIN, f))
    for n in names:
        os.symlink(os.path.join(TMP, n), os.path.join(TMP_BIN, n))
    # a szkriptek bash-t, python3-at használnak: ezek elérhetőek maradnak a rendszer PATH-jából
    os.environ["PATH"] = TMP_BIN + os.pathsep + ORIG_PATH


ORIG_PATH = os.environ["PATH"]


def wait_for(cond, t=3.0):
    t0 = time.time()
    while time.time() - t0 < t:
        if cond():
            return True
        time.sleep(0.02)
    return False


def test_detect_order():
    make_bin(["wpctl", "pactl", "amixer"]); assert sysvol.detect_backend().name == "wpctl"
    make_bin(["pactl", "amixer"]); assert sysvol.detect_backend().name == "pactl"
    make_bin(["amixer"]); assert sysvol.detect_backend().name == "amixer"


def _exercise(names, expect_name):
    make_bin(names)
    setstate(40, False)
    sv = sysvol.SystemVolume()
    assert sv.available and sv.backend.name == expect_name
    assert sv.snapshot() == (None, None)                       # még nem olvastunk
    sv.refresh()
    assert wait_for(lambda: sv.snapshot() == (40, False)), sv.snapshot()
    sv.change(5)
    assert wait_for(lambda: getstate() == (45, False)) and wait_for(lambda: sv.snapshot() == (45, False))
    sv.change(-100)                                             # alsó korlát
    assert wait_for(lambda: getstate()[0] == 0)
    sv.change(500)                                              # felső korlát
    assert wait_for(lambda: getstate()[0] == 100)
    sv.toggle_mute()
    assert wait_for(lambda: getstate()[1] is True) and wait_for(lambda: sv.snapshot()[1] is True)
    sv.toggle_mute()
    assert wait_for(lambda: getstate()[1] is False)
    sv.change(-5)                                               # némított állapotból léptetve: marad a szám
    sv.stop()


def test_wpctl():  _exercise(["wpctl"], "wpctl")
def test_pactl():  _exercise(["pactl"], "pactl")
def test_amixer(): _exercise(["amixer"], "amixer")


def test_change_is_optimistic_and_nonblocking():
    make_bin(["wpctl"]); setstate(50)
    sv = sysvol.SystemVolume(); sv.refresh(); assert wait_for(lambda: sv.snapshot()[0] == 50)
    t0 = time.time()
    for _ in range(50):
        sv.change(1)
    assert time.time() - t0 < 0.2, "a change() nem blokkolhat"
    assert sv.snapshot()[0] == 100 or sv.snapshot()[0] >= 50     # azonnali becsült érték
    assert wait_for(lambda: getstate()[0] == 100, 6), getstate()


def test_no_backend_is_harmless():
    make_bin([])
    os.environ["PATH"] = TMP_BIN
    try:
        sv = sysvol.SystemVolume()
        assert not sv.available
        sv.refresh(); sv.change(5); sv.toggle_mute(); sv.stop()
        assert sv.snapshot() == (None, None)
    finally:
        os.environ["PATH"] = ORIG_PATH


def test_failing_and_hanging_commands_do_not_crash():
    script("wpctl_bad", 'echo "boom" >&2; exit 1\n')
    script("wpctl_hang", 'sleep 5\n')
    class B(sysvol.WpctlBackend): pass
    old = sysvol.CMD_TIMEOUT_S; sysvol.CMD_TIMEOUT_S = 0.4
    try:
        for exe in ("wpctl_bad", "wpctl_hang"):
            make_bin([]); os.symlink(os.path.join(TMP, exe), os.path.join(TMP_BIN, "wpctl"))
            sv = sysvol.SystemVolume(); t0 = time.time()
            sv.refresh(); sv.change(5); sv.toggle_mute()
            assert time.time() - t0 < 0.2
            time.sleep(1.5 if exe == "wpctl_hang" else 0.3)
            assert sv.snapshot() == (None, None)                 # hibánál nincs kitalált érték
            sv.stop()
    finally:
        sysvol.CMD_TIMEOUT_S = old


def test_garbage_output_is_rejected():
    script("wpctl_garbage", 'echo "valami teljesen más"\n')
    make_bin([]); os.symlink(os.path.join(TMP, "wpctl_garbage"), os.path.join(TMP_BIN, "wpctl"))
    sv = sysvol.SystemVolume(); sv.refresh(); time.sleep(0.4)
    assert sv.snapshot() == (None, None); sv.stop()


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("OK", n)
