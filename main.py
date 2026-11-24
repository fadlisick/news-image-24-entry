"""THE TUESDAY GLOBE - one image of Tuesday 24 November 2026.

A single-frame broadsheet poster drawn from scratch with the Python
standard library only: own bitmap font, own scene painters, own PNG
writer (zlib + struct). No Pillow, no network, fully deterministic.
Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---- palette ------------------------------------------------------------
PAPER = (247, 242, 231)
INK = (24, 24, 24)
NAVY = (13, 38, 68)
NAVY2 = (24, 58, 96)
RED = (178, 34, 34)
GOLD = (255, 214, 90)
WHITE = (255, 255, 255)
CREAM = (247, 242, 231)
GREY = (110, 110, 104)
LIGHT = (232, 226, 214)
SKY = (135, 190, 220)
SEA = (38, 110, 158)
DEEPSEA = (18, 70, 110)
GREEN = (46, 125, 70)
SAND = (222, 196, 150)
DARKGREEN = (28, 84, 48)
ORANGE = (214, 110, 30)
BROWN = (120, 84, 50)


class Board:
    """A plain RGB pixel buffer with flat-shape painters."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def _px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def fill(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def rect(self, x, y, w, h, c):
        self.fill(x, y, w, h, c)

    def frame(self, x, y, w, h, c, t=1):
        self.fill(x, y, w, t, c)
        self.fill(x, y + h - t, w, t, c)
        self.fill(x, y, t, h, c)
        self.fill(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c):
        self.fill(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.fill(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self._px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            self.fill(cx - half, cy + dy, half * 2 + 1, 1, c)

    def ring(self, cx, cy, r, c, t=2):
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            inner = int(((r - t) * (r - t) - dy * dy) ** 0.5) if abs(dy) < r - t else 0
            self.fill(cx - half, cy + dy, half - inner, 1, c)
            self.fill(cx + inner + 1, cy + dy, half - inner, 1, c)

    def poly(self, pts, c):
        """Scanline fill of a simple polygon given as [(x, y), ...]."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    if y1 != y0:
                        xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa = int(round(xs[k]))
                xb = int(round(xs[k + 1]))
                if xb > xa:
                    self.fill(xa, y, xb - xa, 1, c)

    def tri(self, x0, y0, x1, y1, x2, y2, c):
        self.poly([(x0, y0), (x1, y1), (x2, y2)], c)


def write_png(board, path):
    raw = bytearray()
    stride = board.w * 3
    for y in range(board.h):
        raw.append(0)
        raw += board.buf[y * stride:(y + 1) * stride]
    data = zlib.compress(bytes(raw), 9)

    def chunk(tag, payload):
        out = struct.pack(">I", len(payload)) + tag + payload
        out += struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", board.w, board.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", data)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---- bitmap font: 5x7, drawn from scratch -------------------------------
# Each glyph is 7 rows of 5 characters; '#' is ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    "q": ("00000", "00000", "01111", "10001", "01111", "00001", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01010", "00100"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    ";": ("00000", "01100", "00000", "01100", "00100", "01000", "00000"),
    ":": ("00000", "01100", "00000", "01100", "00000", "01100", "00000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    "^": ("00100", "01010", "00000", "00000", "00000", "00000", "00000"),
    "\\": ("10000", "01000", "01000", "00100", "00010", "00010", "00001"),
    "`": ("01000", "00100", "00000", "00000", "00000", "00000", "00000"),
    "{": ("00110", "01000", "01000", "11110", "01000", "01000", "00110"),
    "}": ("01100", "00010", "00010", "01111", "00010", "00010", "01100"),
}

CHAR_W = 6  # glyph cell width in font pixels (5 + 1 spacing)
CHAR_H = 7


def text_w(s, scale):
    return len(s) * CHAR_W * scale


def draw_text(b, x, y, s, color, scale=1, bold=False):
    """Draw one line of text; unknown chars become spaces."""
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for r in range(7):
            row = glyph[r]
            for c in range(5):
                if row[c] == "1":
                    b.fill(cx + c * scale, y + r * scale, scale, scale, color)
                    if bold:
                        b.fill(cx + c * scale + 1, y + r * scale, scale, scale, color)
        cx += CHAR_W * scale
    return cx


def wrap_text(s, max_chars):
    """Greedy word wrap into lines of at most max_chars characters."""
    words = s.split(" ")
    lines = []
    cur = ""
    for wd in words:
        if cur == "":
            cur = wd
        elif len(cur) + 1 + len(wd) <= max_chars:
            cur += " " + wd
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_para(b, x, y, w, s, color, scale=1, leading=2, bold=False, max_lines=None):
    """Draw a wrapped paragraph; returns the y just below the last line."""
    max_chars = max(1, w // (CHAR_W * scale))
    lines = wrap_text(s, max_chars)
    if max_lines is not None:
        lines = lines[:max_lines]
    yy = y
    for ln in lines:
        draw_text(b, x, yy, ln, color, scale, bold)
        yy += CHAR_H * scale + leading
    return yy

# ---- scene painters: flat-color mini pictures ---------------------------
# Each takes (board, x, y, w, h) and draws inside that box.

def scene_island(b, x, y, w, h):
    b.fill(x, y, w, h, SKY)
    b.disc(x + int(w * 0.82), y + int(h * 0.18), 10, GOLD)
    b.fill(x, y + int(h * 0.62), w, h - int(h * 0.62), SEA)
    b.fill(x, y + int(h * 0.62), w, 2, WHITE)
    b.poly([(x + int(w * 0.08), y + h), (x + int(w * 0.30), y + int(h * 0.34)),
            (x + int(w * 0.52), y + int(h * 0.52)), (x + int(w * 0.62), y + h)], GREEN)
    b.poly([(x + int(w * 0.52), y + h), (x + int(w * 0.66), y + int(h * 0.44)),
            (x + int(w * 0.86), y + int(h * 0.58)), (x + int(w * 0.92), y + h)], DARKGREEN)
    tx, ty = x + int(w * 0.30), y + int(h * 0.34)
    b.fill(tx - 1, ty - 26, 3, 26, INK)
    b.line(tx + 1, ty - 26, tx + 16, ty - 18, INK)
    b.disc(tx + 1, ty - 27, 3, RED)
    b.ring(tx + 1, ty - 27, 8, RED, 2)
    b.ring(tx + 1, ty - 27, 13, RED, 1)
    jx, jy = x + int(w * 0.62), y + int(h * 0.22)
    b.poly([(jx, jy), (jx + 26, jy + 5), (jx, jy + 9)], INK)
    b.poly([(jx + 4, jy + 3), (jx + 12, jy + 12), (jx + 16, jy + 4)], INK)
    b.tri(x + int(w * 0.10), y + int(h * 0.86), x + int(w * 0.16), y + int(h * 0.86),
          x + int(w * 0.13), y + int(h * 0.78), WHITE)


def scene_chess(b, x, y, w, h):
    b.fill(x, y, w, h, (168, 200, 224))
    b.poly([(x, y + h), (x + int(w * 0.25), y + int(h * 0.30)), (x + int(w * 0.5), y + h)], (120, 140, 160))
    b.poly([(x + int(w * 0.45), y + h), (x + int(w * 0.72), y + int(h * 0.22)), (x + w, y + h)], (96, 120, 146))
    bs = max(5, (h - 12) // 8)
    bx, by = x + (w - 8 * bs) // 2, y + (h - 8 * bs) // 2
    for r in range(8):
        for c in range(8):
            col = (232, 222, 200) if (r + c) % 2 == 0 else (52, 52, 48)
            b.fill(bx + c * bs, by + r * bs, bs, bs, col)
    b.frame(bx, by, bs * 8, bs * 8, INK, 2)
    kx, ky = bx + 2 * bs, by + 1 * bs
    b.disc(kx + bs // 2, ky + bs // 2, bs // 2 - 1, WHITE)
    b.fill(kx + 1, ky - 3, bs - 2, 3, GOLD)
    qx, qy = bx + 5 * bs, by + 6 * bs
    b.disc(qx + bs // 2, qy + bs // 2, bs // 2 - 1, INK)
    b.fill(qx + 1, qy - 3, bs - 2, 3, GOLD)
    px, py = bx + 3 * bs, by + 5 * bs
    b.disc(px + bs // 2, py + bs // 2, bs // 3, INK)


def scene_climate(b, x, y, w, h):
    b.fill(x, y, w, h, (196, 196, 186))
    b.disc(x + int(w * 0.84), y + int(h * 0.20), 12, (226, 140, 60))
    b.fill(x, y + int(h * 0.58), w, h - int(h * 0.58), (178, 138, 92))
    b.line(x + int(w * 0.15), y + h, x + int(w * 0.30), y + int(h * 0.72), (90, 60, 35))
    b.line(x + int(w * 0.30), y + int(h * 0.72), x + int(w * 0.42), y + int(h * 0.86), (90, 60, 35))
    b.line(x + int(w * 0.62), y + h, x + int(w * 0.55), y + int(h * 0.78), (90, 60, 35))
    b.line(x + int(w * 0.55), y + int(h * 0.78), x + int(w * 0.68), y + int(h * 0.88), (90, 60, 35))
    for i in range(5):
        cx = x + int(w * (0.10 + i * 0.17))
        cy = y + int(h * 0.46)
        b.fill(cx, cy, 22, 3, (70, 70, 66))
        b.fill(cx, cy, 3, 12, (70, 70, 66))
        b.fill(cx + 19, cy, 3, 12, (70, 70, 66))
    b.fill(x + int(w * 0.42), y + int(h * 0.30), 52, 22, (240, 240, 232))
    b.fill(x + int(w * 0.42) + 4, y + int(h * 0.30) + 4, 44, 14, NAVY2)
    draw_text(b, x + int(w * 0.42) + 8, y + int(h * 0.30) + 7, "NO DEAL", (255, 255, 255), 1)


def scene_markets(b, x, y, w, h):
    b.fill(x, y, w, h, (210, 226, 238))
    base = y + int(h * 0.86)
    for i, bh in enumerate([26, 44, 34, 58, 48, 70, 60]):
        bx = x + 8 + i * int(w * 0.13)
        b.fill(bx, base - bh, int(w * 0.09), bh, NAVY2 if i % 2 else (90, 110, 140))
    pts = [(x + 10, base - 20), (x + int(w * 0.25), base - 34), (x + int(w * 0.42), base - 26),
           (x + int(w * 0.60), base - 52), (x + int(w * 0.78), base - 46), (x + w - 12, base - 74)]
    for i in range(len(pts) - 1):
        b.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], GREEN)
        b.line(pts[i][0], pts[i][1] + 1, pts[i + 1][0], pts[i + 1][1] + 1, GREEN)
    ex, ey = pts[-1]
    b.tri(ex, ey, ex - 12, ey + 2, ex - 2, ey + 12, GREEN)
    b.disc(x + int(w * 0.86), y + int(h * 0.16), 9, GOLD)


def scene_arctic(b, x, y, w, h):
    b.fill(x, y, w, h, (170, 196, 214))
    b.fill(x, y + int(h * 0.66), w, h - int(h * 0.66), (228, 236, 242))
    bx, by = x + int(w * 0.08), y + int(h * 0.34)
    bw, bh = int(w * 0.40), int(h * 0.34)
    b.fill(bx, by, bw, bh, (150, 150, 146))
    b.tri(bx - 4, by, bx + bw // 2, by - 8, bx + bw + 4, by, RED)
    for i in range(4):
        cx = bx + 6 + i * (bw - 12) // 4
        b.fill(cx, by + 8, 5, bh - 16, WHITE)
    sx, sy = x + int(w * 0.60), y + int(h * 0.52)
    b.fill(sx, sy, 56, 12, (40, 60, 80))
    b.fill(sx + 8, sy - 14, 30, 14, (60, 80, 100))
    b.fill(sx + 34, sy - 26, 4, 12, INK)
    b.tri(x + int(w * 0.88), y + h, x + int(w * 0.94), y + int(h * 0.55), x + w, y + h, DARKGREEN)
    b.tri(x + int(w * 0.80), y + h, x + int(w * 0.85), y + int(h * 0.62), x + int(w * 0.90), y + h, GREEN)


def scene_gaza(b, x, y, w, h):
    b.fill(x, y, w, h, (224, 200, 160))
    b.disc(x + int(w * 0.80), y + int(h * 0.18), 11, (232, 120, 60))
    gy = y + int(h * 0.62)
    b.fill(x, gy, w, h - int(h * 0.62), (196, 164, 120))
    b.fill(x + int(w * 0.06), y + int(h * 0.34), int(w * 0.22), int(h * 0.30), (140, 128, 110))
    b.poly([(x + int(w * 0.06), y + int(h * 0.34)), (x + int(w * 0.17), y + int(h * 0.24)),
            (x + int(w * 0.28), y + int(h * 0.34))], (120, 108, 92))
    b.fill(x + int(w * 0.34), y + int(h * 0.42), int(w * 0.18), int(h * 0.22), (160, 148, 128))
    b.fill(x + int(w * 0.58), y + int(h * 0.30), int(w * 0.26), int(h * 0.34), (130, 118, 100))
    for i in range(3):
        b.fill(x + int(w * (0.62 + i * 0.07)), y + int(h * 0.36), 6, 8, (60, 56, 50))
    b.tri(x + int(w * 0.44), y + int(h * 0.30), x + int(w * 0.52), y + int(h * 0.30),
          x + int(w * 0.48), y + int(h * 0.18), (200, 170, 40))
    draw_text(b, x + int(w * 0.475), y + int(h * 0.225), "!", INK, 1, True)


def scene_ai(b, x, y, w, h):
    b.fill(x, y, w, h, (18, 44, 70))
    bx, by = x + int(w * 0.30), y + int(h * 0.26)
    bw, bh = int(w * 0.40), int(h * 0.56)
    b.fill(bx, by, bw, bh, (120, 160, 200))
    for r in range(2):
        for c in range(3):
            b.fill(bx + 6 + c * 16, by + 5 + r * 10, 10, 7, GOLD if (r + c) % 3 == 0 else WHITE)
    b.tri(bx, by, bx + bw // 2, by - 8, bx + bw, by, RED)
    for (nx, ny) in [(x + int(w * 0.12), y + int(h * 0.30)), (x + int(w * 0.86), y + int(h * 0.24)),
                     (x + int(w * 0.10), y + int(h * 0.70)), (x + int(w * 0.88), y + int(h * 0.66))]:
        b.disc(nx, ny, 4, GOLD)
        b.line(nx, ny, bx + bw // 2, by + bh // 2, (90, 130, 170))


def scene_talks(b, x, y, w, h):
    b.fill(x, y, w, h, SKY)
    b.poly([(x, y + h), (x + int(w * 0.30), y + int(h * 0.42)), (x + int(w * 0.55), y + h)], (150, 168, 180))
    b.poly([(x + int(w * 0.45), y + h), (x + int(w * 0.72), y + int(h * 0.30)), (x + w, y + h)], (120, 142, 160))
    b.fill(x, y + int(h * 0.78), w, h - int(h * 0.78), GREEN)
    fx = x + int(w * 0.20)
    b.fill(fx, y + int(h * 0.24), 2, int(h * 0.54), INK)
    b.fill(fx + 2, y + int(h * 0.24), 34, 7, (255, 153, 51))
    b.fill(fx + 2, y + int(h * 0.24) + 7, 34, 7, WHITE)
    b.fill(fx + 2, y + int(h * 0.24) + 14, 34, 7, (19, 136, 8))
    gx = x + int(w * 0.62)
    b.fill(gx, y + int(h * 0.24), 2, int(h * 0.54), INK)
    b.fill(gx + 2, y + int(h * 0.24), 34, 21, RED)
    for sx in range(5):
        b.fill(gx + 4 + sx, y + int(h * 0.24) + 3 + (sx % 2), 1, 1, GOLD)


def scene_cricket(b, x, y, w, h):
    b.fill(x, y, w, h, SKY)
    b.disc(x + int(w * 0.84), y + int(h * 0.16), 9, GOLD)
    b.fill(x, y + int(h * 0.55), w, h - int(h * 0.55), (64, 140, 70))
    b.fill(x + int(w * 0.42), y + int(h * 0.55), int(w * 0.16), h - int(h * 0.55), (210, 190, 150))
    sx = x + int(w * 0.47)
    for dx in (-4, 0, 4):
        b.fill(sx + dx, y + int(h * 0.60), 2, 14, (240, 220, 160))
    b.fill(sx - 5, y + int(h * 0.60) - 2, 12, 2, (240, 220, 160))
    b.line(x + int(w * 0.30), y + int(h * 0.72), x + int(w * 0.38), y + int(h * 0.60), (160, 110, 60))
    b.line(x + int(w * 0.30), y + int(h * 0.72), x + int(w * 0.30), y + int(h * 0.60), (160, 110, 60))
    b.disc(x + int(w * 0.66), y + int(h * 0.68), 4, RED)


def scene_awacs(b, x, y, w, h):
    b.fill(x, y, w, h, (150, 190, 216))
    b.disc(x + int(w * 0.20), y + int(h * 0.30), 12, WHITE)
    b.disc(x + int(w * 0.78), y + int(h * 0.62), 9, WHITE)
    cx, cy = x + int(w * 0.50), y + int(h * 0.52)
    b.poly([(cx - 34, cy), (cx + 34, cy - 4), (cx + 40, cy + 2), (cx - 30, cy + 6)], (230, 230, 228))
    b.fill(cx - 6, cy - 14, 22, 4, (200, 200, 198))
    b.disc(cx + 2, cy - 12, 6, (210, 210, 208))
    b.poly([(cx - 30, cy + 4), (cx - 40, cy + 16), (cx - 30, cy + 6)], (210, 210, 208))
    b.poly([(cx + 26, cy - 2), (cx + 34, cy - 14), (cx + 34, cy)], (210, 210, 208))


def scene_ship(b, x, y, w, h):
    b.fill(x, y, w, h, (120, 170, 205))
    b.fill(x, y + int(h * 0.64), w, h - int(h * 0.64), SEA)
    b.fill(x, y + int(h * 0.64), w, 2, WHITE)
    sx, sy = x + int(w * 0.16), y + int(h * 0.50)
    b.poly([(sx, sy), (sx + int(w * 0.56), sy), (sx + int(w * 0.50), sy + 16), (sx + 6, sy + 16)], (60, 60, 64))
    b.fill(sx + int(w * 0.10), sy - 14, int(w * 0.24), 14, (120, 120, 118))
    b.fill(sx + int(w * 0.16), sy - 14, 4, 8, INK)
    dx, dy = x + int(w * 0.72), y + int(h * 0.24)
    b.poly([(dx, dy), (dx + 16, dy + 4), (dx, dy + 8)], (40, 40, 44))
    b.line(dx + 8, dy + 4, dx + 8, dy + 12, (40, 40, 44))
    b.disc(x + int(w * 0.30), y + int(h * 0.72), 3, WHITE)
    b.disc(x + int(w * 0.44), y + int(h * 0.78), 3, WHITE)


def scene_oil(b, x, y, w, h):
    b.fill(x, y, w, h, (226, 200, 150))
    b.disc(x + int(w * 0.80), y + int(h * 0.18), 11, (232, 140, 50))
    b.fill(x, y + int(h * 0.72), w, h - int(h * 0.72), (150, 110, 70))
    dx, dy = x + int(w * 0.30), y + h - 4
    top = y + 4
    b.line(dx, dy, dx + 14, top, INK)
    b.line(dx + 28, dy, dx + 14, top, INK)
    b.line(dx + 5, dy - 10, dx + 23, dy - 10, INK)
    b.line(dx + 9, dy - 20, dx + 19, dy - 20, INK)
    b.line(dx + 14, top, dx + 40, top + 8, INK)
    b.fill(dx + 38, top + 4, 6, 8, INK)
    b.disc(x + int(w * 0.72), y + int(h * 0.56), 8, INK)
    b.tri(x + int(w * 0.72), y + int(h * 0.44), x + int(w * 0.68), y + int(h * 0.56),
          x + int(w * 0.76), y + int(h * 0.56), INK)


def scene_bars(b, x, y, w, h):
    b.fill(x, y, w, h, (196, 190, 178))
    bx, by = x + int(w * 0.18), y + int(h * 0.22)
    bw, bh = int(w * 0.64), int(h * 0.62)
    b.fill(bx, by, bw, bh, (140, 130, 116))
    b.tri(bx - 3, by, bx + bw // 2, by - 6, bx + bw + 3, by, (90, 84, 74))
    for i in range(6):
        vx = bx + 4 + i * (bw - 8) // 6
        b.fill(vx, by + 4, 3, bh - 8, INK)
    b.fill(bx + bw // 2 - 8, by + bh // 2 - 6, 16, 12, GOLD)


def scene_moon(b, x, y, w, h):
    b.fill(x, y, w, h, (16, 24, 48))
    for (sx, sy) in [(0.12, 0.18), (0.30, 0.10), (0.55, 0.14), (0.88, 0.12), (0.70, 0.30), (0.20, 0.38)]:
        b.disc(x + int(w * sx), y + int(h * sy), 1, WHITE)
    b.disc(x + int(w * 0.50), y + int(h * 0.45), min(22, int(h * 0.42)), (240, 230, 200))
    b.disc(x + int(w * 0.44), y + int(h * 0.38), 4, (205, 195, 165))
    b.disc(x + int(w * 0.56), y + int(h * 0.50), 5, (205, 195, 165))
    b.disc(x + int(w * 0.52), y + int(h * 0.36), 3, (205, 195, 165))
    base = y + int(h * 0.84)
    for i, bh in enumerate([14, 22, 10, 26, 16]):
        bx = x + 6 + i * int(w * 0.19)
        b.fill(bx, base - bh, int(w * 0.15), bh + h - base, (40, 44, 66))


def scene_bank(b, x, y, w, h):
    b.fill(x, y, w, h, (216, 208, 188))
    bx, by = x + int(w * 0.16), y + int(h * 0.30)
    bw, bh = int(w * 0.68), int(h * 0.46)
    b.tri(bx - 4, by, bx + bw // 2, by - 8, bx + bw + 4, by, (110, 100, 84))
    b.fill(bx, by, bw, bh, (150, 140, 120))
    for i in range(4):
        cx = bx + 6 + i * (bw - 12) // 4
        b.fill(cx, by + 4, 6, bh - 4, (230, 222, 200))
    b.fill(bx, by + bh, bw, 4, (90, 82, 66))
    draw_text(b, x + int(w * 0.47), y + int(h * 0.62), "$", INK, 2, True)

# ---- world map: filled continents, labelled pins ------------------------
CONTINENTS = [
    [(-168, 66), (-150, 70), (-130, 71), (-110, 68), (-95, 69), (-85, 66), (-76, 62),
     (-65, 60), (-60, 52), (-55, 47), (-60, 44), (-70, 42), (-75, 36), (-81, 31),
     (-84, 26), (-90, 21), (-95, 18), (-100, 16), (-105, 20), (-110, 24), (-115, 29),
     (-125, 40), (-124, 48), (-135, 58), (-150, 60), (-165, 60)],
    [(-79, 9), (-72, 11), (-62, 10), (-52, 5), (-50, 0), (-44, -3), (-35, -8),
     (-37, -13), (-40, -20), (-48, -27), (-55, -33), (-62, -39), (-65, -45), (-68, -52),
     (-71, -54), (-73, -45), (-73, -35), (-71, -25), (-75, -15), (-80, -6), (-81, 1)],
    [(-17, 15), (-16, 21), (-10, 30), (-6, 35), (0, 36), (10, 37), (15, 32), (20, 32),
     (25, 32), (30, 31), (33, 27), (35, 22), (38, 18), (43, 12), (48, 11), (51, 11),
     (44, 5), (41, -2), (40, -10), (36, -18), (33, -26), (28, -33), (20, -35), (17, -32),
     (14, -27), (12, -18), (13, -10), (12, -4), (9, 4), (4, 6), (-8, 5), (-13, 8)],
    [(-10, 36), (-9, 38), (-9, 43), (-2, 44), (-1, 46), (0, 50), (3, 52), (7, 54),
     (8, 57), (10, 59), (13, 56), (18, 56), (21, 55), (24, 58), (26, 60), (29, 62),
     (30, 64), (28, 66), (25, 68), (22, 70), (18, 70), (14, 68), (10, 64), (5, 60),
     (5, 58), (0, 55), (-3, 50), (-5, 48), (-10, 44)],
    [(30, 36), (32, 42), (36, 44), (40, 46), (44, 48), (48, 52), (52, 55), (55, 58),
     (58, 62), (62, 66), (68, 68), (75, 70), (85, 72), (95, 74), (105, 76), (115, 73),
     (125, 72), (135, 72), (145, 71), (155, 70), (165, 69), (175, 67), (178, 65),
     (170, 60), (162, 56), (158, 52), (150, 48), (142, 45), (140, 40), (135, 35),
     (130, 33), (127, 35), (122, 32), (120, 25), (115, 22), (110, 20), (108, 14),
     (105, 9), (102, 7), (98, 10), (95, 15), (92, 21), (89, 22), (86, 20), (82, 17),
     (78, 13), (76, 9), (74, 15), (72, 20), (68, 23), (64, 25), (60, 25), (56, 27),
     (52, 29), (49, 30), (46, 30), (43, 32), (40, 35), (36, 36), (33, 36)],
    [(113, -22), (114, -28), (115, -33), (118, -35), (124, -33), (129, -32), (132, -32),
     (135, -35), (138, -35), (140, -38), (145, -38), (148, -39), (150, -37), (153, -32),
     (153, -27), (150, -23), (146, -19), (143, -15), (142, -11), (140, -17), (136, -15),
     (135, -12), (132, -11), (130, -13), (126, -14), (123, -17), (120, -20), (116, -21)],
    [(-45, 60), (-40, 64), (-32, 68), (-25, 70), (-20, 74), (-22, 76), (-30, 80),
     (-40, 80), (-50, 78), (-58, 74), (-55, 70), (-53, 66), (-48, 62)],
    [(130, 31), (133, 34), (137, 35), (140, 38), (141, 42), (144, 44), (142, 44),
     (140, 40), (137, 37), (133, 35)],
    [(167, -45), (170, -43), (173, -41), (175, -38), (177, -38), (174, -41), (171, -43),
     (168, -46)],
]

# (lon, lat, label, label dx, label dy)
PINS = [
    (130.9, 37.5, "ULLEUNG", 6, -4),
    (6.1, 46.2, "GENEVA", 5, -4),
    (30.7, 36.9, "ANTALYA", 5, -8),
    (-74.0, 40.7, "NEW YORK", -54, -4),
    (33.1, 69.0, "MURMANSK", 5, -6),
    (106.3, -6.2, "CIKANDE", 5, 3),
    (-66.9, 10.5, "CARACAS", 5, 3),
    (34.5, 31.5, "GAZA", 6, 6),
    (174.8, -41.3, "WELLINGTON", -62, 3),
    (85.1, 25.6, "PATNA", 5, 3),
]


def draw_map(b, x, y, w, h):
    b.fill(x, y, w, h, (186, 212, 228))
    def px(lon):
        return x + 6 + int((lon + 180.0) / 360.0 * (w - 12))
    def py(lat):
        return y + 6 + int((85.0 - lat) / 140.0 * (h - 12))
    for poly_ll in CONTINENTS:
        b.poly([(px(lon), py(lat)) for lon, lat in poly_ll], (112, 152, 106))
    for lon, lat, label, dx, dy in PINS:
        cx, cy = px(lon), py(lat)
        b.disc(cx, cy, 3, RED)
        b.ring(cx, cy, 4, WHITE, 1)
        draw_text(b, cx + dx, cy + dy, label, INK, 1, True)


# ---- story data: 36 stories --------------------------------------------
LEADS = [
    {"kick": "LEAD 1 - TUESDAY", "head": "ALERT ON ULLEUNG ISLAND",
     "body": "South Korea orders Ulleung islanders to shelter after a suspected North Korean "
             "aircraft breaches its airspace. The warning is lifted after 3 minutes.",
     "src": "(Reuters / AP)", "scene": scene_island},
    {"kick": "LEAD 2 - TUESDAY", "head": "CHESS: GAME 1 IN GENEVA",
     "body": "Gukesh defends his world crown against Sindarov, 20, in the youngest title "
             "match ever. Fourteen games, $2.5m prize fund, first move to the challenger.",
     "src": "(FIDE)", "scene": scene_chess},
    {"kick": "LEAD 3 - TUESDAY FALLOUT", "head": "COP31: THE FALLOUT",
     "body": "Pacific nations despair and the blame game begins after Sunday's collapse in "
             "Antalya. Guterres: 'deeply disappointed'. No deal, first failure since 2009.",
     "src": "(Reuters / BBC)", "scene": scene_climate},
    {"kick": "LEAD 4 - MONDAY, REPORTED TUESDAY", "head": "WALL ST ROARS BACK",
     "body": "Nasdaq jumps 6.5% as Nvidia soars 31% on Huang's return as CEO. Monday's "
             "rally, reported across Asia on Tuesday.",
     "src": "(Reuters)", "scene": scene_markets},
]

CARDS = [
    {"head": "MURMANSK GOVERNOR HELD",
     "body": "Chibis held over 39m rouble theft case.",
     "src": "(Reuters)", "scene": scene_arctic},
    {"head": "GAZA'S POISONED GROUND",
     "body": "Oxfam: Gaza's air, soil, water left toxic.",
     "src": "(Oxfam)", "scene": scene_gaza},
    {"head": "MODI OPENS AI CENTRE",
     "body": "AI centre opens at IIT Patna; Rs 400cr park.",
     "src": "(TOI)", "scene": scene_ai},
    {"head": "INDIA, CHINA TALK BORDER",
     "body": "Commanders meet in Arunachal on border.",
     "src": "(TOI)", "scene": scene_talks},
    {"head": "TEST ENDS IN A DRAW",
     "body": "First Test in Wellington ends in a draw.",
     "src": "(TOI)", "scene": scene_cricket},
    {"head": "NATO JETS FOR POLAND",
     "body": "AWACS sent after missiles landed in Poland.",
     "src": "(Reuters)", "scene": scene_awacs},
    {"head": "KYIV SINKS SHIP IN LIBYA",
     "body": "Kyiv: drones sank corvette Merkuriy off Benghazi.",
     "src": "(Guardian)", "scene": scene_ship},
    {"head": "US: CARTEL IS TERRORISTS",
     "body": "US lists Cartel de los Soles as terrorists.",
     "src": "(CBC)", "scene": scene_oil},
    {"head": "BOLSONARO BACK IN JAIL",
     "body": "Brazil's ex-president returns to prison.",
     "src": "(AP)", "scene": scene_bars},
    {"head": "BEAVER SUPERMOON",
     "body": "November's biggest full moon lights the sky.",
     "src": "(NASA)", "scene": scene_moon},
    {"head": "US SANCTIONS IRAN BANKS",
     "body": "Treasury hits Iran's shadow banking networks.",
     "src": "(Reuters)", "scene": scene_bank},
]

NUMBERS = [
    ("+6.5%", "Nasdaq, Monday rebound"),
    ("31%", "Nvidia jump, Huang returns"),
    ("24", "killed in Indonesia factory fire"),
    ("3 min", "Ulleung warning lasted"),
    ("$2.5m", "chess prize fund, Geneva"),
    ("1bn", "roubles in Murmansk road probe"),
]

TIMELINE = [
    ("21:00 MON", "Wall St closes: Nasdaq +6.5%"),
    ("22:52 MON", "Ulleung alert issued, S. Korea"),
    ("09:00", "Germany Ifo business survey due"),
    ("14:00", "Chess Game 1 starts, Geneva"),
    ("15:00", "US consumer confidence due"),
]

DATECHECK = [
    "Sun 22 Nov - COP31 collapses in Antalya, no deal (Reuters)",
    "Sun 22 Nov - Alcaraz wins ATP Finals in Turin (ATP)",
    "Thu 19 Nov - ICJ: Myanmar guilty of Rohingya genocide (ICJ)",
    "Thu 19 Nov - Trump, Xi, Putin meet in Shenzhen (RFE/RL)",
    "Sat 21 Nov - Indonesia factory fire; 24 dead confirmed Mon (Reuters)",
    "Sat 21 Nov - BepiColombo enters orbit around Mercury (ESA)",
    "Mon 23 Nov - Spain drops all charges against Puigdemont (Reuters)",
    "Mon 23 Nov - EU-Indonesia landmark trade deal signed (Reuters)",
]

ALSO = [
    "Nigeria boat capsizes, 24 dead (Mon)",
    "Estonia to shut Russia land borders (Mon)",
    "EU lists 'The Base' founder as terrorist (Mon)",
    "Trump halts Iowa explosives detonation (Mon)",
    "Germany to use Kyiv's Delta battle tool (Mon)",
    "Iran vows to fight US naval blockade (Mon)",
    "Armenia drops Karabakh from draft charter (Mon)",
    "Sudan drones kill 4 near Khartoum (Mon)",
    "Lebanon villagers return as troops pull back (Mon)",
    "Spain sets general election for 29 Nov (Mon)",
    "WSJ: Kim ignores Trump's outreach (Nov)",
    "Miley Cyrus weds Maxx Morando (Mon)",
    "Acropolis Museum reopens in Athens (Mon)",
]

FOOTER = ("Every story here happened, or was first reported, on Tuesday "
          "24 November 2026 in at least one time zone.")


# ---- layout --------------------------------------------------------------
def masthead(b):
    b.fill(0, 0, W, 6, RED)
    b.fill(0, 6, W, 98, NAVY)
    title = "THE TUESDAY GLOBE"
    draw_text(b, (W - text_w(title, 5)) // 2, 14, title, CREAM, 5, True)
    date = "TUESDAY 24 NOVEMBER 2026"
    draw_text(b, (W - text_w(date, 3)) // 2, 58, date, GOLD, 3, True)
    ed = "36 STORIES - ONE DAY - FIVE CONTINENTS - WORLD EDITION"
    draw_text(b, (W - text_w(ed, 1)) // 2, 88, ed, (200, 210, 225), 1)
    b.fill(0, 104, W, 2, GOLD)


def timeline_strip(b, y0):
    colw = 1008 // 5
    for i, (tm, txt) in enumerate(TIMELINE):
        cx = 8 + i * colw
        if i:
            b.vline(cx - 4, y0 + 2, 30, LIGHT)
        draw_text(b, cx, y0 + 2, tm, RED, 2, True)
        draw_para(b, cx, y0 + 18, colw - 8, txt, INK, 1, leading=1, max_lines=2)
    b.fill(0, y0 + 36, W, 1, LIGHT)


def numbers_band(b, y0):
    b.fill(8, y0, 1008, 50, WHITE)
    b.frame(8, y0, 1008, 50, LIGHT, 1)
    cell = 1008 // 6
    for i, (big, label) in enumerate(NUMBERS):
        cx = 8 + i * cell
        if i:
            b.vline(cx, y0 + 6, 38, LIGHT)
        draw_text(b, cx + 10, y0 + 6, big, NAVY, 3, True)
        draw_para(b, cx + 10, y0 + 30, cell - 20, label, GREY, 1, leading=1, max_lines=2)


def lead_cell(b, x, y, w, h, lead):
    b.fill(x, y, w, h, WHITE)
    b.frame(x, y, w, h, LIGHT, 1)
    lead["scene"](b, x + 2, y + 2, w - 4, 96)
    draw_text(b, x + 8, y + 104, lead["kick"], RED, 1, True)
    yy = draw_para(b, x + 8, y + 114, w - 16, lead["head"], INK, 2,
                   leading=2, bold=True, max_lines=2)
    draw_para(b, x + 8, yy + 2, w - 16, lead["body"], INK, 1, leading=2, max_lines=3)
    src = lead["src"]
    draw_text(b, x + w - 8 - text_w(src, 1), y + h - 12, src, RED, 1)


def card_cell(b, x, y, w, h, card):
    b.fill(x, y, w, h, WHITE)
    b.frame(x, y, w, h, LIGHT, 1)
    card["scene"](b, x + 1, y + 1, w - 2, 36)
    yy = draw_para(b, x + 5, y + 41, w - 10, card["head"], INK, 1,
                   leading=1, bold=True, max_lines=2)
    draw_para(b, x + 5, yy + 1, w - 10, card["body"], INK, 1, leading=1, max_lines=2)
    draw_text(b, x + w - 5 - text_w(card["src"], 1), y + h - 10, card["src"], RED, 1)


def map_and_datecheck(b, y0, h):
    b.fill(8, y0, 500, h, WHITE)
    b.frame(8, y0, 500, h, LIGHT, 1)
    draw_text(b, 16, y0 + 6, "WHERE IT HAPPENED", RED, 1, True)
    draw_map(b, 16, y0 + 18, 484, h - 24)
    bx = 516
    b.fill(bx, y0, 500, h, WHITE)
    b.frame(bx, y0, 500, h, LIGHT, 1)
    draw_text(b, bx + 8, y0 + 6, "DATE CHECK - THESE ARE NOT TUESDAY", RED, 1, True)
    yy = y0 + 20
    for item in DATECHECK:
        draw_text(b, bx + 8, yy, item, INK, 1)
        yy += 13


def also_list(b, y0, h):
    draw_text(b, 8, y0, "ALSO TODAY", RED, 1, True)
    b.fill(96, y0 + 3, 920, 1, LIGHT)
    col_a = ALSO[:7]
    col_b = ALSO[7:]
    yy = y0 + 12
    for i, item in enumerate(col_a):
        draw_text(b, 8, yy + i * 10, "- " + item, INK, 1)
    for i, item in enumerate(col_b):
        draw_text(b, 516, yy + i * 10, "- " + item, INK, 1)


def build():
    b = Board(W, H, PAPER)
    masthead(b)
    timeline_strip(b, 110)
    numbers_band(b, 150)
    lead_w = (1008 - 8) // 2
    lead_cell(b, 8, 204, lead_w, 182, LEADS[0])
    lead_cell(b, 8 + lead_w + 8, 204, lead_w, 182, LEADS[1])
    lead_cell(b, 8, 390, lead_w, 182, LEADS[2])
    lead_cell(b, 8 + lead_w + 8, 390, lead_w, 182, LEADS[3])
    row1 = CARDS[:6]
    cw1 = (1008 - 5 * 4) // 6
    for i, card in enumerate(row1):
        card_cell(b, 8 + i * (cw1 + 4), 576, cw1, 88, card)
    row2 = CARDS[6:]
    cw2 = (1008 - 4 * 4) // 5
    for i, card in enumerate(row2):
        card_cell(b, 8 + i * (cw2 + 4), 668, cw2, 88, card)
    map_and_datecheck(b, 760, 136)
    also_list(b, 900, 84)
    b.fill(0, 988, W, 1, RED)
    draw_text(b, (W - text_w(FOOTER, 1)) // 2, 996, FOOTER, INK, 1)
    return b


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    board = build()
    size = write_png(board, path)
    # Validation guard: verify what was written, without changing it.
    with open(path, "rb") as f:
        blob = f.read()
    assert blob[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    w, h = struct.unpack(">II", blob[16:24])
    assert (w, h) == (W, H), "bad dimensions"
    assert len(blob) == size and len(blob) <= 1048576, "bad size"
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
