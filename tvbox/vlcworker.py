# -*- coding: utf-8 -*-
"""A libVLC blokkoló hívásainak (set_media / play / stop / hangerő) külön szálra tétele.

MIÉRT: a VLC 3.x set_media()/stop() híváskor SZINKRON módon lezárja az előző
bemenetet (hálózati kapcsolatok, demuxer, kimenet). Lassú vagy nem válaszoló
szervernél ez több másodpercig - mérésnél 11-13 mp-ig - blokkolhatja a hívó
szálat. Ha ez a Qt GUI-szál, a teljes felület megfagy. Ez az osztály a
hívásokat egyetlen háttérszálon futtatja, "legutolsó kérés nyer" elvvel:
a közben felgyűlt köztes csatornaváltásokat eldobja, így a VLC-t sem terheli
30 lejátszás/mp.

A modul Qt-független (visszahívásokkal dolgozik), ezért VLC nélkül tesztelhető.
FIGYELEM: a visszahívások a MUNKASZÁLON futnak; Qt-ba csak signalon át szabad
továbbítani őket.
"""
import threading


class VlcWorker:
    """KOMPOZÍCIÓ, nem öröklés: a threading.Thread belső attribútumai (pl. a
    Python 3.13 `_handle`-je) korábban elfedték a saját metódusaimat, és minden
    lejátszás TypeError-ral elbukott."""

    def __init__(self, instance, player, on_switched, on_failed, log=None):
        self._thread = threading.Thread(target=self._run, name="vlc-worker", daemon=True)
        self._instance = instance
        self._player = player
        self._on_switched = on_switched    # (gen) - a régi bemenet már lezárult
        self._on_failed = on_failed        # (gen, exc)
        self._log = log or (lambda *a: None)
        self._cv = threading.Condition()
        self._req = None                   # ("play", gen, url, opts) | ("stop", gen)
        self._audio = None                 # (volume, muted)
        self._closing = False
        self.busy_since = None             # diagnosztika: mióta blokkol egy hívás

    def start(self):
        self._thread.start()

    def is_alive(self):
        return self._thread.is_alive()

    # -- a GUI-szálról hívható, SOHA nem blokkoló kérések ---------------------
    def request_play(self, gen, url, opts):
        with self._cv:
            self._req = ("play", gen, url, list(opts))
            self._cv.notify()

    def request_stop(self, gen):
        with self._cv:
            self._req = ("stop", gen)
            self._cv.notify()

    def request_audio(self, volume, muted):
        with self._cv:
            self._audio = (volume, muted)
            self._cv.notify()

    def close(self, timeout=4.0):
        """Leállítás. True, ha a szál a határidőn belül le is állt."""
        with self._cv:
            self._closing = True
            self._req = None
            self._cv.notify()
        if self._thread.is_alive():
            self._thread.join(timeout)
        return not self._thread.is_alive()

    # -- munkaszál --------------------------------------------------------
    def _run(self):
        while True:
            with self._cv:
                while self._req is None and self._audio is None and not self._closing:
                    self._cv.wait()
                if self._closing:
                    break
                req, self._req = self._req, None
                audio, self._audio = self._audio, None
            try:
                if req is not None:
                    self._process(req)
                if audio is not None:
                    vol, muted = audio
                    self._player.audio_set_volume(int(vol))
                    self._player.audio_set_mute(bool(muted))
            except Exception as e:  # noqa - a szál sosem halhat meg csendben
                self._log("VLC munkaszál hiba: %r" % (e,))
                if req is not None:
                    try:
                        self._on_failed(req[1], e)
                    except Exception:
                        pass
        try:
            self._player.stop()
        except Exception:
            pass

    def _process(self, req):
        import time
        self.busy_since = time.monotonic()
        try:
            if req[0] == "stop":
                self._player.stop()
                return
            _, gen, url, opts = req
            media = self._instance.media_new(url)
            for o in opts:
                media.add_option(o)
            self._player.set_media(media)   # itt záródik le szinkron a régi bemenet
            self._on_switched(gen)          # a régi adás eseményei már mögöttünk vannak
            self._player.play()
        finally:
            self.busy_since = None
