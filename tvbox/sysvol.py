# -*- coding: utf-8 -*-
"""Rendszer-hangerő (a gép fő hangereje) - a külön ablakban futó YouTube-hoz.

MIÉRT KELL? A YouTube a Brave-ben, KÜLÖN folyamatként fut, a TV Box ilyenkor
minimalizálva van, és a saját VLC-je le van állítva: a VLC-hangerő ezért itt
hatástalan. Ilyenkor a telefon hangerő-gombjai a gép fő hangerejét állítják,
és a telefon ezt az értéket (százalékban) mutatja.

Támogatott háttérrendszerek (az első elérhető nyer):
  Linux:   wpctl (PipeWire) -> pactl (PulseAudio) -> amixer (ALSA)
  Windows: pycaw (pip install pycaw), ennek hiányában a billentyűzet
           hangerő-gombjai (ilyenkor a százalék NEM olvasható vissza)
  macOS:   osascript

Minden külső hívás egy KÜLÖN háttérszálon fut, időkorláttal - a felület
sosem várakozik rá. A legutóbbi ismert érték a snapshot()-tal azonnal lekérhető.
"""
import logging
import queue
import re
import shutil
import subprocess
import sys
import threading
import time

logger = logging.getLogger("tvbox")

CMD_TIMEOUT_S = 3.0


def _run(argv):
    res = subprocess.run(argv, capture_output=True, text=True, timeout=CMD_TIMEOUT_S)
    if res.returncode != 0:
        raise RuntimeError("%s -> %s" % (argv[0], (res.stderr or res.stdout).strip()[:120]))
    return res.stdout


def _clamp(value):
    return max(0, min(100, int(round(value))))


# ---------------------------------------------------------------------------
# Háttérrendszerek: get() -> (százalék|None, némítva|None), set(százalék), toggle_mute()
# ---------------------------------------------------------------------------
class WpctlBackend:
    name = "wpctl"
    SINK = "@DEFAULT_AUDIO_SINK@"

    def get(self):
        out = _run(["wpctl", "get-volume", self.SINK])
        m = re.search(r"Volume:\s*([0-9]*\.?[0-9]+)", out)
        if not m:
            raise RuntimeError("wpctl: nem értelmezhető kimenet: %r" % out[:80])
        return _clamp(float(m.group(1)) * 100), "[MUTED]" in out

    def set(self, percent):
        _run(["wpctl", "set-volume", self.SINK, "%.2f" % (percent / 100.0)])

    def toggle_mute(self):
        _run(["wpctl", "set-mute", self.SINK, "toggle"])


class PactlBackend:
    name = "pactl"
    SINK = "@DEFAULT_SINK@"

    def get(self):
        out = _run(["pactl", "get-sink-volume", self.SINK])
        m = re.search(r"(\d+)%", out)
        if not m:
            raise RuntimeError("pactl: nem értelmezhető kimenet: %r" % out[:80])
        mute = _run(["pactl", "get-sink-mute", self.SINK])
        return _clamp(int(m.group(1))), bool(re.search(r"yes|igen", mute, re.I))

    def set(self, percent):
        _run(["pactl", "set-sink-volume", self.SINK, "%d%%" % percent])

    def toggle_mute(self):
        _run(["pactl", "set-sink-mute", self.SINK, "toggle"])


class AmixerBackend:
    name = "amixer"

    def get(self):
        out = _run(["amixer", "sget", "Master"])
        m = re.search(r"\[(\d+)%\]", out)
        if not m:
            raise RuntimeError("amixer: nem értelmezhető kimenet: %r" % out[:80])
        return _clamp(int(m.group(1))), bool(re.search(r"\[off\]", out))

    def set(self, percent):
        _run(["amixer", "-q", "sset", "Master", "%d%%" % percent])

    def toggle_mute(self):
        _run(["amixer", "-q", "sset", "Master", "toggle"])


class OsascriptBackend:
    name = "osascript"

    def get(self):
        out = _run(["osascript", "-e", "output volume of (get volume settings)"]).strip()
        muted = _run(["osascript", "-e", "output muted of (get volume settings)"]).strip() == "true"
        return _clamp(int(out)), muted

    def set(self, percent):
        _run(["osascript", "-e", "set volume output volume %d" % percent])

    def toggle_mute(self):
        _, muted = self.get()
        _run(["osascript", "-e", "set volume output muted %s" % ("false" if muted else "true")])


class PycawBackend:
    """Windows fő hangerő a pycaw-n keresztül. A COM-objektumokat KIZÁRÓLAG a
    háttérszálon hozzuk létre és használjuk (COM-szál-szabály)."""
    name = "pycaw"

    def __init__(self):
        self._endpoint = None

    def _vol(self):
        if self._endpoint is None:
            import comtypes
            from comtypes import CLSCTX_ALL
            from ctypes import POINTER, cast
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            try:
                comtypes.CoInitialize()
            except OSError:
                pass
            dev = AudioUtilities.GetSpeakers()
            ep = getattr(dev, "EndpointVolume", None)       # újabb pycaw
            if ep is None:
                iface = dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                ep = cast(iface, POINTER(IAudioEndpointVolume))
            self._endpoint = ep
        return self._endpoint

    def get(self):
        ep = self._vol()
        return _clamp(ep.GetMasterVolumeLevelScalar() * 100), bool(ep.GetMute())

    def set(self, percent):
        self._vol().SetMasterVolumeLevelScalar(percent / 100.0, None)

    def toggle_mute(self):
        ep = self._vol()
        ep.SetMute(0 if ep.GetMute() else 1, None)


class WinKeysBackend:
    """Tartalék Windows-on: a billentyűzet hangerő-gombjai. A pontos érték nem
    olvasható vissza (get() -> (None, None)), a lépés kb. 2% / gombnyomás."""
    name = "winkeys"
    VK_MUTE, VK_DOWN, VK_UP = 0xAD, 0xAE, 0xAF

    def __init__(self):
        import ctypes
        self._user32 = ctypes.windll.user32

    def _tap(self, vk, times=1):
        for _ in range(times):
            self._user32.keybd_event(vk, 0, 0, 0)
            self._user32.keybd_event(vk, 0, 2, 0)

    def get(self):
        return None, None

    def set(self, percent):
        pass

    def delta(self, d):
        self._tap(self.VK_UP if d > 0 else self.VK_DOWN, max(1, abs(d) // 2))

    def toggle_mute(self):
        self._tap(self.VK_MUTE)


def detect_backend():
    """Az első működő háttérrendszer, vagy None."""
    if sys.platform == "win32":
        try:
            import pycaw.pycaw  # noqa: F401
            return PycawBackend()
        except Exception:
            try:
                return WinKeysBackend()
            except Exception:
                return None
    if sys.platform == "darwin":
        return OsascriptBackend() if shutil.which("osascript") else None
    for exe, cls in (("wpctl", WpctlBackend), ("pactl", PactlBackend), ("amixer", AmixerBackend)):
        if shutil.which(exe):
            return cls()
    return None


# ---------------------------------------------------------------------------
# A GUI-szál felé nyújtott, nem blokkoló felület
# ---------------------------------------------------------------------------
class SystemVolume:
    def __init__(self, backend="auto"):
        self.backend = detect_backend() if backend == "auto" else backend
        self._lock = threading.Lock()
        self._percent = None
        self._muted = None
        self._stamp = 0.0
        self._q = queue.Queue(maxsize=64)
        self._thread = None
        self._stopped = False

    @property
    def available(self):
        return self.backend is not None

    @property
    def can_read(self):
        return self.available and getattr(self.backend, "name", "") != "winkeys"

    def snapshot(self):
        """(százalék|None, némítva|None) - a legutóbbi ismert érték, azonnal."""
        with self._lock:
            return self._percent, self._muted

    def age(self):
        with self._lock:
            return time.monotonic() - self._stamp if self._stamp else float("inf")

    # -- parancsok (nem blokkolnak) ----------------------------------------
    def refresh(self):
        self._submit(("read", 0))

    def change(self, delta):
        with self._lock:                                  # azonnali, becsült érték a kijelzéshez
            if self._percent is not None:
                self._percent = _clamp(self._percent + delta)
                if delta > 0:
                    self._muted = False
        self._submit(("delta", int(delta)))

    def toggle_mute(self):
        with self._lock:
            if self._muted is not None:
                self._muted = not self._muted
        self._submit(("mute", 0))

    def stop(self):
        self._stopped = True
        try:
            self._q.put_nowait(("stop", 0))
        except queue.Full:
            pass

    # -- belső ---------------------------------------------------------------
    def _submit(self, job):
        if not self.available or self._stopped:
            return
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._worker, name="tvbox-sysvol", daemon=True)
            self._thread.start()
        try:
            self._q.put_nowait(job)
        except queue.Full:
            pass            # túlterhelés (pl. nyomva tartott gomb): a következő olvasás helyreállítja

    def _store(self, percent, muted):
        with self._lock:
            self._percent, self._muted, self._stamp = percent, muted, time.monotonic()

    def _worker(self):
        b = self.backend
        while not self._stopped:
            kind, arg = self._q.get()
            if kind == "stop":
                return
            # A torlódott, azonos típusú parancsokat összevonjuk (nyomva tartott gomb).
            if kind == "delta":
                try:
                    while True:
                        nk, na = self._q.get_nowait()
                        if nk == "delta":
                            arg += na
                        else:
                            self._q.put_nowait((nk, na))
                            break
                except queue.Empty:
                    pass
            try:
                if kind == "read":
                    self._store(*b.get())
                elif kind == "delta":
                    if hasattr(b, "delta"):
                        b.delta(arg)
                    else:
                        cur, _ = b.get()
                        b.set(_clamp((cur if cur is not None else 0) + arg))
                    if self.can_read:
                        self._store(*b.get())
                elif kind == "mute":
                    b.toggle_mute()
                    if self.can_read:
                        self._store(*b.get())
            except Exception as e:      # a hangerő-hiba sosem dönthet el semmit
                logger.warning("Rendszer-hangerő (%s) hiba: %s", getattr(b, "name", "?"), e)
