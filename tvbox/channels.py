# -*- coding: utf-8 -*-
"""Csatorna- és rádiólisták, forrás-állapot."""



# ===========================================================================
# Csatorna- / adólisták
# ===========================================================================
CHANNEL_DATA = [
    ("Közszolgálati", [
        ("M1", "http://88.212.15.19/live/test_m_1_hungary_1200_atk/playlist.m3u8"),
        ("M2 / Petőfi TV", "http://88.212.15.19/live/m2_hun/index.m3u8"),
        ("M5", "http://88.212.15.19/live/test_m_5_hun_atk_1200/playlist.m3u8"),
        ("Duna TV", "http://88.212.15.19/live/duna_hun/index.m3u8"),
        ("Duna World", "http://88.212.15.19/live/duna_world_hun/index.m3u8"),
    ]),
    ("Fő kereskedelmi csatornák", [
        ("RTL", "http://88.212.15.19/live/test_rtl_klub_hungary_1200_atk/playlist.m3u8"),
        ("TV2", "http://88.212.15.19/live/test_tv_2_hungary_1200_atk/playlist.m3u8"),
        ("ATV", "http://88.212.15.19/live/test_atv_hungary_1200_atk/playlist.m3u8"),
        ("Viasat 6", "http://88.212.15.19/live/viasat6/index.m3u8"),
        ("AMC", "http://88.212.15.19/live/amc_hun/index.m3u8"),
        ("Dikh TV", "http://88.212.15.19/live/dikh/index.m3u8"),
        # --- ÚJ (v16): további fő kereskedelmi csatornák ---
        ("Prime", "http://88.212.15.19/live/prime/index.m3u8"),
        ("Super TV2", "http://88.212.15.19/live/test_super_tv2_hungary_1200_atk/playlist.m3u8"),
        ("TV4", "http://88.212.15.19/live/test_tv_4_hun_atk_1200/playlist.m3u8"),
    ]),
    ("Mese / Gyerek", [
        ("ducktv HD", "https://dash3.antik.sk/live/duck_tv/index.m3u8"),
        ("Minimax", "http://88.212.15.19/live/minimax_hun/index.m3u8"),
        ("JimJam", "http://88.212.15.19/live/jim_jam_hun/index.m3u8"),
        ("Nick Jr.", "http://88.212.15.19/live/nick_junior_hun/index.m3u8"),
        ("Nicktoons", "http://88.212.15.19/live/nicktoons_hungary/index.m3u8"),
        ("Nickelodeon", "http://88.212.15.19/live/test_nickelodeon_hu_1200_atk/playlist.m3u8"),
        ("Disney Channel", "http://88.212.15.19/live/disney_channel_hun/index.m3u8"),
        ("TV2 Kids", "http://88.212.15.19/live/tv2_kids/index.m3u8"),
        # --- ÚJ (v16) ---
        ("Kölyökklub", "http://88.212.15.19/live/kolyokklub_atk/index.m3u8"),
    ]),
    ("Film", [
        ("Film+", "http://88.212.15.19/live/film_plus_hun_atk/index.m3u8"),
        ("Mozi+", "http://88.212.15.19/live/mozi_plusz/index.m3u8"),
        ("Film Café", "http://88.212.15.19/live/film_cafe/index.m3u8"),
        ("Film4", "http://88.212.15.19/live/film4_hun/index.m3u8"),
        ("Magyar Mozi TV", "http://88.212.15.19/live/mozi/index.m3u8"),
        ("Moziklub", "http://88.212.15.19/live/moziklub_atk/index.m3u8"),
        ("Moziverzum", "http://88.212.15.19/live/moziverzum/index.m3u8"),
    ]),
    ("Tudomány / Dokumentum / Bűnügyi", [
        ("Crime + Investigation", "http://88.212.15.19/live/test_cai_hevc/playlist.m3u8"),
        ("National Geographic", "http://88.212.15.19/live/ngc_hun/index.m3u8"),
        ("National Geographic Wild", "http://88.212.15.19/live/ngw_hun/index.m3u8"),
        ("Spektrum", "http://88.212.15.19/live/spektrum_hun/index.m3u8"),
        ("Spektrum Home", "http://88.212.15.19/live/spektrum_home_hun/index.m3u8"),
        ("History", "http://88.212.15.19/live/history_hun/index.m3u8"),
        ("BBC Earth Hungary", "http://88.212.15.19/live/bbce_hun/index.m3u8"),
        # --- ÚJ (v16): további dokumentum / valóság ---

        ("Life TV", "http://88.212.15.19/live/lifetv/index.m3u8"),
    ]),
    ("Szórakoztató / Sorozat", [
        ("Viasat 2", "http://88.212.15.19/live/viasat2/index.m3u8"),
        ("Viasat 3", "http://88.212.15.19/live/viasat3/index.m3u8"),
        ("AXN", "http://88.212.15.19/live/axn_hun/index.m3u8"),
        ("TV2 Comedy", "http://88.212.15.19/live/tv2_comedy/index.m3u8"),
        ("FEM3", "http://88.212.15.19/live/test_fem3_atktv/playlist.m3u8"),
        ("RTL Kettő", "http://88.212.15.19/live/test_rtl2_hungary_1200_atk/playlist.m3u8"),
        ("RTL+ / RTL Három", "http://88.212.15.19/live/test_rtl_plus_hungary_1200_atk/playlist.m3u8"),
        ("RTL Otthon", "http://88.212.15.19/live/rtl_otthon_atk/index.m3u8"),
        # --- ÚJ (v16): sorozatcsatornák ---
        ("Izaura TV", "http://88.212.15.19/live/izaura/index.m3u8"),
        ("Sorozat+", "http://88.212.15.19/live/test_sorozat_hungary_1200_atk/playlist.m3u8"),
        ("Sorozatklub", "http://88.212.15.19/live/sorozatklub_atk/index.m3u8"),
        ("Story4", "http://88.212.15.19/live/test_story_4_atk_1200/playlist.m3u8"),
    ]),
    ("Életmód / Gasztro", [
        ("TV Paprika", "http://88.212.15.19/live/parpika_hun/index.m3u8"),
    ]),
    ("Zene", [
        ("Music Box Hits", "http://88.212.15.19/live/mb_hits/index.m3u8"),
        ("Music Box Classic", "http://88.212.15.19/live/mb_classic/index.m3u8"),
        ("Music Box Dance", "http://88.212.15.19/live/mb_dance/index.m3u8"),
        # --- ÚJ (v16) ---
        ("Slager TV", "http://88.212.15.19/live/test_slager_tv_hungary_1200_atk/playlist.m3u8"),
        ("Zenebutik", "http://88.212.15.19/live/zenebutik/index.m3u8"),
        ("Muzsika TV", "http://88.212.15.19/live/test_muzsika_hungary_1200_atk/playlist.m3u8"),
        ("Dance Television", "https://m1b2.worldcast.tv/dancetelevisionone/2/dancetelevisionone.m3u8"),
    ]),
    ("24/7 csatornák", [
        ("Mr. Bean Animation",
         "https://amg00627-amg00627c29-rakuten-it-3989.playouts.now.amagi.tv/playlist/"
         "amg00627-banijayfast-mrbeanitcc-rakutenit/playlist.m3u8"),
        ("Mr. Bean Live Action",
         "https://amg00627-amg00627c40-rakuten-uk-5725.playouts.now.amagi.tv/playlist/"
         "amg00627-banijayfast-mrbeanpopupcc-rakutenuk/playlist.m3u8"),
        ("SpongeBob", "https://jmp2.uk/plu-63f87d057533d80008ab9549.m3u8"),
    ]),
    # --- ÚJ (v16): sport csatornák ---
    ("Sport", [
        ("Sport 1", "http://88.212.15.19/live/sport1_hun/index.m3u8"),
        ("Sport 2", "http://88.212.15.19/live/sport2_hun/index.m3u8"),
        ("Spiler1", "http://88.212.15.19/live/spiler1/index.m3u8"),
        ("Spiler2", "http://88.212.15.19/live/spiler2/index.m3u8"),
    ]),
    # --- ÚJ (v16): egyéb / regionális / külföldi ---
    ("Egyéb / Regionális", [
        ("Ozone TV", "http://88.212.15.19/live/ozone/index.m3u8"),
        ("TV7 Békéscsaba", "https://stream.y5.hu/stream/stream_bekescsaba/stream.m3u8"),
        ("Kanal1 (SK)", "https://dash.antik.sk/live/test_upnetwork/playlist.m3u8"),
        ("NOE TV", "https://n105.quickmedia.tv/noetv/live/noetv/Ifd4_1_4/chunks_dvr_timeshift-0-7200.m3u8"),
        ("TV Barrandov (cseh)", "http://88.212.15.19/live/test_barrandov/playlist.m3u8"),
        # A "fb_premium_hungary" elnevezés a forrás-URL-ből lett kikövetkeztetve,
        # a pontos csatornanevet érdemes ellenőrizni lejátszás közben.
        ("FB Premium (HU)", "http://88.212.15.19/live/fb_premium_hungary/index.m3u8"),
        ("MTV (USA)", "http://23.237.104.106:8080/USA_MTV/index.m3u8"),
        # --- ÚJ (v17): további HU közéleti / helyi TV-k (nem IPTV-szolgáltatói,
        # hanem a saját üzemeltetőik által közvetlenül nyújtott HLS-stream-ek) ---
        ("Balaton TV", "https://stream.iptvservice.eu/hls/balatontv.m3u8"),
    ]),
    ("Szlovák csatornák", [
        ("Markíza KRIMI", "http://88.212.15.19/live/test_markiza_krimi_hevc/playlist.m3u8"),
        ("Markíza KLASIK", "https://cdnsk003.panaccess.com/local/Markiza_Klasik/index.m3u8"),
        ("JOJ", "http://88.212.15.19/live/test_joj_25p/playlist.m3u8"),
        ("JOJ Plus", "http://88.212.15.19/live/test_pluska_25p/playlist.m3u8"),
        ("Doma", "http://88.212.15.19/live/test_doma_hd_hevc/playlist.m3u8"),
        ("Dajto", "http://88.212.15.19/live/test_dajto_25p/playlist.m3u8"),
        # --- ÚJ (v16): további szlovák csatornák (RTVS közszolgálati + kereskedelmi) ---
        ("Jednotka (RTVS)", "http://88.212.15.19/live/test_jednotka_25p/playlist.m3u8"),
        ("Dvojka (RTVS)", "http://88.212.15.19/live/test_dvojka_25p/playlist.m3u8"),
        ("Prima Cool SK", "http://88.212.15.19/live/prima_cool_avc_25p/playlist.m3u8"),
        ("Prima Krimi SK", "http://88.212.15.19/live/prima_krimi_avc_25p/playlist.m3u8"),
    ]),
]


RADIO_DATA = [
    ("Rádióadók", [
        ("Klubrádió", "https://stream.klubradio.hu:8443/bpstream"),
        ("Rádió 1", "https://icast.connectmedia.hu/5201/live.mp3"),
        # --- ÚJ (v16): további magyar rádióadók ---
        ("Retro Rádió", "https://icast.connectmedia.hu/5001/live.mp3"),
        ("Kossuth Rádió", "https://icast.connectmedia.hu/4724/mr1ex.aac"),
        # A lista.txt végén szereplő, névtelen "mr2.mp3" adó azonosítása
        # alapján ez a Petőfi Rádió (MR2) hivatalos adása.
        ("Petőfi Rádió", "https://icast.connectmedia.hu/4738/mr2.mp3"),
        ("MegaDance Rádió", "https://gamershouse.hu:8080/livemega.mp3"),
        ("Oxygen Music Radio", "https://oxygenmusic.hu:8443/oxygenmusic_128"),
        ("Mercy Rádió", "http://stream.mercyradio.eu:80/mercyradio.mp3"),
    ]),
    # --- ÚJ (v17): szlovák rádióadók, kb. 28 db, a legnépszerűbb
    # közszolgálati (RTVS/Rádio a Rozhlas Slovenska) és kereskedelmi
    # adóktól. Forrás: a szlovák rádiók saját (RTVS, Bauer Media, Radio
    # Group stb.) nyilvános icecast/shoutcast stream-ei. ---
    ("🇸🇰 Szlovák rádióadók", [
        ("Rádio Slovensko (RTVS)", "http://live.slovakradio.sk:8000/Slovensko_128.mp3"),
        ("Rádio Devín (RTVS)", "http://live.slovakradio.sk:8000/Devin_256.mp3"),
        ("Rádio_FM (RTVS)", "http://live.slovakradio.sk:8000/FM_128.mp3"),
        ("Rádio Regina Západ (RTVS)", "http://icecast.stv.livebox.sk/regina-ba_128.mp3"),
        ("Rádio Slovakia International", "http://icecast.stv.livebox.sk/rsi_128.mp3"),
        ("Rádio Patria (RTVS)", "http://icecast.stv.livebox.sk/patria_128.mp3"),
        ("Rádio Litera (RTVS)", "http://icecast.stv.livebox.sk/litera_128.mp3"),
        ("Fun Rádio", "http://stream.funradio.sk:8000/fun128.mp3"),
        ("Fun Rádio Dance", "http://stream.funradio.sk:8000/dance128.mp3"),
        ("Fun Rádio 80-90 roky", "http://stream.funradio.sk:8000/80-90-128.mp3"),
        ("Rádio Vlna", "http://stream.radiovlna.sk/vlna-hi.mp3"),
        ("Rádio Lumen", "http://audio.lumen.sk:8000/live128.mp3"),
        ("Rádio Viva Metropol", "http://stream.sepia.sk:8000/viva128.mp3"),
    ]),
]


# Elérhető FORRÁSOK, ebben a sorrendben jelennek meg a "B" menüben.
# Tuple: (mode_key, ikon, megjelenített név, menü-cím, mértékegység-szó, adatok)
# Új forrás (pl. YouTube, böngésző) hozzáadásához csak ide kell egy új sort
# írni - a menü, a számbeírás, a mentés/betöltés mind automatikusan kezeli.
SOURCES = [
    ("tv", "📺", "Televízió", "TV csatornák", "csatorna", CHANNEL_DATA),
    ("radio", "📻", "Rádió", "Rádióadók", "adó", RADIO_DATA),
]


def _build_source_state(data):
    """Egy forrás (pl. CHANNEL_DATA) kategóriákra bontott, sorszámozott
    csatorna-állapotát építi fel."""
    channels = {}
    categories = []
    counter = 1
    for category_name, entries in data:
        keys = []
        for name, url in entries:
            key = str(counter)
            channels[key] = (name, url)
            keys.append(key)
            counter += 1
        categories.append((category_name, keys))
    return {"channels": channels, "categories": categories, "keys": list(channels.keys())}
