"""The World in One Day -- Thursday 19 November 2026.

A single 1024x1024 PNG newspaper front page, drawn entirely in code with
the Python standard library only. No network, no files read at run time,
no randomness: two runs write byte-identical output.

The front page leads with the three-way summit in Shenzhen (Trump, Xi and
Putin), then the worldwide rollout of GTA VI, the attack on the Kerch
Bridge, Voyager 1 reaching one light-day from Earth, the EU's 45bn euro
loan plan for Ukraine, and Cyclone Akvan bearing down on India's east
coast -- with the day's other headlines running along the foot of the page.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (247, 243, 232)
INK = (18, 18, 18)
RED = (176, 32, 32)
NAVY = (27, 58, 107)
GREY = (110, 108, 100)
LIGHT = (232, 227, 212)
GOLD = (198, 152, 48)
SKY = (38, 84, 138)
SEA = (24, 68, 96)


class Canvas:
    """A plain RGB framebuffer with a few filled-shape primitives."""

    def __init__(self, w, h, colour):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        for i in range(w * h):
            self.px[i * 3] = colour[0]
            self.px[i * 3 + 1] = colour[1]
            self.px[i * 3 + 2] = colour[2]

    def set(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = colour[0]
            self.px[i + 1] = colour[1]
            self.px[i + 2] = colour[2]

    def rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = colour[0]
                self.px[i + 1] = colour[1]
                self.px[i + 2] = colour[2]

    def hline(self, x, y, w, colour, thick=1):
        self.rect(x, y, w, thick, colour)

    def vline(self, x, y, h, colour, thick=1):
        self.rect(x, y, thick, h, colour)

    def line(self, x0, y0, x1, y1, colour, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.rect(x0 - thick // 2, y0 - thick // 2, thick, thick, colour)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            span = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - span, yy, span * 2 + 1, 1, colour)

    def ring(self, cx, cy, r, colour, thick=2):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            outer = int((r * r - dy * dy) ** 0.5)
            inner2 = (r - thick) * (r - thick) - dy * dy
            inner = int(inner2 ** 0.5) if inner2 > 0 else 0
            self.rect(cx - outer, yy, outer - inner, 1, colour)
            self.rect(cx + inner + 1, yy, outer - inner, 1, colour)

    def triangle(self, x0, y0, x1, y1, x2, y2, colour):
        top = min(y0, y1, y2)
        bot = max(y0, y1, y2)
        for yy in range(top, bot + 1):
            xs = []
            for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2), (x2, y2, x0, y0)):
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by):
                    xs.append(ax + (bx - ax) * (yy - ay) / (by - ay))
            if len(xs) >= 2:
                xa = int(min(xs))
                xb = int(max(xs))
                self.rect(xa, yy, xb - xa + 1, 1, colour)


def png_bytes(canvas):
    """Encode the framebuffer as a PNG (filter 0 per scanline)."""
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", comp)
        + chunk(b"IEND", b"")
    )


# A 5x7 bitmap font, one 7-tuple of 5-bit rows per glyph. Bit 4 is the
# leftmost pixel. Lowercase letters sit on the same 7-row grid; the
# descenders of g, j, p, q and y drop to the bottom rows.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "a": (0x00, 0x00, 0x0E, 0x01, 0x0F, 0x11, 0x0F),
    "b": (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x1E),
    "c": (0x00, 0x00, 0x0E, 0x10, 0x10, 0x11, 0x0E),
    "d": (0x01, 0x01, 0x0F, 0x11, 0x11, 0x11, 0x0F),
    "e": (0x00, 0x00, 0x0E, 0x11, 0x1F, 0x10, 0x0E),
    "f": (0x06, 0x09, 0x08, 0x1E, 0x08, 0x08, 0x08),
    "g": (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "h": (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x11),
    "i": (0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E),
    "j": (0x02, 0x00, 0x06, 0x02, 0x02, 0x12, 0x0C),
    "k": (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
    "l": (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "m": (0x00, 0x00, 0x1A, 0x15, 0x15, 0x15, 0x15),
    "n": (0x00, 0x00, 0x1E, 0x11, 0x11, 0x11, 0x11),
    "o": (0x00, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E),
    "p": (0x00, 0x00, 0x1E, 0x11, 0x1E, 0x10, 0x10),
    "q": (0x00, 0x00, 0x0F, 0x11, 0x0F, 0x01, 0x01),
    "r": (0x00, 0x00, 0x16, 0x19, 0x10, 0x10, 0x10),
    "s": (0x00, 0x00, 0x0F, 0x10, 0x0E, 0x01, 0x1E),
    "t": (0x08, 0x08, 0x1C, 0x08, 0x08, 0x08, 0x06),
    "u": (0x00, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D),
    "v": (0x00, 0x00, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "w": (0x00, 0x00, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "x": (0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11),
    "y": (0x00, 0x00, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "z": (0x00, 0x00, 0x1F, 0x02, 0x04, 0x08, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    '"': (0x0A, 0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00),
    "-": (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "+": (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    "=": (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    "*": (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
    "#": (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
}


# ---- text ----

def text_width(text, scale):
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, scale, colour):
    cx = x
    for ch in text:
        glyph = FONT.get(ch)
        if glyph is None:
            glyph = FONT[" "]
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    cv.rect(cx + col * scale, y + row * scale, scale, scale, colour)
        cx += 6 * scale
    return cx


def centre_text(cv, cx, y, text, scale, colour):
    draw_text(cv, cx - text_width(text, scale) // 2, y, text, scale, colour)


def wrap(text, maxw, scale):
    lines = []
    cur = ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= maxw:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_lines(cv, x, y, lines, scale, colour, leading=None):
    if leading is None:
        leading = 7 * scale + 4
    for ln in lines:
        draw_text(cv, x, y, ln, scale, colour)
        y += leading
    return y


def kicker(cv, x, y, text, colour=RED):
    draw_text(cv, x, y, text, 2, colour)
    return y + 7 * 2 + 6


def headline(cv, x, y, text, maxw, scale, colour=INK):
    lines = wrap(text, maxw, scale)
    return draw_lines(cv, x, y, lines, scale, colour, 7 * scale + 5)


# ---- deterministic pseudo-randomness (fixed seeds, no module state) ----

def lcg(seed):
    state = seed & 0x7FFFFFFF
    while True:
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        yield state


# ---- drawn scenes ----

def draw_skyline(cv, x, y, w, h, colour, seed):
    gen = lcg(seed)
    bx = x
    base = y + h
    while bx < x + w:
        bw = 16 + next(gen) % 22
        bh = h // 3 + next(gen) % (2 * h // 3)
        cv.rect(bx, base - bh, bw, bh, colour)
        if next(gen) % 3 == 0:
            cv.rect(bx + bw // 3, base - bh - 8, 4, 8, colour)
        bx += bw + 4


def draw_flags(cv, x, y, w, h):
    # Three flag panels: United States, China, Russia.
    fw = (w - 16) // 3
    # United States: red field, white stripes, blue canton with dots.
    cv.rect(x, y, fw, h, (178, 34, 52))
    for i in range(1, 6, 2):
        cv.rect(x, y + i * h // 7, fw, h // 7, (245, 245, 240))
    cv.rect(x, y, fw * 2 // 5, h * 4 // 7, NAVY)
    for r in range(4):
        for c in range(4):
            cv.set(x + 4 + c * 7, y + 5 + r * 8, (245, 245, 240))
    # China: red field, one large gold star and four small ones.
    cx = x + fw + 8
    cv.rect(cx, y, fw, h, (222, 41, 16))
    cv.disc(cx + 16, y + 16, 7, GOLD)
    for sx, sy in ((36, 10), (44, 18), (44, 28), (36, 34)):
        cv.disc(cx + sx, y + sy, 3, GOLD)
    # Russia: white, blue and red horizontal bands.
    rx = x + 2 * (fw + 8)
    third = h // 3
    cv.rect(rx, y, fw, third, (245, 245, 240))
    cv.rect(rx, y + third, fw, third, (0, 60, 160))
    cv.rect(rx, y + 2 * third, fw, h - 2 * third, (200, 20, 20))


def draw_neon_city(cv, x, y, w, h):
    cv.rect(x, y, w, h, (16, 12, 40))
    # Synthwave sun with slits.
    cv.disc(x + w // 2, y + h // 3, 34, (255, 80, 160))
    for i in range(4):
        cv.rect(x + w // 2 - 34, y + h // 3 + 6 + i * 7, 68, 3, (16, 12, 40))
    gen = lcg(19)
    bx = x + 6
    base = y + h
    while bx < x + w - 10:
        bw = 22 + next(gen) % 26
        bh = h // 3 + next(gen) % (h // 2)
        cv.rect(bx, base - bh, bw, bh, (8, 8, 18))
        for wy in range(base - bh + 6, base - 6, 12):
            for wx in range(bx + 4, bx + bw - 4, 9):
                if next(gen) % 3 == 0:
                    cv.rect(wx, wy, 4, 5, (0, 220, 220) if next(gen) % 2 else (255, 80, 200))
        bx += bw + 6
    cv.rect(x, base - 4, w, 4, (255, 80, 160))


def draw_bridge(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    cv.disc(x + w - 30, y + 22, 16, (250, 220, 140))
    # Water.
    cv.rect(x, y + h - 26, w, 26, SEA)
    for i in range(5):
        cv.rect(x + 8 + i * 34, y + h - 18 + (i % 2) * 6, 22, 2, (220, 235, 245))
    # Deck with a broken gap and smoke.
    deck_y = y + h - 52
    cv.rect(x + 6, deck_y, w - 12, 7, (240, 240, 235))
    cv.rect(x + w // 2 - 14, deck_y, 28, 7, SKY)
    # Arch and suspenders.
    cv.line(x + 10, deck_y, x + w // 2, y + 18, INK, 3)
    cv.line(x + w - 10, deck_y, x + w // 2, y + 18, INK, 3)
    for fx in (0.25, 0.4, 0.6, 0.75):
        px = int(x + 10 + fx * (w - 20))
        py = int(deck_y - (deck_y - (y + 18)) * (1 - abs(fx - 0.5) * 2) * 0.55)
        cv.vline(px, py, deck_y - py, INK, 2)
    # Smoke plume and flame from the gap.
    cv.disc(x + w // 2, deck_y - 12, 8, (120, 120, 118))
    cv.disc(x + w // 2 + 6, deck_y - 24, 11, (150, 150, 148))
    cv.disc(x + w // 2 - 4, deck_y - 36, 14, (180, 180, 178))
    cv.triangle(x + w // 2 - 8, deck_y, x + w // 2 + 8, deck_y, x + w // 2, deck_y - 16, (255, 140, 30))


def draw_voyager(cv, x, y, w, h):
    cv.rect(x, y, w, h, (10, 12, 30))
    gen = lcg(77)
    for _ in range(46):
        sx = x + 4 + next(gen) % (w - 8)
        sy = y + 4 + next(gen) % (h - 8)
        cv.rect(sx, sy, 2, 2, (240, 240, 235))
    # Sun in the corner.
    cv.disc(x + w - 26, y + 24, 14, GOLD)
    # Probe: gold body, white dish, long boom.
    px, py = x + w // 2 - 10, y + h // 2 - 8
    cv.rect(px, py, 34, 20, GOLD)
    cv.rect(px + 6, py + 6, 10, 8, (120, 90, 20))
    cv.line(px + 34, py + 10, px + 74, py - 14, (240, 240, 235), 2)
    cv.disc(px + 76, py - 15, 4, (240, 240, 235))
    cv.line(px - 6, py + 10, px - 46, py + 26, (200, 200, 195), 2)
    cv.disc(px - 48, py + 27, 5, (180, 180, 175))
    cv.line(px + 10, py + 20, px + 4, py + 44, (240, 240, 235), 2)
    cv.disc(px + 4, py + 46, 4, (240, 240, 235))


def draw_eu_stars(cv, x, y, w, h):
    cv.rect(x, y, w, h, (0, 40, 120))
    cx, cy = x + w // 2, y + h // 2
    r = min(w, h) // 2 - 16
    for k in range(12):
        ang = -math.pi / 2 + k * math.pi / 6
        sx = int(cx + r * math.cos(ang))
        sy = int(cy + r * math.sin(ang))
        cv.disc(sx, sy, 6, GOLD)
        cv.rect(sx - 2, sy - 8, 4, 16, GOLD)
        cv.rect(sx - 8, sy - 2, 16, 4, GOLD)


def draw_cyclone(cv, x, y, w, h):
    cv.rect(x, y, w, h, (8, 46, 66))
    cx, cy = x + w // 2, y + h // 2
    for arm in range(3):
        for step in range(26):
            t = step / 25.0
            rad = 8 + t * (min(w, h) // 2 - 10)
            ang = arm * 2.094 + t * 5.2
            sx = int(cx + rad * math.cos(ang))
            sy = int(cy + rad * math.sin(ang))
            cv.disc(sx, sy, 5, (230, 240, 245))
    cv.disc(cx, cy, 12, (8, 46, 66))
    cv.ring(cx, cy, 12, (230, 240, 245), 2)
    # Rain bands at the edges.
    for i in range(6):
        cv.vline(x + 12 + i * 16, y + h - 22, 14, (150, 190, 210), 2)


def draw_vangogh(cv, x, y, w, h):
    cv.rect(x, y, w, h, GOLD)
    cv.rect(x + 6, y + 6, w - 12, h - 12, (18, 32, 86))
    gen = lcg(1904)
    for _ in range(26):
        sx = x + 12 + next(gen) % (w - 24)
        sy = y + 12 + next(gen) % (h - 24)
        cv.disc(sx, sy, 3, (250, 210, 80))
    # Swirling strokes: two clusters of arcs.
    for i in range(3):
        cv.ring(x + w // 3, y + h // 2, 8 + i * 7, (250, 210, 80), 3)
    for i in range(2):
        cv.ring(x + 2 * w // 3, y + h // 3, 6 + i * 6, (250, 210, 80), 3)
    # Cypress on the right.
    cv.triangle(x + w - 40, y + h - 8, x + w - 18, y + h - 8, x + w - 29, y + 16, (8, 40, 20))
    # Sunflowers at the base.
    for i in range(3):
        fx = x + 18 + i * 26
        cv.disc(fx, y + h - 22, 7, (250, 200, 40))
        cv.disc(fx, y + h - 22, 3, (90, 50, 10))


# ---- the front page ----

def compose():
    cv = Canvas(W, H, PAPER)
    m = 36
    right = W - m
    # Top rule and masthead.
    cv.hline(m, 22, right - m, INK, 3)
    centre_text(cv, W // 2, 34, "THE WORLD IN ONE DAY", 6, INK)
    cv.hline(m, 86, right - m, RED, 4)
    centre_text(cv, W // 2, 98, "THURSDAY, 19 NOVEMBER 2026", 2, RED)
    cv.hline(m, 120, right - m, INK, 2)

    # Lead story: the Shenzhen summit (left, wide).
    lx = m
    lw = 600
    y = kicker(cv, lx, 136, "SUMMIT IN SHENZHEN")
    y = headline(cv, lx, y, "TRUMP, XI AND PUTIN MEET IN SHENZHEN", lw, 4)
    y = draw_lines(cv, lx, y + 6, wrap(
        "The three leaders gather for trilateral talks at the APEC summit, "
        "after Xi hugged Trump on the tarmac on his arrival in China.",
        lw, 2), 2, INK)
    draw_flags(cv, lx, y + 10, lw, 92)
    draw_skyline(cv, lx, y + 112, lw, 62, INK, 2026)

    # Second story: GTA VI (right, narrow, dark panel).
    rx = lx + lw + 24
    rw = right - rx
    cv.rect(rx - 12, 130, rw + 24, 330, NAVY)
    y2 = kicker(cv, rx, 146, "VICE CITY OPENS", GOLD)
    y2 = headline(cv, rx, y2, "GTA VI ROLLS OUT WORLDWIDE", rw, 3, (245, 245, 240))
    draw_neon_city(cv, rx, y2 + 8, rw, 118)
    draw_lines(cv, rx, y2 + 134, wrap(
        "After a 13-year wait, Grand Theft Auto VI begins its global rollout "
        "and gamers pour into Vice City.", rw, 2), 2, (235, 235, 230))

    # Divider.
    cv.hline(m, 478, right - m, INK, 2)

    # Middle band: three stories.
    cols = [(m, 300), (m + 324, 300), (m + 648, 304)]
    # Bridge.
    x, w = cols[0]
    y = kicker(cv, x, 494, "CRIMEA")
    y = headline(cv, x, y, "KERCH BRIDGE HIT AGAIN", w, 3)
    draw_bridge(cv, x, y + 6, w, 92)
    draw_lines(cv, x, y + 106, wrap(
        "Russian officials say the Crimean Bridge was attacked again overnight.",
        w, 2), 2, INK)
    # Voyager.
    x, w = cols[1]
    y = kicker(cv, x, 494, "DEEP SPACE")
    y = headline(cv, x, y, "VOYAGER 1 REACHES ONE LIGHT-DAY", w, 3)
    draw_voyager(cv, x, y + 6, w, 92)
    draw_lines(cv, x, y + 106, wrap(
        "NASA says the probe passed the mark this morning.", w, 2), 2, INK)
    # EU loan.
    x, w = cols[2]
    y = kicker(cv, x, 494, "BRUSSELS")
    y = headline(cv, x, y, "EU PLANS 45BN LOAN FOR UKRAINE", w, 3)
    draw_eu_stars(cv, x, y + 6, w, 92)
    draw_lines(cv, x, y + 106, wrap(
        "The EU proposes a 45bn euro loan for Ukraine.", w, 2), 2, INK)

    # Divider.
    cv.hline(m, 752, right - m, INK, 2)

    # Bottom band: cyclone (left) and Van Gogh (right).
    y = kicker(cv, m, 768, "WEATHER")
    y = headline(cv, m, y, "CYCLONE AKVAN NEARS INDIA", 560, 3)
    draw_cyclone(cv, m, y + 6, 250, 92)
    draw_lines(cv, m + 266, y + 6, wrap(
        "Akvan is likely to cross between Machilipatnam and Puri, officials say.",
        300, 2), 2, INK)
    bx = m + 580
    y = kicker(cv, bx, 768, "ART MARKET", GOLD)
    y = headline(cv, bx, y, "VAN GOGH SELLS FOR $190.4M", right - bx, 3)
    draw_vangogh(cv, bx, y + 6, 170, 92)
    draw_lines(cv, bx + 182, y + 6, wrap(
        "A record price after a row over its Nazi-era past.",
        right - bx - 182, 2), 2, INK)

    # Footer ticker.
    cv.hline(m, 952, right - m, INK, 2)
    draw_lines(cv, m, 964, wrap(
        "ALSO TODAY: JEFFRIES FOR SPEAKER * ANTHROPIC $1.4TN DEBUT * FED "
        "POINTS TO MORE HIKES * MYANMAR VERDICT DUE * GAZA INCURSION * "
        "US-IRAN CLASH IN GULF",
        right - m, 2), 2, GREY)
    centre_text(cv, W // 2, 1006, "Drawn from the day's reporting - 19 November 2026", 1, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(compose())
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
