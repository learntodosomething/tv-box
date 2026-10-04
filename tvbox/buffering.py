# -*- coding: utf-8 -*-
"""Pufferelés-felügyelet: Qt- és VLC-független döntési logika.

A StreamSupervisor NEM nyúl a lejátszóhoz, csak azt mondja meg, mit kellene
tenni (várni / újracsatlakozni / feladni), és hogy mekkora gyorsítótárral.
Így az idővezérelt viselkedés szimulált órával, VLC nélkül tesztelhető.
"""
import hashlib

# network-caching lépcsők (ms). Stall után a következő lépcsőre lépünk.
CACHE_LADDER_TV = [2000, 3500, 6000, 9000]
CACHE_LADDER_RADIO = [3000, 5000, 8000, 12000]

STALL_TIMEOUT_S = 12.0        # ennyi ideig tartó <100% pufferelés = elakadás
FIRST_CONNECT_TIMEOUT_S = 18  # induláskor ennyit várunk az első képkockára
MAX_AUTO_RETRIES = 4          # egy csatornaválasztásra jutó automatikus próbák
BACKOFF_S = [1.0, 2.0, 4.0, 8.0]
STABLE_AFTER_S = 30.0
SHOW_BUFFER_CARD_AFTER_S = 0.8  # rövidebb pufferelésnél nem villog a spinner


def url_id(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


class StreamSupervisor:
    def __init__(self, learned=None):
        # url_id -> megtanult lépcső-index (stall után feljebb lép)
        self.learned = dict(learned or {})
        self.reset("", False)

    def reset(self, url, is_radio):
        self.url = url
        self.is_radio = is_radio
        self.retries = 0
        self.playing_since = None
        self.buffering_since = None
        self.session_level = None

    # -- gyorsítótár-szint ---------------------------------------------------
    @property
    def ladder(self):
        return CACHE_LADDER_RADIO if self.is_radio else CACHE_LADDER_TV

    def level(self):
        base = self.learned.get(url_id(self.url), 0)
        if self.session_level is not None:
            base = max(base, self.session_level)
        return min(base, len(self.ladder) - 1)

    def cache_ms(self):
        return self.ladder[self.level()]

    def escalate(self):
        new = min(self.level() + 1, len(self.ladder) - 1)
        self.session_level = new
        self.learned[url_id(self.url)] = new
        return self.ladder[new]

    # -- események -----------------------------------------------------------
    def on_buffering(self, pct, now):
        if pct >= 100:
            self.buffering_since = None
            return
        if self.buffering_since is None:
            self.buffering_since = now

    def on_playing(self, now):
        if self.playing_since is None:
            self.playing_since = now
        self.buffering_since = None

    def check(self, now, started_at):
        """Időzítőből hívandó. Visszatér: 'ok' | 'stalled' | 'dead'."""
        if self.playing_since is None:
            if now - started_at > FIRST_CONNECT_TIMEOUT_S:
                return "stalled"
            return "ok"
        if (self.buffering_since is not None
                and now - self.buffering_since > STALL_TIMEOUT_S):
            return "stalled"
        if self.buffering_since is None and now - self.playing_since > STABLE_AFTER_S:
            self.retries = 0   # stabilan megy: új hiba esetén újra van próbálkozási keret
        return "ok"

    def next_action(self, reason):
        """reason: 'stalled' | 'error' | 'ended'.
        Visszatér (action, delay_s, cache_ms) - action: 'retry' | 'giveup'."""
        if self.retries >= MAX_AUTO_RETRIES:
            return ("giveup", 0.0, self.cache_ms())
        delay = BACKOFF_S[min(self.retries, len(BACKOFF_S) - 1)]
        self.retries += 1
        if reason in ("stalled", "ended"):
            cache = self.escalate()
        else:
            cache = self.cache_ms()
        self.playing_since = None
        self.buffering_since = None
        return ("retry", delay, cache)
