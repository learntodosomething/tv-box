import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import remote_check as rc

def test_block_rule_detection():
    none = "--- Halozati profil ---\nEth: Private\n--- Python-ra vonatkozo TILTO (Block) szabalyok - ezek ... ---\nnincs\n--- Vedelmi szoftverek ---\nDefender"
    some = none.replace("\nnincs\n", "\npython.exe | C:\\Python313\\python.exe | profil: Public\n")
    assert rc.has_python_block(none) is False
    assert rc.has_python_block(some) is True
    assert rc.has_python_block("") is False
    assert rc.has_python_block("--- TILTO ---\n--- Vedelmi ---") is False

def test_scan_finds_open_port_only_on_listening_ip():
    import socket
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1); port = srv.getsockname()[1]
    try:
        res = rc.scan(["127.0.0.1"], [port, port + 1 if port < 65535 else port - 1])
        assert res["127.0.0.1"] == [port]
    finally: srv.close()

if __name__ == "__main__":
    test_block_rule_detection(); print("OK test_block_rule_detection")
    test_scan_finds_open_port_only_on_listening_ip(); print("OK test_scan_finds_open_port_only_on_listening_ip")
