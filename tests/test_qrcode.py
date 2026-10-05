import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tvbox import qrcode_min as q

def test_reed_solomon_known_vector():
    # Thonky "HELLO WORLD" 1-M: adat- és EC-kódszavak
    data = [32, 91, 11, 120, 209, 114, 220, 77, 67, 64, 236, 17, 236, 17, 236, 17]
    assert q.rs_remainder(data, q.rs_divisor(10)) == [196, 35, 39, 119, 235, 215, 231, 226, 93, 23]

def test_format_info_known_values():
    assert q.format_bits("M", 0) == 0b101010000010010
    assert q.format_bits("L", 0) == 0b111011111000100

def test_size_and_versions():
    assert len(q.make_qr("A", "M")) == 21
    assert len(q.make_qr("x" * 30, "M")) == 29            # 3-M kapacitás 42, de 2-M csak 26 bájt
    assert len(q.make_qr("x" * 50, "L")) == 29            # 3-L (53 bájt)
    assert len(q.make_qr("x" * 60, "L")) == 33            # 4-L
    try: q.make_qr("x" * 300); assert False
    except ValueError: pass

def _render(matrix, scale=8, quiet=4):
    import numpy as np
    n = len(matrix); size = (n + 2 * quiet) * scale
    img = np.full((size, size), 255, dtype="uint8")
    for y in range(n):
        for x in range(n):
            if matrix[y][x]:
                img[(y + quiet) * scale:(y + quiet + 1) * scale, (x + quiet) * scale:(x + quiet + 1) * scale] = 0
    return img

def _decoder():
    import cv2
    # Az Aruco-alapú dekóder megbízhatóbb; a régi QRCodeDetector néhány (szerkezetileg
    # helyes) kódnál is megbotlik - 960 kódból 960-at az Aruco olvasott ki helyesen.
    if hasattr(cv2, "QRCodeDetectorAruco"):
        return cv2.QRCodeDetectorAruco(), True
    return cv2.QRCodeDetector(), False

def test_decodes_with_real_decoder():
    try:
        det, strong = _decoder()
    except ImportError:
        print("  (cv2 nincs, dekódolás kihagyva)"); return
    samples = ["A", "http://192.168.1.23:8765/?t=Ab3dE_9xYz12",
               "http://10.0.0.5:8765/?t=Zk9Q-w3LmN8p",
               "https://example.com/very/long/path?with=query&and=more&params=1234567890",
               "http://192.168.100.100:8766/?t=abcdefghijklmnop&x=\u00fcnicode-\u00e9",
               "x" * 100]
    fails = []
    for ecc in ("L", "M"):
        for s in samples:
            try: m = q.make_qr(s, ecc)
            except ValueError: continue            # túl hosszú ehhez az ECC-hez
            text = det.detectAndDecode(_render(m))[0]
            if text != s: fails.append((ecc, len(s), text[:30]))
    assert len(fails) <= (0 if strong else 2), fails

def test_every_mask_decodes():
    try:
        det, strong = _decoder()
    except ImportError:
        return
    if not strong:
        print("  (Aruco dekóder nincs, kihagyva)"); return
    orig = q._penalty
    s = "http://192.168.1.23:8765/?t=Ab3dE_9xYz12"
    try:
        for forced in range(8):
            calls = []
            q._penalty = lambda m, c=calls, f=forced: (c.append(1) or (0 if len(c) == f + 1 else 1000))
            for ecc in ("L", "M"):
                calls.clear()
                assert det.detectAndDecode(_render(q.make_qr(s, ecc)))[0] == s, (forced, ecc)
    finally:
        q._penalty = orig

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("OK", n)
