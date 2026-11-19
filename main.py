"""The world in one day: Thursday 19 November 2026.

A newspaper front page drawn entirely in code and written out as one
1024x1024 PNG. Pure Python 3.13 standard library only: a bytearray
canvas, a 5x7 bitmap alphabet stored as strings of 0s and 1s, and a
hand-rolled PNG encoder (zlib + struct, filter 0 on every scanline).
No network, no clock, no randomness, no file reads, so the bytes it
writes are identical on every run.

Headlines, each reported on Thursday 19 November 2026:
  * Grand Theft Auto VI begins its global rollout; Vice City returns
    after a 13-year wait, midnight launches, early reviews at 99.
  * Democrats nominate Hakeem Jeffries for Speaker of the US House;
    set to be the first African-American Speaker.
  * The EU proposes a 45-billion-euro loan for Ukraine, to be repaid
    once Russia pays reparations.
  * NASA's Voyager 1 reaches one light-day from Earth, almost 50
    years after launch.
  * Cyclone Akvan bears down on India's east coast, due to cross
    between Machilipatnam and Puri.
  * Fed minutes show most officials expect further rate rises.
  * Also: Modi meets the Prince and Princess of Wales; the US-Iran
    fire exchange widens across the Gulf; Pew says Islam is on track
    to become the world's largest faith by 2035.
"""

import os
import struct
import zlib
from pathlib import Path

W = 1024
H = 1024

PAPER = (248, 244, 233)
INK = (24, 24, 24)
RED = (176, 26, 26)
CRIMSON = (205, 38, 38)
NAVY = (22, 48, 110)
ROYAL = (38, 84, 190)
TEAL = (12, 104, 104)
GOLD = (188, 132, 20)
RULE = (198, 190, 170)
SKYDAY = (206, 224, 238)
DUSK1 = (64, 38, 96)
DUSK2 = (146, 52, 96)
DUSK3 = (232, 128, 64)
SUNSET = (255, 196, 88)
NEON = (255, 64, 160)
PALM = (16, 110, 64)
SEA = (24, 84, 128)
SAND = (226, 208, 168)
CLOUD = (255, 255, 255)
GREY = (118, 122, 128)
LIGHT = (236, 238, 242)
CREAM = (255, 250, 238)
SPACE = (8, 10, 28)
STAR = (235, 238, 255)

# 5x7 bitmap alphabet. One glyph per line: seven rows of five bits,
# "1" a filled cell, "0" empty, bit order left to right.
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
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
}

CELL = 6  # advance per glyph, in unscaled units


class Sheet:
    """An RGB canvas backed by one flat bytearray."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = c

    def box(self, x, y, w, h, c):
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + max(0, x)) * 3
            span = min(self.w, x + w) - max(0, x)
            if span > 0:
                self.buf[base:base + span * 3] = bytes(c) * span

    def hline(self, x, y, w, c):
        self.box(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.box(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            half = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            self.box(cx - half, yy, half * 2 + 1, 1, c)

    def ring(self, cx, cy, r, c, thick=1):
        for t in range(thick):
            rr = r - t
            for yy in range(cy - rr, cy + rr + 1):
                half = int((rr * rr - (yy - cy) ** 2) ** 0.5)
                self.set(cx - half, yy, c)
                self.set(cx + half, yy, c)

    def arc(self, cx, cy, r, a0, a1, c):
        import math
        steps = max(8, int((a1 - a0) * r))
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            self.set(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), c)

    def glyph(self, x, y, ch, s, c):
        rows = FONT.get(ch, FONT["?"])
        for r, row in enumerate(rows):
            for col, bit in enumerate(row):
                if bit == "1":
                    self.box(x + col * s, y + r * s, s, s, c)

    def text(self, x, y, s, c, txt):
        cx = x
        for ch in txt.upper():
            self.glyph(cx, y, ch, s, c)
            cx += CELL * s
        return cx

    def twidth(self, s, txt):
        return len(txt) * CELL * s

    def centred(self, y, s, c, txt, cx=None):
        if cx is None:
            cx = self.w // 2
        self.text(cx - self.twidth(s, txt) // 2, y, s, c, txt)

    def wrap(self, s, width, txt):
        """Split txt into lines that fit width at scale s."""
        words = txt.split(" ")
        lines = []
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if self.twidth(s, trial) <= width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, width, s, c, txt, gap=5):
        for line in self.wrap(s, width, txt):
            self.text(x, y, s, c, line)
            y += 7 * s + gap
        return y


def png_bytes(sheet):
    raw = bytearray()
    for y in range(sheet.h):
        raw.append(0)
        raw += sheet.buf[y * sheet.w * 3:(y + 1) * sheet.w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", sheet.w, sheet.h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", comp)
        + chunk(b"IEND", b"")
    )

# ---------------------------------------------------------------- scenes

def skyline(s, x, y, w, h):
    """Vice City at dusk: banded sunset sky, sun, towers, palms, sea."""
    bands = [DUSK1, DUSK2, DUSK3, SUNSET]
    for i, c in enumerate(bands):
        s.box(x, y + i * h // 4, w, h // 4 + 1, c)
    s.disc(x + w // 2, y + h // 3, 34, SUNSET)
    s.ring(x + w // 2, y + h // 3, 42, CLOUD, 2)
    towers = [(0, 92, 66), (74, 118, 84), (168, 84, 58), (238, 112, 96),
              (348, 100, 70), (430, 118, 88), (534, 88, 62), (620, 112, 80),
              (716, 96, 66), (800, 118, 92), (908, 104, 74)]
    for tx, th, tw in towers:
        bx = x + tx
        by = y + h - 26 - th
        s.box(bx, by, tw, th + 26, INK)
        for wy in range(by + 10, by + th, 16):
            for wx in range(bx + 8, bx + tw - 8, 16):
                if (wx // 16 + wy // 16) % 3 == 0:
                    s.box(wx, wy, 7, 9, SUNSET)
    for px in (x + 30, x + w - 46):
        s.line(px, y + h - 26, px + 4, y + h - 78, PALM)
        for a in range(5):
            s.arc(px + 4, y + h - 78, 22, 3.4 + a * 0.5, 3.9 + a * 0.5, PALM)
    s.box(x, y + h - 26, w, 26, SEA)
    for i in range(6):
        yy = y + h - 22 + i * 4
        s.hline(x + (i * 53) % 120, yy, 90 - i * 8, CLOUD)
    s.box(x, y + h - 30, w, 4, NEON)
    s.text(x + 14, y + 8, 2, CLOUD, "VICE CITY")
    s.text(x + 14, y + 26, 1, CLOUD, "LEONIDA - AFTER 13 YEARS")


def capitol(s, x, y, w, h):
    """The US Capitol dome in flat white and navy."""
    s.box(x, y, w, h, SKYDAY)
    cx = x + w // 2
    s.box(cx - 4, y + 2, 8, 12, NAVY)
    s.line(cx, y + 2, cx, y, INK)
    for yy in range(y + 12, y + 64):
        half = int((52 * 52 - (yy - (y + 64)) ** 2) ** 0.5)
        s.box(cx - half, yy, half * 2 + 1, 1, CLOUD)
    s.box(cx - 62, y + 64, 124, 10, CLOUD)
    for i in range(6):
        colx = x + 24 + i * 36
        s.box(colx, y + 74, 12, 52, CLOUD)
        s.box(colx - 3, y + 70, 18, 5, CLOUD)
    s.box(x + 12, y + 126, w - 24, 12, CLOUD)
    s.box(x, y + h - 16, w, 16, NAVY)
    s.text(x + 10, y + h - 14, 1, CLOUD, "WASHINGTON")
    s.disc(x + w - 22, y + 16, 12, GOLD)
    s.ring(x + w - 22, y + 16, 12, INK, 1)


def eu_stars(s, x, y, w, h):
    """A ring of gold stars on EU blue, over a yellow-blue band."""
    import math
    s.box(x, y, w, h, ROYAL)
    s.box(x, y + h - 34, w, 34, GOLD)
    s.box(x, y + h - 17, w, 17, (245, 214, 60))
    cx, cy = x + w // 2, y + h // 2 - 8
    for i in range(12):
        a = -math.pi / 2 + i * math.pi / 6
        sx = int(cx + 62 * math.cos(a))
        sy = int(cy + 62 * math.sin(a))
        s.disc(sx, sy, 4, GOLD)
        s.box(sx - 1, sy - 6, 2, 12, GOLD)
        s.box(sx - 6, sy - 1, 12, 2, GOLD)
    s.text(x + 10, y + 8, 2, CLOUD, "EU")
    s.text(x + w - 66, y + 8, 1, CLOUD, "BRUSSELS")


def voyager(s, x, y, w, h):
    """Voyager 1 in deep space, one light-day from home."""
    s.box(x, y, w, h, SPACE)
    for i in range(48):
        sx = x + (i * 97 + 31) % (w - 8) + 4
        sy = y + (i * 61 + 17) % (h - 8) + 4
        s.set(sx, sy, STAR)
        if i % 7 == 0:
            s.set(sx + 1, sy, STAR)
    cx, cy = x + w // 2 + 40, y + h // 2 - 4
    for i in range(7):
        s.disc(x + 16 + i * 18, y + h - 14 - i * 6, 2, GREY)
    s.line(x + 16, y + h - 12, cx - 26, cy + 6, (120, 130, 160))
    s.box(cx - 24, cy - 5, 48, 10, (190, 196, 208))
    s.box(cx - 32, cy - 12, 10, 24, (150, 156, 170))
    s.line(cx + 24, cy - 5, cx + 40, cy - 24, (190, 196, 208))
    s.disc(cx + 42, cy - 26, 3, CRIMSON)
    s.line(cx - 8, cy + 5, cx - 22, cy + 22, (190, 196, 208))
    s.disc(cx - 24, cy + 24, 8, (210, 214, 224))
    s.ring(cx - 24, cy + 24, 8, INK, 1)
    s.text(x + 10, y + 6, 1, STAR, "1977 - 2026")
    s.text(x + 10, y + h - 12, 1, STAR, "ONE LIGHT-DAY OUT")


def cyclone(s, x, y, w, h):
    """A cyclone spiral over the Bay of Bengal."""
    import math
    s.box(x, y, w, h, (198, 222, 236))
    s.box(x, y + h - 22, w, 22, (58, 130, 110))
    s.text(x + 8, y + h - 18, 1, CLOUD, "BAY OF BENGAL")
    cx, cy = x + w // 2, y + h // 2
    for r in range(8, 32, 7):
        a0 = r * 0.12
        s.arc(cx, cy, r, a0, a0 + 4.4, SEA if r % 14 == 1 else TEAL)
        s.arc(cx, cy, r - 3, a0 + 0.5, a0 + 4.0, CLOUD)
    s.disc(cx, cy, 7, CREAM)
    s.ring(cx, cy, 7, SEA, 1)
    s.text(x + 8, y + 6, 1, INK, "AKVAN")


def fed_chart(s, x, y, w, h):
    """Rising bars and a red rate arrow."""
    s.box(x, y, w, h, LIGHT)
    base = y + h - 20
    vals = [12, 19, 16, 25, 22, 31, 28, 38]
    bw = (w - 32) // len(vals)
    for i, v in enumerate(vals):
        bx = x + 16 + i * bw
        s.box(bx, base - v, bw - 6, v, ROYAL if i % 2 == 0 else NAVY)
    s.hline(x + 8, base, w - 16, INK)
    s.line(x + 16, base - 10, x + w - 20, base - 40, CRIMSON)
    s.line(x + w - 20, base - 40, x + w - 32, base - 38, CRIMSON)
    s.line(x + w - 20, base - 40, x + w - 22, base - 30, CRIMSON)
    s.text(x + 10, y + 4, 1, INK, "RATES: UP?")
    s.text(x + 10, y + h - 12, 1, GREY, "FED MINUTES - OCT MEETING")


# ---------------------------------------------------------------- page

def kicker(s, x, y, txt):
    s.text(x, y, 1, RED, txt)
    s.hline(x, y + 11, s.twidth(1, txt), RED)


def draw_page(s):
    s.box(0, 0, W, H, PAPER)
    s.box(8, 8, W - 16, H - 16, PAPER)
    s.box(8, 8, W - 16, 2, INK)
    s.box(8, H - 10, W - 16, 2, INK)
    s.box(8, 8, 2, H - 16, INK)
    s.box(W - 10, 8, 2, H - 16, INK)

    # Masthead.
    s.centred(26, 1, RED, "ONE DAY - ONE PICTURE - THE WORLD'S NEWS")
    s.centred(48, 5, INK, "THE WORLD IN ONE DAY")
    s.centred(96, 2, RED, "THURSDAY, 19 NOVEMBER 2026")
    s.hline(28, 124, W - 56, INK)
    s.hline(28, 128, W - 56, INK)

    # Lead story: GTA VI.
    lx, lw = 28, W - 56
    kicker(s, lx, 142, "LEAD STORY - ENTERTAINMENT")
    s.text(lx, 160, 4, INK, "VICE CITY OPENS")
    s.text(lx, 192, 4, INK, "ITS DOORS")
    s.text(lx + 620, 168, 3, RED, "GTA VI")
    s.text(lx + 620, 196, 2, INK, "IS HERE")
    s.para(lx, 228, 560, 2, INK,
           "Grand Theft Auto VI rolls out worldwide today, unlocking "
           "at midnight in each zone after a 13-year wait. Early "
           "reviews: 99 out of 100.",
           gap=4)
    s.para(lx + 590, 228, 378, 2, INK,
           "Rockstar returns to Vice City: the year's biggest launch, "
           "on PS5 and Xbox.",
           gap=4)
    skyline(s, lx, 312, lw, 152)

    # Second row: Jeffries and the EU loan.
    y2 = 486
    s.hline(28, y2 - 10, W - 56, RULE)
    c1, c2 = 28, 524
    cw = 472
    kicker(s, c1, y2, "WASHINGTON")
    s.text(c1, y2 + 18, 3, INK, "JEFFRIES TO")
    s.text(c1, y2 + 42, 3, INK, "MAKE HISTORY")
    s.para(c1, y2 + 72, cw, 2, INK,
           "Democrats nominate Hakeem Jeffries for Speaker of the "
           "US House - set to be the first African-American Speaker.",
           gap=4)
    capitol(s, c1, y2 + 134, cw, 150)
    kicker(s, c2, y2, "BRUSSELS - KYIV")
    s.text(c2, y2 + 18, 3, INK, "EU PLANS 45BN")
    s.text(c2, y2 + 42, 3, INK, "LOAN FOR KYIV")
    s.para(c2, y2 + 72, cw, 2, INK,
           "The EU proposes a 45-billion-euro loan to fund Ukraine, "
           "to be repaid once Russia pays reparations.",
           gap=4)
    eu_stars(s, c2, y2 + 134, cw, 150)

    # Third row: Voyager, cyclone, Fed.
    y3 = 800
    s.hline(28, y3 - 10, W - 56, RULE)
    cols = [(28, 310), (358, 310), (688, 308)]
    heads = ["VOYAGER 1: ONE", "LIGHT-DAY OUT"]
    kicker(s, cols[0][0], y3, "SPACE")
    s.text(cols[0][0], y3 + 18, 2, INK, "VOYAGER 1: ONE")
    s.text(cols[0][0], y3 + 36, 2, INK, "LIGHT-DAY OUT")
    s.para(cols[0][0], y3 + 60, 310, 1, INK,
           "NASA's Voyager 1 reaches one light-day from Earth, about "
           "16 billion miles, almost 50 years after launch.",
           gap=3)
    voyager(s, cols[0][0], y3 + 96, 310, 64)
    kicker(s, cols[1][0], y3, "WEATHER")
    s.text(cols[1][0], y3 + 18, 2, INK, "CYCLONE AKVAN")
    s.text(cols[1][0], y3 + 36, 2, INK, "NEARS INDIA")
    s.para(cols[1][0], y3 + 60, 310, 1, INK,
           "Cyclone Akvan bears down on India's east coast, due to "
           "cross between Machilipatnam and Puri.",
           gap=3)
    cyclone(s, cols[1][0], y3 + 96, 310, 64)
    kicker(s, cols[2][0], y3, "ECONOMY")
    s.text(cols[2][0], y3 + 18, 2, INK, "FED POINTS TO")
    s.text(cols[2][0], y3 + 36, 2, INK, "MORE HIKES")
    s.para(cols[2][0], y3 + 60, 308, 1, INK,
           "Minutes from the Fed's October meeting show most "
           "officials expect further rate rises if inflation stays "
           "high.",
           gap=3)
    fed_chart(s, cols[2][0], y3 + 96, 308, 64)

    # Footer ticker.
    s.hline(28, 968, W - 56, INK)
    s.text(28, 976, 2, RED, "ALSO TODAY:")
    s.para(28, 992, W - 56, 1, INK,
           "Modi meets the Prince and Princess of Wales in Delhi - "
           "US and Iran exchange fire again as Gulf attacks widen - "
           "Pew: Islam on track to be the world's largest faith by 2035",
           gap=3)


def main():
    out = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")) / "entry.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet = Sheet(W, H, PAPER)
    draw_page(sheet)
    out.write_bytes(png_bytes(sheet))


if __name__ == "__main__":
    main()
