# -*- coding: utf-8 -*-
"""Teszt-segéd: szintetikus XMLTV fájl gyártása (az EPG-tesztekhez és a stressz-teszthez)."""
import gzip
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

TITLES = ["Híradó", "Időjárás", "Reggeli", "Sorozat: Szomszédok", "Film: A kincskereső", "Sport összefoglaló",
          "Dokumentum: Vadvilág", "Zenés műsor", "Gyerekeknek: Mese", "Éjszakai ismétlés", "Talk show", "Krimi",
          "Árvíz & vihar <különkiadás>", "Ünnepi \"gála\""]


def xmltv_time(ts, tz_hours=2):
    tz = timezone(timedelta(hours=tz_hours))
    dt = datetime.fromtimestamp(ts, tz)
    return dt.strftime("%Y%m%d%H%M%S") + " %s%02d00" % ("+" if tz_hours >= 0 else "-", abs(tz_hours))


def make_xmltv(path, channel_names, hours_back=6, hours_fwd=48, step_minutes=30, gz=False,
               extra_channels=0, tz_hours=2, seed=1, use_ids_only=False, now=None):
    """Egy XMLTV fájlt ír. `channel_names`: a megadott nevű csatornák (display-name),
    `extra_channels`: ennyi további, nem használt csatorna (tömeg-teszthez)."""
    rnd = random.Random(seed)
    now = time.time() if now is None else now
    start0 = (int(now) // 1800) * 1800 - hours_back * 3600
    n_steps = int((hours_back + hours_fwd) * 60 / step_minutes)
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv generator-info-name="tvbox-test">']
    all_ch = [("ch%d.hu" % i, name) for i, name in enumerate(channel_names)]
    all_ch += [("extra%d.example" % i, "Extra csatorna %d" % i) for i in range(extra_channels)]
    for cid, name in all_ch:
        if use_ids_only:
            lines.append('<channel id="%s"/>' % escape(cid))
        else:
            lines.append('<channel id="%s"><display-name lang="hu">%s</display-name></channel>' % (escape(cid), escape(name)))
    count = 0
    for cid, name in all_ch:
        for i in range(n_steps):
            st = start0 + i * step_minutes * 60
            en = st + step_minutes * 60
            title = rnd.choice(TITLES)
            lines.append('<programme start="%s" stop="%s" channel="%s"><title lang="hu">%s</title>'
                         '<desc lang="hu">%s</desc></programme>'
                         % (xmltv_time(st, tz_hours), xmltv_time(en, tz_hours), escape(cid),
                            escape(title), escape("Leírás " + title)))
            count += 1
    lines.append("</tv>")
    data = "\n".join(lines).encode("utf-8")
    if gz:
        with gzip.open(path, "wb") as f:
            f.write(data)
    else:
        with open(path, "wb") as f:
            f.write(data)
    return count
