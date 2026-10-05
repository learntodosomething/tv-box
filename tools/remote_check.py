#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A telefonos távirányító hálózati diagnosztikája (csak a standard könyvtárat használja).

Futtasd, MIKÖZBEN a TV Box fut és a távirányító be van kapcsolva:
    python tools/remote_check.py

Független hálózati teszt (a TV Box nélkül is megy; ha ezt sem éri el a telefon, a gond
a hálózatban/tűzfalban van, nem az alkalmazásban):
    python tools/remote_check.py --serve          # 8000-es port
    python tools/remote_check.py --serve 8123

Kiírja a gép IPv4-címeit (virtuális/VPN kártyák is kiderülnek), megmondja, melyik
porton hallgat a távirányító, és hogy a szabály megvan-e a Windows tűzfalban.
FIGYELEM: a telefon felőli elérést innen nem lehet közvetlenül mérni - lásd a
legalsó tesztet: nyisd meg a kiírt címet a telefonon (token nélkül is betölt az oldal).
"""
import os
import shutil
import socket
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tvbox.remote import DEFAULT_PORT, PORT_TRIES, lan_ip   # noqa: E402


def local_ips():
    ips = {lan_ip()}
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    return sorted(ips)


def port_open(ip, port, timeout=0.4):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return s.connect_ex((ip, port)) == 0
    finally:
        s.close()


def scan(ips, ports):
    """{ip: [nyitott portok]}"""
    return {ip: [p for p in ports if port_open(ip, p)] for ip in ips}


def firewall_rule_present():
    if os.name != "nt":
        return None
    try:
        out = subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", 'name=TV Box Remote'],
                             capture_output=True, text=True, timeout=10)
        return out.returncode == 0 and "TV Box Remote" in out.stdout
    except Exception:
        return None


_PS_DIAG = r'''
$ErrorActionPreference = 'SilentlyContinue'
'--- Halozati profil (Private/Public) ---'
Get-NetConnectionProfile | ForEach-Object { '{0}: {1}' -f $_.InterfaceAlias, $_.NetworkCategory }
'--- Tuzfal profilok (AllowInboundRules=False: MINDEN bejovo kapcsolat tiltva) ---'
Get-NetFirewallProfile | ForEach-Object { '{0}: Enabled={1} AllowInboundRules={2} DefaultInbound={3}' -f $_.Name, $_.Enabled, $_.AllowInboundRules, $_.DefaultInboundAction }
'--- Python-ra vonatkozo TILTO (Block) szabalyok - ezek felulirjak az engedelyezoket ---'
$n = 0
Get-NetFirewallRule -Direction Inbound -Action Block -Enabled True | ForEach-Object {
  $app = ($_ | Get-NetFirewallApplicationFilter).Program
  if ($app -like '*python*') { $n++; '{0} | {1} | profil: {2}' -f $_.DisplayName, $app, $_.Profile }
}
if ($n -eq 0) { 'nincs' }
'--- Vedelmi szoftverek (harmadik felu tuzfal is lehet) ---'
Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | ForEach-Object { $_.displayName }
'''


def has_python_block(ps_output):
    """A PowerShell-kimenet 'TILTO' szakaszában van-e tényleges szabálysor ('nincs' = nincs)."""
    lines = ps_output.splitlines()
    for i, line in enumerate(lines):
        if "TILTO" in line:
            for nxt in lines[i + 1:]:
                nxt = nxt.strip()
                if not nxt:
                    continue
                return not nxt.startswith("---") and nxt != "nincs"
    return False


def windows_diagnostics():
    if os.name != "nt" or not shutil.which("powershell"):
        return
    print("\n===== Windows tűzfal / hálózat részletei =====")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", _PS_DIAG],
                             capture_output=True, text=True, timeout=60, errors="replace")
        print(out.stdout.strip() or "(nincs kimenet)")
        if has_python_block(out.stdout):
            print("\n>>> Python-ra vonatkozó tiltó szabály van! Futtasd: tools/remote_firewall_fix_blocks.bat")
    except Exception as e:  # noqa
        print("A PowerShell-diagnosztika nem futott le:", e)


def serve_plain(port):
    """Egyszerű, a TV Box-tól független szerver: eldönti, hogy a telefon általában eléri-e a gépet."""
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            body = ("<meta name=viewport content='width=device-width'><h1 style='font:700 28px sans-serif'>"
                    "M\u0170K\u00d6DIK \u2705</h1><p>A telefon eléri a gépet a %d-es porton.</p>" % port).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            print("  <- kérés érkezett innen:", self.client_address[0])

        def log_message(self, *a):
            pass

    httpd = ThreadingHTTPServer(("0.0.0.0", port), H)
    ip = lan_ip()
    print("Teszt-szerver fut. Nyisd meg a TELEFONON:  http://%s:%d/" % (ip, port))
    print("  - 'MŰKÖDIK' oldal és a konzolon megjelenik a telefon címe:  a hálózat/tűzfal rendben van,")
    print("    a gond a TV Box 8765-ös portjára vonatkozó szabályban van")
    print("  - nem tölt be:  tűzfal (python.exe tiltó szabály), vendég-Wi-Fi / eszközök elkülönítése")
    print("    a routeren, VPN, vagy a telefon nem ugyanazon a hálózaton van")
    print("  (kilépés: Ctrl+C)\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--serve":
        serve_plain(int(sys.argv[2]) if len(sys.argv) > 2 else 8000)
        return 0
    ports = list(range(DEFAULT_PORT, DEFAULT_PORT + PORT_TRIES))
    ips = local_ips()
    print("A gép IPv4-címei:", ", ".join(ips))
    print("Az alapértelmezett (útvonal szerinti) cím:", lan_ip(), "\n")
    result = scan(ips, ports)
    found = [(ip, p) for ip, ps in result.items() for p in ps]
    if not found:
        print("NEM hallgat senki a %d-%d portokon. Fut a TV Box, és be van kapcsolva a" % (ports[0], ports[-1]))
        print("Beállítások -> Telefonos távirányító?")
        return 1
    # a telefonnak nem jó a loopback cím: a hálózati címeket tesszük előre
    found.sort(key=lambda t: (t[0].startswith("127."), t[0] != lan_ip(), t[0], t[1]))
    for ip, p in found:
        print("OK  a távirányító hallgat:  http://%s:%d/%s" % (ip, p, "   (csak ezen a gépen érhető el)" if ip.startswith("127.") else ""))
    if all(ip.startswith("127.") for ip, _ in found):
        print("\nCsak loopbacken hallgat - nincs használható hálózati cím. Csatlakozik a gép Wi-Fi-hez/vezetékes hálózathoz?")
        return 1
    rule = firewall_rule_present()
    print()
    if rule is True:
        print("Windows tűzfal: a 'TV Box Remote' szabály megvan.")
    elif rule is False:
        print("Windows tűzfal: NINCS 'TV Box Remote' szabály. Ha a telefon nem éri el az oldalt,")
        print("futtasd a tools/remote_firewall_windows.bat fájlt (rendszergazdaként).")
    windows_diagnostics()
    print("\nTELEFONOS TESZT: nyisd meg a telefon böngészőjében ezt (token nélkül is betölt):")
    print("   http://%s:%d/" % (found[0][0], found[0][1]))
    print("  - betölt (hibaüzenettel a tetején): a hálózat rendben, a QR-kód tokenje a gond -> olvasd be újra")
    print("  - nem tölt be:  tűzfal, vendég-Wi-Fi (eszközök elkülönítve), mobilnet bekapcsolva, vagy más hálózat")
    print("    -> a pontos hibaüzenetet nézd meg a telefonon (időtúllépés = eldobott csomag: tűzfal/elkülönítés;")
    print("       'kapcsolat elutasítva' = elérte a gépet, de ott nem hallgat semmi)")
    print("    -> független teszt:  python tools/remote_check.py --serve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
