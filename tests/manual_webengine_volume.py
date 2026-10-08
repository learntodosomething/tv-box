"""KÉZI teszt a beépített YouTube hangerejéhez: valódi QtWebEngine, helyi <video> oldal.
Kell hozzá: PyQtWebEngine, ffmpeg és egy kijelző (pl. xvfb-run -a -s "-screen 0 1280x720x24" python3 tests/manual_webengine_volume.py).
A YouTube élő oldala helyett egy helyi oldalt tölt be, így internet nélkül is fut.
Megjegyzés: ha PyQtWebEngine telepítve van, az offscreen platform nem elég (nincs OpenGL) - a többi teszt
(test_power_dim_settings, stress_test) ilyenkor szintén kijelzőt igényel."""
import sys, os, json, threading, time, http.server, socketserver, urllib.request, tempfile, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
SITE = tempfile.mkdtemp()
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=white:s=640x360:r=25", "-t", "40",
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", os.path.join(SITE, "white.mp4")], check=True)
open(os.path.join(SITE, "index.html"), "w").write('<html><body style="margin:0"><video src="white.mp4" autoplay loop muted style="width:100%"></video></body></html>')
os.environ["HOME"] = tempfile.mkdtemp()
os.environ["QTWEBENGINE_DISABLE_SANDBOX"]="1"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"]="--no-sandbox --disable-gpu --autoplay-policy=no-user-gesture-required"
import tvbox.config as cfg
cfg.CONFIG_PATH=os.path.join(os.environ['HOME'],'s.json')
os.environ.pop("TVBOX_EPG", None)
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s,*a,**k): super().__init__(*a,directory=SITE,**k)
    def log_message(s,*a): pass
class TS(socketserver.ThreadingMixIn, http.server.HTTPServer): daemon_threads=True
srv=TS(("127.0.0.1",0),H); threading.Thread(target=srv.serve_forever,daemon=True).start()
import tvbox.external_apps as ea
ea.WEB_APPS["youtube"]["url"]="http://127.0.0.1:%d/index.html" % srv.server_address[1]
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import QCoreApplication, Qt
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
app=QApplication([])
import tvbox.app as A
print("EMBEDDED_WEB_ENABLED:", A.EMBEDDED_WEB_ENABLED)
w=A.TVBox(); w.resize(1280,720); w.show(); QTest.qWait(2000)
srvr=w._remote_server
def call(path, body=None):
    req=urllib.request.Request("http://127.0.0.1:%d%s"%(srvr.port,path), data=json.dumps(body).encode() if body is not None else None,
        headers={"X-Token":srvr.token,"Content-Type":"application/json"}, method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req,timeout=5) as r: return json.loads(r.read())
def hcall(path, body=None):
    out={}; t=threading.Thread(target=lambda: out.update(r=call(path,body))); t.start()
    while t.is_alive(): QTest.qWait(20)
    return out["r"]
w._show_web_app("youtube"); QTest.qWait(5000)
print("active_web_app:", w.active_web_app, "| view url:", w.web_view.url().toString()[:40])
w.web_view.page().runJavaScript("var v=document.querySelector('video'); v.muted=false; v.volume=0.4; 1;"); QTest.qWait(300)
QTest.qWait(1500)
st=hcall("/api/state"); print("state volume/scope/muted:", st["volume"], st["vol_scope"], st["muted"], "| VLC volume is", w.volume)
hcall("/api/cmd",{"cmd":"volume","delta":5}); QTest.qWait(600)
st=hcall("/api/state"); print("after +5:", st["volume"], "| OSD visible:", w.volume_osd.isVisible(), "| OSD text:", w.volume_value.text())
w.volume_osd.grab().save("/tmp/osd_web.png")
hcall("/api/cmd",{"cmd":"volume","delta":-15}); QTest.qWait(600)
st=hcall("/api/state"); print("after -15:", st["volume"], "| OSD text:", w.volume_value.text())
hcall("/api/cmd",{"cmd":"mute"}); QTest.qWait(600)
st=hcall("/api/state"); print("after mute:", st["muted"], "| OSD caption:", w.volume_caption.text())
w.web_view.page().runJavaScript("document.querySelector('video').volume=0.9;document.querySelector('video').muted=false;1;"); QTest.qWait(2500)
st=hcall("/api/state"); print("changed inside page -> phone sees:", st["volume"], st["muted"])
# standby while embedded YouTube is active
w._screen_power=lambda on: None
hcall("/api/cmd",{"cmd":"power","state":"off","held":2000}); QTest.qWait(500)
print("standby:", w.standby, "| web app left:", w.active_web_app)
hcall("/api/cmd",{"cmd":"power","state":"on","held":2000}); QTest.qWait(800)
print("woke:", not w.standby)
w.close()
