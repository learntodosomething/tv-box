#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Csatorna-diagnosztika: melyik adás pufferel és MIÉRT.

Csak a Python standard könyvtárát használja (VLC/Qt nem kell).
Futtatás a projekt gyökeréből:
    python tools/stream_probe.py                 # minden csatorna (TV + rádió)
    python tools/stream_probe.py --only radio    # csak rádió
    python tools/stream_probe.py --workers 1     # pontosabb sávszél-mérés
    python tools/stream_probe.py --json out.json

Mérőszám HLS-nél: "valós idejű tényező" = (letöltött szegmens hossza) /
(letöltés ideje). 1.0 alatt a szerver lassabb a lejátszásnál => biztosan
pufferel. 1.0-1.5 között határeset (kis hálózati ingadozásra is elakad).
"""
import argparse, json, os, re, sys, time
import urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
UA = "Mozilla/5.0 (tvbox-probe)"


def _open(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout)


def parse_master(text, base):
    """Master playlistből (sávszél, URL) lista."""
    out, lines = [], text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("#EXT-X-STREAM-INF"):
            m = re.search(r"BANDWIDTH=(\d+)", ln)
            bw = int(m.group(1)) if m else 0
            for nxt in lines[i + 1:]:
                if nxt and not nxt.startswith("#"):
                    out.append((bw, urllib.parse.urljoin(base, nxt.strip())))
                    break
    return out


def parse_media(text, base):
    """Media playlistből (targetduration, media_sequence, [(dur, url)])."""
    td, seq, segs, dur = 0.0, 0, [], None
    for ln in text.splitlines():
        if ln.startswith("#EXT-X-TARGETDURATION:"):
            td = float(ln.split(":")[1])
        elif ln.startswith("#EXT-X-MEDIA-SEQUENCE:"):
            seq = int(ln.split(":")[1])
        elif ln.startswith("#EXTINF:"):
            dur = float(ln.split(":")[1].split(",")[0])
        elif ln and not ln.startswith("#") and dur is not None:
            segs.append((dur, urllib.parse.urljoin(base, ln.strip())))
            dur = None
    return td, seq, segs


def probe_hls(url, timeout=8):
    r = {"kind": "hls"}
    t0 = time.time()
    with _open(url, timeout) as resp:
        text = resp.read(400_000).decode("utf-8", "replace")
    r["playlist_s"] = round(time.time() - t0, 2)
    if "#EXTM3U" not in text:
        raise ValueError("nem m3u8")
    base = url
    variants = parse_master(text, url)
    if variants:
        r["variants"] = len(variants)
        bw, vurl = sorted(variants)[len(variants) // 2 if len(variants) > 2 else 0]
        r["picked_kbps"] = bw // 1000
        with _open(vurl, timeout) as resp:
            text = resp.read(400_000).decode("utf-8", "replace")
        base = vurl
    td, seq1, segs = parse_media(text, base)
    if not segs:
        raise ValueError("üres szegmenslista")
    r["target_s"] = td
    # frissesség: halad-e az élő lista?
    time.sleep(min(max(td, 2), 6))
    with _open(base, timeout) as resp:
        _, seq2, _ = parse_media(resp.read(400_000).decode("utf-8", "replace"), base)
    r["live_advancing"] = seq2 > seq1
    # az utolsó 2 szegmens letöltése
    ratios, ttfbs = [], []
    for dur, surl in segs[-2:]:
        t1 = time.time()
        with _open(surl, timeout + 10) as resp:
            first = resp.read(1)
            ttfbs.append(time.time() - t1)
            n = len(first) + len(resp.read())
        dt = max(time.time() - t1, 1e-3)
        ratios.append(dur / dt)
    r["realtime_x"] = round(min(ratios), 2)
    r["ttfb_s"] = round(max(ttfbs), 2)
    return r


def probe_audio(url, seconds=5, timeout=8):
    r = {"kind": "audio"}
    t0 = time.time()
    with _open(url, timeout) as resp:
        r["ttfb_s"] = round(time.time() - t0, 2)
        br = resp.headers.get("icy-br")
        nominal = int(br.split(",")[0]) if br and br.split(",")[0].isdigit() else None
        got, t1 = 0, time.time()
        while time.time() - t1 < seconds:
            chunk = resp.read(8192)
            if not chunk:
                break
            got += len(chunk)
        dt = max(time.time() - t1, 1e-3)
    kbps = got * 8 / dt / 1000
    r["kbps"] = round(kbps)
    r["nominal_kbps"] = nominal or 128
    r["realtime_x"] = round(kbps / r["nominal_kbps"], 2)   # induló burst miatt >=1 normális
    return r


def probe(entry):
    mode, key, name, url = entry
    try:
        is_hls = ".m3u8" in url.lower() or "playlist" in url.lower()
        r = probe_hls(url) if is_hls else probe_audio(url)
        r["error"] = None
    except Exception as e:  # noqa
        r = {"kind": "?", "error": "%s: %s" % (type(e).__name__, str(e)[:70])}
    r.update(mode=mode, key=key, name=name, url=url)
    return r


def verdict(r):
    if r["error"]:
        return "HALOTT"
    x, ttfb = r.get("realtime_x", 0), r.get("ttfb_s", 0)
    if r["kind"] == "hls" and not r.get("live_advancing", True):
        return "ELAKADT (az élő lista nem halad)"
    if x < 1.0:
        return "LASSÚ (pufferelni fog)"
    if x < 1.5 or ttfb > 3:
        return "HATÁRESET"
    return "OK"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["tv", "radio"])
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--json")
    a = ap.parse_args()
    from tvbox.channels import SOURCES, _build_source_state
    entries = []
    for mode, _i, _l, _t, _u, data in SOURCES:
        if a.only and a.only != mode:
            continue
        for key, (name, url) in _build_source_state(data)["channels"].items():
            entries.append((mode, key, name, url))
    print("Vizsgálat: %d adás, %d párhuzamos szál ...\n" % (len(entries), a.workers))
    with ThreadPoolExecutor(a.workers) as ex:
        results = list(ex.map(probe, entries))
    order = {"HALOTT": 0, "ELAKADT": 1, "LASSÚ": 2, "HATÁRESET": 3, "OK": 4}
    for r in results:
        r["verdict"] = verdict(r)
    results.sort(key=lambda r: (order.get(r["verdict"].split(" ")[0], 5), r.get("realtime_x", 0)))
    print("%-9s %-4s %-26s %-8s %-7s %s" % ("ÍTÉLET", "SZ.", "NÉV", "RT-x", "TTFB", "megjegyzés"))
    for r in results:
        print("%-9s %-4s %-26s %-8s %-7s %s" % (
            r["verdict"].split(" ")[0], r["mode"][0] + r["key"], r["name"][:26],
            r.get("realtime_x", "-"), r.get("ttfb_s", "-"), r["error"] or ""))
    bad = [r for r in results if r["verdict"] != "OK"]
    print("\nÖsszesen %d/%d nem OK. (RT-x: 1.0 alatt a szerver lassabb a lejátszásnál.)" % (len(bad), len(results)))
    if a.json:
        json.dump(results, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
