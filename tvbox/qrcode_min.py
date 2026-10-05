# -*- coding: utf-8 -*-
"""Minimális, függőségmentes QR-kód generátor (bájt mód, 1-6. verzió, L/M hibajavítás).

Egy URL (~50-90 karakter) kirajzolásához elég; nagyobb adatot nem támogat.
A kimenet egy logikai mátrix (True = sötét modul), amit a QrWidget rajzol ki.
Qt-független, ezért egyedül is tesztelhető (lásd tests/test_qrcode.py, ami valódi
QR-dekóderrel ellenőrzi a kimenetet).
"""

# ECC jelölők a formátuminformációban
_ECL_BITS = {"L": 1, "M": 0}

# verzió -> (összes kódszó, EC kódszó blokkonként, blokkok száma, adat kódszó blokkonként)
_TABLE = {
    "L": {1: (26, 7, 1, 19), 2: (44, 10, 1, 34), 3: (70, 15, 1, 55),
          4: (100, 20, 1, 80), 5: (134, 26, 1, 108), 6: (172, 18, 2, 68)},
    "M": {1: (26, 10, 1, 16), 2: (44, 16, 1, 28), 3: (70, 26, 1, 44),
          4: (100, 18, 2, 32), 5: (134, 24, 2, 43), 6: (172, 16, 4, 27)},
}
_ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34]}


# --------------------------------------------------------------------------
# Reed-Solomon (GF(256), 0x11D)
# --------------------------------------------------------------------------
def _gf_mul(x, y):
    z = 0
    for i in range(7, -1, -1):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def rs_divisor(degree):
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            result[j] = _gf_mul(result[j], root)
            if j + 1 < degree:
                result[j] ^= result[j + 1]
        root = _gf_mul(root, 2)
    return result


def rs_remainder(data, divisor):
    result = [0] * len(divisor)
    for b in data:
        factor = b ^ result.pop(0)
        result.append(0)
        for i, coef in enumerate(divisor):
            result[i] ^= _gf_mul(coef, factor)
    return result


# --------------------------------------------------------------------------
# Adatkódolás
# --------------------------------------------------------------------------
def _pick_version(nbytes, ecc):
    for ver in sorted(_TABLE[ecc]):
        _total, _ec, blocks, data_per = _TABLE[ecc][ver]
        if 4 + 8 + 8 * nbytes <= blocks * data_per * 8:
            return ver
    raise ValueError("Az adat túl hosszú ehhez a minimális QR-generátorhoz (%d bájt)." % nbytes)


def _data_codewords(payload, ver, ecc):
    _total, _ec, blocks, data_per = _TABLE[ecc][ver]
    capacity = blocks * data_per
    bits = []

    def put(value, length):
        for i in range(length - 1, -1, -1):
            bits.append((value >> i) & 1)

    put(0b0100, 4)              # bájt mód
    put(len(payload), 8)        # karakterszám (1-9. verzió: 8 bit)
    for b in payload:
        put(b, 8)
    put(0, min(4, capacity * 8 - len(bits)))   # lezáró
    while len(bits) % 8:
        bits.append(0)
    words = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = 0xEC
    while len(words) < capacity:
        words.append(pad)
        pad ^= 0xEC ^ 0x11
    return words


def _interleave(words, ver, ecc):
    _total, ec_len, blocks, data_per = _TABLE[ecc][ver]
    divisor = rs_divisor(ec_len)
    data_blocks = [words[i * data_per:(i + 1) * data_per] for i in range(blocks)]
    ec_blocks = [rs_remainder(b, divisor) for b in data_blocks]
    out = []
    for i in range(data_per):
        for b in data_blocks:
            out.append(b[i])
    for i in range(ec_len):
        for b in ec_blocks:
            out.append(b[i])
    return out


# --------------------------------------------------------------------------
# Mátrix
# --------------------------------------------------------------------------
def format_bits(ecc, mask):
    data = (_ECL_BITS[ecc] << 3) | mask
    rem = data
    for _ in range(10):
        rem = (rem << 1) ^ ((rem >> 9) * 0x537)
    return ((data << 10) | rem) ^ 0x5412


class _Builder:
    def __init__(self, ver, ecc):
        self.ver, self.ecc = ver, ecc
        self.size = 17 + 4 * ver
        n = self.size
        self.mod = [[False] * n for _ in range(n)]
        self.func = [[False] * n for _ in range(n)]
        self._draw_function_patterns()

    def _set(self, x, y, dark):
        self.mod[y][x] = dark
        self.func[y][x] = True

    def _draw_function_patterns(self):
        n = self.size
        for i in range(n):                     # időzítő minták
            self._set(6, i, i % 2 == 0)
            self._set(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):   # kereső minták + elválasztó
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < n and 0 <= y < n:
                        self._set(x, y, max(abs(dx), abs(dy)) not in (2, 4))
        pos = _ALIGN[self.ver]
        for i, cx in enumerate(pos):           # igazító minták
            for j, cy in enumerate(pos):
                if (i == 0 and j == 0) or (i == 0 and j == len(pos) - 1) or (i == len(pos) - 1 and j == 0):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self._set(cx + dx, cy + dy, max(abs(dx), abs(dy)) != 1)
        self._draw_format(0)                   # a helyek lefoglalása
        # (a formátum-bitek a maszk kiválasztása után kerülnek végleges értékre)

    def _draw_format(self, mask):
        bits = format_bits(self.ecc, mask)
        n = self.size
        g = lambda i: ((bits >> i) & 1) != 0
        for i in range(0, 6):
            self._set(8, i, g(i))
        self._set(8, 7, g(6))
        self._set(8, 8, g(7))
        self._set(7, 8, g(8))
        for i in range(9, 15):
            self._set(14 - i, 8, g(i))
        for i in range(0, 8):
            self._set(n - 1 - i, 8, g(i))
        for i in range(8, 15):
            self._set(8, n - 15 + i, g(i))
        self._set(8, n - 8, True)              # mindig sötét modul

    def place_data(self, codewords):
        n = self.size
        total_bits = len(codewords) * 8
        i = 0
        right = n - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(n):
                for j in range(2):
                    x = right - j
                    upward = ((right + 1) & 2) == 0
                    y = n - 1 - vert if upward else vert
                    if not self.func[y][x] and i < total_bits:
                        self.mod[y][x] = ((codewords[i >> 3] >> (7 - (i & 7))) & 1) != 0
                        i += 1
            right -= 2

    def apply_mask(self, mask):
        n = self.size
        for y in range(n):
            for x in range(n):
                if self.func[y][x]:
                    continue
                if mask == 0: inv = (x + y) % 2 == 0
                elif mask == 1: inv = y % 2 == 0
                elif mask == 2: inv = x % 3 == 0
                elif mask == 3: inv = (x + y) % 3 == 0
                elif mask == 4: inv = (x // 3 + y // 2) % 2 == 0
                elif mask == 5: inv = x * y % 2 + x * y % 3 == 0
                elif mask == 6: inv = (x * y % 2 + x * y % 3) % 2 == 0
                else: inv = ((x + y) % 2 + x * y % 3) % 2 == 0
                self.mod[y][x] ^= inv


def _penalty(m):
    n = len(m)
    score = 0
    lines = [row for row in m] + [[m[y][x] for y in range(n)] for x in range(n)]
    for line in lines:                                   # 1. szabály: azonos színű sorozatok
        run, prev = 1, line[0]
        for v in line[1:]:
            if v == prev:
                run += 1
            else:
                if run >= 5: score += 3 + (run - 5)
                run, prev = 1, v
        if run >= 5: score += 3 + (run - 5)
    for y in range(n - 1):                               # 2. szabály: 2x2 blokkok
        for x in range(n - 1):
            if m[y][x] == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]:
                score += 3
    pat1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]             # 3. szabály: kereső-szerű minták
    pat2 = pat1[::-1]
    for line in lines:
        ln = [1 if v else 0 for v in line]
        for i in range(n - 10):
            seg = ln[i:i + 11]
            if seg == pat1 or seg == pat2:
                score += 40
    dark = sum(v for row in m for v in row)              # 4. szabály: egyensúly
    k = abs(dark * 20 - n * n * 10) // (n * n)
    return score + k * 10


def make_qr(text, ecc="M"):
    """Visszaad egy négyzetes logikai mátrixot (True = sötét), quiet zone NÉLKÜL."""
    if ecc not in _TABLE:
        raise ValueError("ecc: 'L' vagy 'M'")
    payload = text.encode("utf-8")
    ver = _pick_version(len(payload), ecc)
    codewords = _interleave(_data_codewords(payload, ver, ecc), ver, ecc)
    best = None
    for mask in range(8):
        b = _Builder(ver, ecc)
        b.place_data(codewords)
        b.apply_mask(mask)
        b._draw_format(mask)
        p = _penalty(b.mod)
        if best is None or p < best[0]:
            best = (p, b.mod)
    return [list(r) for r in best[1]]
