# -*- coding: utf-8 -*-
"""YouTube reklámblokkoló és a WebEngine tárolómappa előkészítése."""
import os
from tvbox.compat import QWebEngineUrlRequestInterceptor, logger


# ===========================================================================
# YouTube reklám- és követésblokkoló a beépített QtWebEngine-hez
#
# Ez nem a Brave Shields teljes klónja. A QtWebEngine URL-szinten tud
# kéréseket blokkolni, ezért biztosan reklámhoz/követéshez tartozó domaineket
# és ismert YouTube reklám-végpontokat tiltunk, majd JS-sel eltüntetjük a
# reklám UI-elemeket. A YouTube időről időre változtat, ezért 100%-os,
# örökös garancia nem adható.
#
# FONTOS, FELHASZNÁLÓ ÁLTAL JELENTETT PROBLÉMA MIATTI VÁLTOZÁS: amikor egy
# videóreklám következett volna, a fenti végpontok BLOKKOLÁSA miatt a
# YouTube lejátszója egy ideig SÖTÉT/BERAGADT képernyőt mutatott, mielőtt
# felismerte a hibát és továbblépett a tényleges tartalomra - vagyis a
# reklámblokkoló ebben a konkrét, Leanback/TV-felületen ROSSZABB, zavaróbb
# felhasználói élményt adott, mint maga a reklám. EZÉRT ez a funkció
# Mostantól MINDIG be van kapcsolva (nincs hozzá beállítás) - de csak a beépített
# QtWebEngine-nézetre hat, amit jelenleg a WEB_APP_ORDER = [] kikapcsol. A külön
# Brave-ablakban futó YouTube-ot a Brave saját Shields-e védi.
# ===========================================================================
if QWebEngineUrlRequestInterceptor is not None:
    class YouTubeAdBlockInterceptor(QWebEngineUrlRequestInterceptor):
        BLOCKED_HOSTS = {
            # Klasszikus Google/YouTube hirdetési infrastruktúra.
            "doubleclick.net",
            "googlesyndication.com",
            "googleadservices.com",
            "adservice.google.com",
            "pagead2.googlesyndication.com",
            "ads.youtube.com",
            "ads.google.com",
            "googleads.g.doubleclick.net",
            "securepubads.g.doubleclick.net",
            "tpc.googlesyndication.com",
            "pagead2.googleadservices.com",
        }

        BLOCKED_URL_PARTS = (
            "/pagead/",
            "/api/stats/ads",
            "/ptracking",
            "googleads.g.doubleclick.net",
            "doubleclick.net/pagead",
            "googlesyndication.com/pagead",
        )

        def __init__(self, parent=None):
            super().__init__(parent)
            self.enabled = True

        def set_enabled(self, enabled):
            self.enabled = bool(enabled)

        def interceptRequest(self, info):
            if not self.enabled:
                return
            try:
                url = info.requestUrl().toString()
                host = info.requestUrl().host().lower().rstrip(".")
                if any(host == h or host.endswith("." + h) for h in self.BLOCKED_HOSTS):
                    info.block(True)
                    return
                lower_url = url.lower()
                if any(part in lower_url for part in self.BLOCKED_URL_PARTS):
                    info.block(True)
            except Exception:
                return
else:
    YouTubeAdBlockInterceptor = None


YOUTUBE_ADBLOCK_JS = r"""
(function() {
    const STYLE_ID = 'tvbox-adblock-style';
    const HIDDEN_ATTR = 'data-tvbox-ad-hidden';
    const PLAYER_GUARD_STYLE_ID = 'tvbox-adblock-player-guard';

    // Ezek kifejezetten YouTube-reklám elemek. Nem használunk általános
    // "class contains ad" szabályt, mert az könnyen valódi videó/UI elemeket
    // is elrejthetne.
    const selectors = [
        '#masthead-ad',
        '#player-ads',
        'ytd-display-ad-renderer',
        'ytd-promoted-sparkles-web-renderer',
        'ytd-ad-slot-renderer',
        'ytd-in-feed-ad-layout-renderer',
        'ytd-banner-promo-renderer',
        'ytd-statement-banner-renderer',
        'ytm-promoted-sparkles-web-renderer',
        'ytd-action-companion-ad-renderer',
        '.ytp-ad-overlay-container',
        '.ytp-ad-text-overlay',
        '.ytp-ad-message-container',
        '.ytp-ad-player-overlay',
        '.ytp-ad-skip-button',
        '.ytp-ad-preview-container',
        '.ytp-ad-image-overlay',
        '.ytp-ad-action-interstitial',
        '.ytp-ad-skip-button-modern',
        '.ytp-ad-skip-button-slot',
        '.video-ads'
    ];

    // A CSS azonnal, már a dokumentum létrehozásakor bekerül. Ez sokkal
    // kevésbé engedi, hogy a reklám egyetlen pillanatra felvillanjon.
    function installStyle() {
        if (document.getElementById(STYLE_ID)) return;
        const style = document.createElement('style');
        style.id = STYLE_ID;
        style.textContent = selectors.map(s =>
            s + ' { display:none !important; visibility:hidden !important; opacity:0 !important; }'
        ).join('\n');
        (document.head || document.documentElement).appendChild(style);

        // A reklám első képkockáját se engedjük kirajzolódni. Amíg a YouTube
        // "ad-showing/ad-interrupting" állapotban van, a lejátszó fekete.
        // Ez jobb UX, mint egy 100-300 ms-os reklámvillanás.
        const guard = document.createElement('style');
        guard.id = PLAYER_GUARD_STYLE_ID;
        guard.textContent = `
            #movie_player.ad-showing video,
            #movie_player.ad-interrupting video,
            .html5-video-player.ad-showing video,
            .html5-video-player.ad-interrupting video {
                visibility: hidden !important;
                opacity: 0 !important;
            }
            #movie_player.ad-showing .html5-video-container,
            #movie_player.ad-interrupting .html5-video-container {
                background: #000 !important;
            }
        `;
        (document.head || document.documentElement).appendChild(guard);
    }

    function hideAdNode(el) {
        if (!el || el.nodeType !== 1) return;

        // Elsőként magát a reklámot rejtjük el.
        el.style.setProperty('display', 'none', 'important');
        el.style.setProperty('visibility', 'hidden', 'important');
        el.style.setProperty('opacity', '0', 'important');
        el.setAttribute(HIDDEN_ATTR, '1');

        // A főoldali rácsban a reklám gyakran egy "rich item" belsejében van.
        // A teljes kártyát is elrejtjük, így nem marad lyuk a rácsban.
        const item = el.closest && el.closest(
            'ytd-rich-item-renderer, ytd-grid-video-renderer, ytd-video-renderer'
        );
        if (item) {
            item.style.setProperty('display', 'none', 'important');
            item.setAttribute(HIDDEN_ATTR, '1');
        }

        // In-feed hirdetésnél a teljes ad-layout konténert is eltüntetjük.
        const layout = el.closest && el.closest(
            'ytd-in-feed-ad-layout-renderer, ytd-ad-slot-renderer'
        );
        if (layout) {
            layout.style.setProperty('display', 'none', 'important');
            layout.setAttribute(HIDDEN_ATTR, '1');
        }
    }

    function removeEmptyAdContainers() {
        // Ha egy teljes rich-grid-row csak reklámkártyákból/üres helyekből áll,
        // az egész sort elrejtjük. Így nem marad üres sor a kezdőlapon.
        document.querySelectorAll('ytd-rich-grid-row').forEach(row => {
            const items = Array.from(row.querySelectorAll(':scope > #contents > ytd-rich-item-renderer'));
            if (!items.length) return;
            const visible = items.filter(item => {
                const st = window.getComputedStyle(item);
                return st.display !== 'none' && item.getAttribute(HIDDEN_ATTR) !== '1';
            });
            if (visible.length === 0) {
                row.style.setProperty('display', 'none', 'important');
                row.setAttribute(HIDDEN_ATTR, '1');
            }
        });
    }

    function cleanAds() {
        installStyle();

        for (const selector of selectors) {
            document.querySelectorAll(selector).forEach(hideAdNode);
        }

        // A YouTube SPA újrarenderelheti az oldalt és újra létrehozhatja a
        // reklámkártyát, ezért a gombot mindig megkeressük.
        document.querySelectorAll(
            '.ytp-ad-skip-button, .ytp-ad-skip-button-modern, .ytp-ad-skip-button-slot'
        ).forEach(btn => {
            try { btn.click(); } catch (e) {}
        });

        // Ha mégis elindul egy reklámvideó, azonnal a végére ugrunk, amikor a
        // YouTube már megadta a tényleges duration értéket.
        const video = document.querySelector('video');
        const adShowing = document.querySelector('.ad-showing, .ad-interrupting');
        if (video && adShowing) {
            try {
                // Némítsük el az esetlegesen már elindult reklámot, majd
                // amint a duration ismert, azonnal ugorjunk a végére.
                video.muted = true;
                const duration = Number(video.duration);
                if (Number.isFinite(duration) && duration > 0) {
                    video.currentTime = Math.max(0, duration - 0.05);
                    try { video.play(); } catch (e) {}
                }
            } catch (e) {}
        }

        removeEmptyAdContainers();
    }

    installStyle();
    cleanAds();

    // A YouTube egy SPA: navigációkor nincs teljes oldalbetöltés, csak DOM-
    // változás. Ezért MutationObserver figyeli a frissen létrejövő elemeket.
    if (!window.__tvboxAdBlockObserver) {
        window.__tvboxAdBlockObserver = new MutationObserver(function() {
            if (window.__tvboxAdBlockSweep) return;
            window.__tvboxAdBlockSweep = true;
            requestAnimationFrame(function() {
                window.__tvboxAdBlockSweep = false;
                cleanAds();
            });
        });
        window.__tvboxAdBlockObserver.observe(document.documentElement, {
            subtree: true,
            childList: true
        });
    }

    if (!window.__tvboxAdBlockInterval) {
        // 700 ms túl lassú: ennyi idő alatt egy reklám már látható lehet.
        // 120 ms gyors sweep + MutationObserver adja a két védelmi réteget.
        window.__tvboxAdBlockInterval = setInterval(cleanAds, 120);
    }
})();
"""


# ===========================================================================
# Fő ablak
# ===========================================================================
def _prepare_webengine_storage_dir():
    """A beépített böngésző-nézet (pl. YouTube) SAJÁT, ehhez az
    alkalmazáshoz kötött tárolási mappáját készíti elő - lásd a
    _build_web_view()-nél lévő bővebb magyarázatot arról, miért NEM a
    QtWebEngine implicit "alapértelmezett" profilját használjuk.

    Rendellenes leállás után (összeomlás, kényszerített bezárás, áram-
    kimaradás egy Raspberry Pi-n) a Chromium néha "beragadt" zároló-
    fájlokat hagyhat ebben a mappában, amik a KÖVETKEZŐ indításkor
    megakadályozzák a profil rendes megnyitását - ez a legvalószínűbb
    magyarázat arra, hogy a beépített YouTube-nézet néha összeomlott, ha
    korábban már egyszer megnyitották, majd a programot újraindították
    ("crash után ismét jól megy néha" - pont ez a fajta, zároló-fájltól
    függő, nem-determinisztikus viselkedés jellemző rá). Ezért induláskor
    itt előre eltávolítjuk a jól ismert zároló-fájlokat, MIELŐTT a profil
    egyáltalán létrejönne."""
    storage_dir = os.path.join(os.path.expanduser("~"), ".tvbox", "webengine_profile")
    try:
        os.makedirs(storage_dir, exist_ok=True)
        for lock_name in ("SingletonLock", "SingletonCookie", "SingletonSocket", "lockfile"):
            lock_path = os.path.join(storage_dir, lock_name)
            try:
                if os.path.lexists(lock_path):
                    os.remove(lock_path)
            except OSError as e:
                logger.debug("Nem sikerült eltávolítani a zároló-fájlt (%s): %s", lock_path, e)
    except OSError as e:
        logger.warning("Nem sikerült előkészíteni a webnézet tárolási mappáját: %s", e)
        return None
    return storage_dir
