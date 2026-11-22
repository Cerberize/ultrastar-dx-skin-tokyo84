#!/usr/bin/env python3
"""
Tokyo84 — UltraStar Deluxe Complete Texture & 80s FM Synth Sound Generator
Zero external dependencies (Python 3.10+ stdlib only).

Generates EVERY texture required by UltraStar Deluxe (verified against
UltraStar-Deluxe/USDX Modern.ini & Blue.ini) plus 1984 DX7/FM UI WAVs.

Colorization rule in USDX:
  - Textures drawn with `Type = Colorized` (pitch bars, Leiste1, ScoreLevel, etc.)
    MUST be white/bright-grayscale with alpha so OpenGL glColor tinting produces
    pure, vivid neon colors without muddy color multiplication.
  - Textures drawn with `Type = Transparent` or `Plain` carry full Kabukicho
    Midnight Material Design 3 Dark Tonal + Neon RGBA colors.
"""

from __future__ import annotations

import math
import struct
import wave
import zlib
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
THEME_DIR = ROOT / "themes" / "Tokyo84"
SOUNDS_DIR = ROOT / "sounds"

# ---------------------------------------------------------------------------
# Color Palette — Kabukicho Midnight (Material 3 Dark Tonal + 80s Neon Focus)
# ---------------------------------------------------------------------------
COL_BG_DEEP = (11, 13, 24)        # #0B0D18 Deep Indigo Night
COL_SURFACE_1 = (19, 22, 38)      # #131626 M3 Surface Container Low
COL_SURFACE_2 = (27, 31, 52)      # #1B1F34 M3 Surface Container
COL_SURFACE_3 = (37, 42, 69)      # #252A45 M3 Surface Container High
COL_OUTLINE = (72, 79, 118)       # #484F76 M3 Outline Variant
COL_MAGENTA = (255, 46, 147)      # #FF2E93 Electric Shinjuku Magenta
COL_CYAN = (0, 229, 255)          # #00E5FF Cyber Rain Cyan
COL_AMBER = (255, 179, 0)         # #FFB300 Tokyo Tower Golden Amber
COL_WHITE = (244, 246, 255)       # #F4F6FF Crisp Off-White
COL_PURE_WHITE = (255, 255, 255)  # #FFFFFF Pure White (for USDX Colorized slots)
COL_EMERALD = (0, 230, 168)       # #00E6A8 Yamanote Mint
COL_VIOLET = (179, 136, 255)      # #B388FF Shibuya Violet


# ---------------------------------------------------------------------------
# Minimal Pure-Python RGBA PNG Writer
# ---------------------------------------------------------------------------
def write_png(path: Path, width: int, height: int, pixels: bytearray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * stride : (y + 1) * stride])

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), level=6))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png_bytes)


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if v < lo else (hi if v > hi else v)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_rgb(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[float, float, float]:
    t = clamp(t)
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


def sdf_rounded_box(px: float, py: float, bx: float, by: float, r: float) -> float:
    qx = abs(px) - bx + r
    qy = abs(py) - by + r
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r


def sdf_circle(px: float, py: float, r: float) -> float:
    return math.hypot(px, py) - r


def sdf_star5(px: float, py: float, r: float, rf: float = 0.45) -> float:
    angle = math.atan2(py, px) - math.pi / 2.0
    dist = math.hypot(px, py)
    sector = 2.0 * math.pi / 5.0
    a = ((angle % sector) + sector) % sector
    if a > sector * 0.5:
        a = sector - a
    t = a / (sector * 0.5)
    edge_r = r * (1.0 - (1.0 - rf) * (t ** 0.85))
    return dist - edge_r


def render_canvas(
    width: int,
    height: int,
    shader: Callable[[float, float, int, int], tuple[float, float, float, float]],
) -> bytearray:
    buf = bytearray(width * height * 4)
    idx = 0
    for y in range(height):
        py = y + 0.5
        for x in range(width):
            px = x + 0.5
            r, g, b, a = shader(px, py, width, height)
            buf[idx] = int(clamp(r, 0, 255))
            buf[idx + 1] = int(clamp(g, 0, 255))
            buf[idx + 2] = int(clamp(b, 0, 255))
            buf[idx + 3] = int(clamp(a, 0, 255))
            idx += 4
    return buf


# ---------------------------------------------------------------------------
# USDX Colorizable (Pure White/Grayscale + Alpha) Shaders
# ---------------------------------------------------------------------------
def make_colorizable_pill(
    width: int,
    height: int,
    radius: float | None = None,
    border_only: bool = False,
    soft_glow: bool = False,
    high_contrast_border: bool = False,
) -> bytearray:
    """
    Pure white/grayscale rounded pill so USDX `Color` / `DColor` tints it cleanly.
    When `high_contrast_border=True`, renders a darker tonal interior (lum ~145)
    with a crisp 3px pure-white rim (lum 255) + outer bloom so selected buttons
    get a vivid glowing neon accent border and huge contrast vs unselected pills!
    """
    pad = 4.0 if soft_glow else 2.0
    bx = width * 0.5 - pad
    by = height * 0.5 - pad
    rad = radius if radius is not None else min(bx, by)

    def shader(x: float, y: float, w: int, h: int):
        cx = x - w * 0.5
        cy = y - h * 0.5
        d = sdf_rounded_box(cx, cy, bx, by, rad)
        v = y / h
        if d <= 0.0:
            if border_only:
                if d > -2.8:
                    return (255.0, 255.0, 255.0, 248.0)
                return (220.0, 220, 230.0, 60.0)
            if high_contrast_border:
                # Crisp 3px bright pure-white rim -> tints into vivid neon accent border!
                if d > -3.2:
                    return (255.0, 255.0, 255.0, 255.0)
                # Subtle inner bevel highlight
                if d > -4.6:
                    return (210.0, 210.0, 218.0, 232.0)
                # Darker tonal body so white text stays ultra-legible & border pops
                lum = lerp(168.0, 128.0, v)
                return (lum, lum, lum, 226.0)
            lum = lerp(255.0, 226.0, v)
            if d > -2.0:
                lum = 255.0
            return (lum, lum, lum, 242.0)
        else:
            if soft_glow:
                g = math.exp(-d * 0.58) * (0.62 if high_contrast_border else 0.45)
                return (255.0, 255.0, 255.0, g * 255.0)
            aa = clamp(1.0 - d)
            return (255.0, 255.0, 255.0, aa * 220.0)

    return render_canvas(width, height, shader)


def make_colorizable_note(
    width: int,
    height: int,
    mode: str = "sung",  # sung | plain | glow
    cap: str = "full",   # full | left | mid | right
) -> bytearray:
    """
    White/grayscale Hi-Fi Neon Pill pitch bar for USDX's player-color tinting:
      - sung  (GrayLeft/Mid/Right): bright glowing neon tube with white-hot core
      - plain (NotePlainLeft/Mid/Right): clean translucent track with crisp neon rim
      - glow  (NoteBGLeft/Mid/Right): soft outer neon bloom halo
    """
    pad_y = 5.0 if mode == "glow" else 4.0
    pad_x = 4.0 if cap == "full" else 0.0
    by = height * 0.5 - pad_y
    rad = by

    def shader(x: float, y: float, w: int, h: int):
        cy = y - h * 0.5
        if cap == "full":
            d = sdf_rounded_box(x - w * 0.5, cy, w * 0.5 - pad_x, by, rad)
        elif cap == "left":
            if x >= rad + pad_x:
                d = abs(cy) - by
            else:
                d = math.hypot(x - (rad + pad_x), max(abs(cy) - (by - rad), 0.0)) - rad
        elif cap == "right":
            if x <= w - (rad + pad_x):
                d = abs(cy) - by
            else:
                d = math.hypot(x - (w - rad - pad_x), max(abs(cy) - (by - rad), 0.0)) - rad
        else:
            d = abs(cy) - by

        if mode == "glow":
            if d <= 0.0:
                return (255.0, 255.0, 255.0, 95.0)
            bloom = math.exp(-d * 0.42) * 0.65
            return (255.0, 255.0, 255.0, bloom * 255.0)
        elif mode == "plain":
            if d <= 0.0:
                if d > -2.4:
                    return (255.0, 255.0, 255.0, 235.0)
                return (210.0, 210.0, 220.0, 125.0)
            aa = clamp(1.0 - d)
            return (255.0, 255.0, 255.0, aa * 210.0)
        else:  # sung
            if d <= 0.0:
                core = math.exp(-((cy / (by * 0.58)) ** 2))
                lum = lerp(225.0, 255.0, core)
                return (lum, lum, lum, 252.0)
            bloom = math.exp(-d * 0.55) * 0.55
            aa = clamp(1.0 - d)
            return (255.0, 255.0, 255.0, max(aa * 252.0, bloom * 255.0))

    return render_canvas(width, height, shader)


# ---------------------------------------------------------------------------
# Full-Color Material 3 Dark Tonal + Neon UI Shaders
# ---------------------------------------------------------------------------
def make_surface_card(
    width: int,
    height: int,
    radius: float = 18.0,
    alpha_fill: float = 232.0,
    border_accent: tuple[int, int, int] = COL_OUTLINE,
    top_accent_bar: bool = False,
) -> bytearray:
    pad = 2.0
    bx = width * 0.5 - pad
    by = height * 0.5 - pad

    def shader(x: float, y: float, w: int, h: int):
        d = sdf_rounded_box(x - w * 0.5, y - h * 0.5, bx, by, min(radius, bx, by))
        u = clamp(x / w)
        v = clamp(y / h)
        if d <= 0.0:
            r, g, b = lerp_rgb(COL_SURFACE_2, COL_SURFACE_1, v)
            if top_accent_bar and y < pad + 3.5:
                neon = lerp_rgb(COL_MAGENTA, COL_CYAN, u)
                return (neon[0], neon[1], neon[2], 248.0)
            if d > -1.6:
                bt = clamp((d + 1.6) / 1.6)
                r = lerp(r, border_accent[0], bt * 0.85)
                g = lerp(g, border_accent[1], bt * 0.85)
                b = lerp(b, border_accent[2], bt * 0.85)
            return (r, g, b, alpha_fill)
        elif d < 2.0:
            aa = clamp(1.0 - d)
            return (border_accent[0], border_accent[1], border_accent[2], aa * alpha_fill * 0.65)
        return (0.0, 0.0, 0.0, 0.0)

    return render_canvas(width, height, shader)


def make_gradient_bar(
    width: int,
    height: int,
    c1: tuple[int, int, int],
    c2: tuple[int, int, int],
    radius: float = 8.0,
    alpha: float = 240.0,
) -> bytearray:
    bx = width * 0.5 - 1.0
    by = height * 0.5 - 1.0

    def shader(x: float, y: float, w: int, h: int):
        d = sdf_rounded_box(x - w * 0.5, y - h * 0.5, bx, by, min(radius, bx, by))
        r, g, b = lerp_rgb(c1, c2, x / w)
        if d <= 0.0:
            return (r, g, b, alpha)
        aa = clamp(1.0 - d)
        return (r, g, b, aa * alpha)

    return render_canvas(width, height, shader)


def make_star(size: int, color: tuple[int, int, int], filled: bool = True, glow: bool = True) -> bytearray:
    radius = size * 0.36

    def shader(x: float, y: float, w: int, h: int):
        cx = x - w * 0.5
        cy = y - h * 0.5
        d = sdf_star5(cx, cy, radius, 0.44)
        if d <= 0.0:
            if filled:
                center_boost = clamp(1.0 - math.hypot(cx, cy) / radius)
                r = lerp(color[0], 255.0, center_boost * 0.65)
                g = lerp(color[1], 255.0, center_boost * 0.65)
                b = lerp(color[2], 255.0, center_boost * 0.65)
                return (r, g, b, 252.0)
            else:
                if d > -2.4:
                    return (color[0], color[1], color[2], 190.0)
                return (COL_SURFACE_1[0], COL_SURFACE_1[1], COL_SURFACE_1[2], 120.0)
        else:
            if glow and filled:
                g_val = math.exp(-d * 0.22) * 0.75
                return (color[0], color[1], color[2], g_val * 255.0)
            aa = clamp(1.0 - d)
            return (color[0], color[1], color[2], aa * 180.0)

    return render_canvas(size, size, shader)


def make_glow_orb(size: int, color: tuple[int, int, int]) -> bytearray:
    r_core = size * 0.24

    def shader(x: float, y: float, w: int, h: int):
        cx = x - w * 0.5
        cy = y - h * 0.5
        d = sdf_circle(cx, cy, r_core)
        if d <= 0.0:
            t = clamp(1.0 - math.hypot(cx, cy) / r_core)
            return (lerp(color[0], 255.0, t), lerp(color[1], 255.0, t), lerp(color[2], 255.0, t), 255.0)
        g = math.exp(-d * 0.28) * 0.85
        return (color[0], color[1], color[2], g * 255.0)

    return render_canvas(size, size, shader)


def make_cursor(size: int = 48, pressed: bool = False) -> bytearray:
    accent = COL_AMBER if pressed else COL_MAGENTA

    def shader(x: float, y: float, w: int, h: int):
        px = x - 4.0
        py = y - 4.0
        if px < 0 or py < 0:
            return (0.0, 0.0, 0.0, 0.0)
        in_wedge = (py >= 0.38 * px) and (px >= 0.38 * py) and (px + py <= 36.0)
        if in_wedge:
            t = clamp((px + py) / 36.0)
            c = lerp_rgb(COL_WHITE, COL_CYAN, t)
            border = (py - 0.38 * px < 2.2) or (px - 0.38 * py < 2.2) or (36.0 - (px + py) < 2.2)
            if border:
                return (accent[0], accent[1], accent[2], 255.0)
            return (c[0], c[1], c[2], 245.0)
        return (0.0, 0.0, 0.0, 0.0)

    return render_canvas(size, size, shader)


def make_arrow(size: int = 48, direction: str = "right") -> bytearray:
    r_outer = size * 0.42

    def shader(x: float, y: float, w: int, h: int):
        cx = x - w * 0.5
        cy = y - h * 0.5
        dc = sdf_circle(cx, cy, r_outer)
        if dc > 2.0:
            return (0.0, 0.0, 0.0, 0.0)
        fx = cx if direction == "right" else -cx
        d_chev = abs(abs(cy) + (fx - 4.5))
        in_chev = (-6.0 <= fx <= 6.0) and (abs(cy) <= 10.0) and (d_chev < 2.2)
        if dc <= 0.0:
            if in_chev:
                return (COL_CYAN[0], COL_CYAN[1], COL_CYAN[2], 255.0)
            if dc > -1.6:
                return (COL_CYAN[0], COL_CYAN[1], COL_CYAN[2], 200.0)
            return (COL_SURFACE_2[0], COL_SURFACE_2[1], COL_SURFACE_2[2], 225.0)
        aa = clamp(1.0 - dc)
        return (COL_CYAN[0], COL_CYAN[1], COL_CYAN[2], aa * 160.0)

    return render_canvas(size, size, shader)


# Crisp 5x7 pixel font for USDX bottom-bar shortcut keycaps
PIXEL_FONT: dict[str, list[str]] = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
}


def make_keycap(label: str, accent: tuple[int, int, int] = COL_CYAN, width: int = 44, height: int = 34) -> bytearray:
    """Clean M3 dark keycap pill with crisp legible shortcut glyph (arrows, Enter, ESC, C, etc.)."""
    bx = width * 0.5 - 2.0
    by = height * 0.5 - 2.0

    # Pre-rasterize glyph mask onto (width x height) boolean grid
    mask = [[False] * width for _ in range(height)]

    def plot(px: int, py: int) -> None:
        if 0 <= px < width and 0 <= py < height:
            mask[py][px] = True

    if label == "NAVI":
        # Four-way directional arrows (up/down/left/right)
        cx, cy = width // 2, height // 2
        for i in range(4):
            # Up triangle
            for dx in range(-i, i + 1):
                plot(cx + dx, cy - 9 + i)
            # Down triangle
            for dx in range(-i, i + 1):
                plot(cx + dx, cy + 9 - i)
            # Left triangle
            for dy in range(-i, i + 1):
                plot(cx - 11 + i, cy + dy)
            # Right triangle
            for dy in range(-i, i + 1):
                plot(cx + 11 - i, cy + dy)
        # Center square
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                plot(cx + dx, cy + dy)
    elif label == "ENTER":
        # Return arrow symbol: vertical stem down on right, horizontal left, arrowhead left
        cx, cy = width // 2, height // 2
        for y in range(cy - 6, cy + 4):
            plot(cx + 9, y)
            plot(cx + 10, y)
        for x in range(cx - 8, cx + 11):
            plot(x, cy + 2)
            plot(x, cy + 3)
        for i in range(5):
            plot(cx - 8 + i, cy + 2 - i)
            plot(cx - 8 + i, cy + 3 + i)
            plot(cx - 7 + i, cy + 2 - i)
            plot(cx - 7 + i, cy + 3 + i)
    else:
        scale = 2 if len(label) == 1 else 1
        glyph_w = 5 * scale
        gap = 2 if scale == 1 else 3
        total_w = len(label) * glyph_w + (len(label) - 1) * gap
        total_h = 7 * scale
        ox = (width - total_w) // 2
        oy = (height - total_h) // 2
        for idx_c, ch in enumerate(label):
            rows = PIXEL_FONT.get(ch)
            if not rows:
                continue
            gx = ox + idx_c * (glyph_w + gap)
            for ry, row in enumerate(rows):
                for rx, bit in enumerate(row):
                    if bit == "#":
                        for sy in range(scale):
                            for sx in range(scale):
                                plot(gx + rx * scale + sx, oy + ry * scale + sy)

    def shader(x: float, y: float, w: int, h: int):
        cx = x - w * 0.5
        cy = y - h * 0.5
        d = sdf_rounded_box(cx, cy, bx, by, 7.0)
        ix, iy = int(x), int(y)
        if d <= 0.0:
            if 0 <= ix < w and 0 <= iy < h and mask[iy][ix]:
                return (COL_WHITE[0], COL_WHITE[1], COL_WHITE[2], 255.0)
            if d > -1.8:
                return (accent[0], accent[1], accent[2], 240.0)
            return (COL_SURFACE_2[0], COL_SURFACE_2[1], COL_SURFACE_2[2], 240.0)
        aa = clamp(1.0 - d)
        return (accent[0], accent[1], accent[2], aa * 180.0)

    return render_canvas(width, height, shader)


def make_transparent_pixel() -> bytearray:
    return bytearray([0, 0, 0, 0])


def make_menu_icon(size: int, kind: str, accent: tuple[int, int, int]) -> bytearray:
    rad = size * 0.24
    half = size * 0.42

    def shader(x: float, y: float, w: int, h: int):
        cx = x - w * 0.5
        cy = y - h * 0.5
        d_box = sdf_rounded_box(cx, cy, half, half, rad)
        if d_box > 4.0:
            return (0.0, 0.0, 0.0, 0.0)

        scale = size / 96.0
        sx, sy = cx / scale, cy / scale
        glyph = False
        if kind == "sing":
            d_mic = sdf_rounded_box(sx, sy + 5.0, 8.0, 14.0, 8.0)
            d_arc = abs(math.hypot(sx, sy + 2.0) - 15.0) < 2.6 and sy > -2.0
            d_stem = abs(sx) < 2.4 and 13.0 <= sy <= 23.0
            d_base = abs(sy - 23.0) < 2.4 and abs(sx) <= 10.0
            glyph = (d_mic <= 0.0) or d_arc or d_stem or d_base
        elif kind == "party":
            glyph = (
                sdf_star5(sx - 8.0, sy - 6.0, 11.0, 0.45) <= 0.0
                or sdf_star5(sx + 12.0, sy + 8.0, 8.5, 0.45) <= 0.0
                or sdf_circle(sx + 11.0, sy - 13.0, 4.0) <= 0.0
            )
        elif kind == "stats":
            b1 = sdf_rounded_box(sx + 14.0, sy - 6.0, 4.5, 10.0, 2.5) <= 0.0
            b2 = sdf_rounded_box(sx, sy - 1.0, 4.5, 15.0, 2.5) <= 0.0
            b3 = sdf_rounded_box(sx - 14.0, sy - 10.0, 4.5, 6.0, 2.5) <= 0.0
            glyph = b1 or b2 or b3
        elif kind == "options":
            for ry, kx in [(-12.0, -7.0), (0.0, 9.0), (12.0, -3.0)]:
                if abs(sy - ry) < 2.2 and abs(sx) <= 18.0:
                    glyph = True
                if sdf_circle(sx - kx, sy - ry, 4.8) <= 0.0:
                    glyph = True
        elif kind == "quit":
            ring = abs(math.hypot(sx, sy) - 14.0) < 2.6 and not (sy < -5.0 and abs(sx) < 7.0)
            bar = abs(sx) < 2.5 and -19.0 <= sy <= -4.0
            glyph = ring or bar
        elif kind == "duet":
            glyph = (
                (sdf_circle(sx + 8.0, sy, 11.0) <= 0.0 and sdf_circle(sx + 8.0, sy, 7.2) >= 0.0)
                or (sdf_circle(sx - 8.0, sy, 11.0) <= 0.0 and sdf_circle(sx - 8.0, sy, 7.2) >= 0.0)
            )
        elif kind == "video":
            frame = abs(sdf_rounded_box(sx, sy, 17.0, 12.0, 4.0)) < 2.4
            tri = (-5.0 <= sx <= 8.0) and (abs(sy) <= (8.0 - sx) * 0.62)
            glyph = frame or tri
        else:  # medley / default
            r1 = abs(math.hypot(sx + 10.0, sy) - 8.0) < 2.5
            r2 = abs(math.hypot(sx - 10.0, sy) - 8.0) < 2.5
            bar = abs(sy - 9.0) < 2.4 and abs(sx) <= 12.0
            glyph = r1 or r2 or bar

        if d_box <= 0.0:
            if glyph:
                return (COL_WHITE[0], COL_WHITE[1], COL_WHITE[2], 255.0)
            dist_c = math.hypot(cx, cy) / half
            r = lerp(accent[0], COL_SURFACE_1[0], clamp(0.60 + dist_c * 0.35))
            g = lerp(accent[1], COL_SURFACE_1[1], clamp(0.60 + dist_c * 0.35))
            b = lerp(accent[2], COL_SURFACE_1[2], clamp(0.60 + dist_c * 0.35))
            if d_box > -2.0:
                return (accent[0], accent[1], accent[2], 235.0)
            return (r, g, b, 240.0)
        glow = math.exp(-d_box * 0.55) * 0.45
        return (accent[0], accent[1], accent[2], glow * 255.0)

    return render_canvas(size, size, shader)


def make_default_cover(size: int = 320) -> bytearray:
    """1984 Tokyo City Pop vinyl sleeve placeholder cover."""
    def shader(x: float, y: float, w: int, h: int):
        u = x / w
        v = y / h
        cx = x - w * 0.5
        cy = y - h * 0.5
        r, g, b = lerp_rgb((14, 16, 36), (34, 18, 56), v)
        d_sun = math.hypot(cx, cy + h * 0.06) - w * 0.24
        if d_sun <= 0.0:
            sun_t = clamp((y - h * 0.20) / (h * 0.48))
            sr, sg, sb = lerp_rgb(COL_AMBER, COL_MAGENTA, sun_t)
            if not (cy > -h * 0.02 and int(y / 8) % 2 == 0):
                r, g, b = sr, sg, sb
        if v > 0.65:
            gv = (v - 0.65) / 0.35
            if abs((gv * 8.0) % 1.0 - 0.5) > 0.44:
                r, g, b = lerp_rgb((r, g, b), COL_CYAN, 0.65 * gv)
            px = (u - 0.5) / (gv + 0.15)
            if abs((px * 2.5) % 1.0 - 0.5) > 0.46:
                r, g, b = lerp_rgb((r, g, b), COL_MAGENTA, 0.55 * gv)
        if x < 3 or x > w - 3 or y < 3 or y > h - 3:
            r, g, b = lerp_rgb(COL_MAGENTA, COL_CYAN, u)
        return (r, g, b, 255.0)

    return render_canvas(size, size, shader)


def make_medal(size: int, color: tuple[int, int, int]) -> bytearray:
    def shader(x: float, y: float, w: int, h: int):
        cx = x - w * 0.5
        cy = y - h * 0.5
        dc = sdf_circle(cx, cy, size * 0.40)
        if dc <= 0.0:
            ds = sdf_star5(cx, cy, size * 0.22, 0.45)
            if ds <= 0.0:
                return (COL_WHITE[0], COL_WHITE[1], COL_WHITE[2], 255.0)
            if dc > -3.5:
                return (color[0], color[1], color[2], 255.0)
            return (
                lerp(color[0], COL_SURFACE_1[0], 0.45),
                lerp(color[1], COL_SURFACE_1[1], 0.45),
                lerp(color[2], COL_SURFACE_1[2], 0.45),
                245.0,
            )
        glow = math.exp(-dc * 0.28) * 0.6
        return (color[0], color[1], color[2], glow * 255.0)

    return render_canvas(size, size, shader)


def make_color_picker(size: int = 128) -> bytearray:
    """HSV color picker wheel/square for USDX player color picker."""
    def shader(x: float, y: float, w: int, h: int):
        u = x / w
        v = y / h
        # Rainbow hue horizontally, value vertically
        hue = u * 6.0
        c = 1.0 - v * 0.85
        xv = c * (1.0 - abs((hue % 2.0) - 1.0))
        if hue < 1:
            rgb = (c, xv, 0.0)
        elif hue < 2:
            rgb = (xv, c, 0.0)
        elif hue < 3:
            rgb = (0.0, c, xv)
        elif hue < 4:
            rgb = (0.0, xv, c)
        elif hue < 5:
            rgb = (xv, 0.0, c)
        else:
            rgb = (c, 0.0, xv)
        return (rgb[0] * 255.0, rgb[1] * 255.0, rgb[2] * 255.0, 255.0)

    return render_canvas(size, size, shader)


# ---------------------------------------------------------------------------
# 1984 FM / Analog Synthesizer WAV Generator
# ---------------------------------------------------------------------------
def write_wav(path: Path, samples: list[float], sample_rate: int = 44100) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for s in samples:
            frames.extend(struct.pack("<h", int(clamp(s, -1.0, 1.0) * 32767)))
        wf.writeframes(bytes(frames))


def fm_tone(
    freq: float,
    duration: float,
    mod_ratio: float = 2.0,
    mod_index: float = 1.8,
    decay: float = 10.0,
    volume: float = 0.55,
    sr: int = 44100,
) -> list[float]:
    n = int(duration * sr)
    out = []
    for i in range(n):
        t = i / sr
        env = (1.0 - math.exp(-t * 320.0)) * math.exp(-t * decay)
        mod_env = math.exp(-t * decay * 1.4)
        mod = math.sin(2.0 * math.pi * freq * mod_ratio * t) * mod_index * mod_env
        out.append(math.sin(2.0 * math.pi * freq * t + mod) * env * volume)
    return out


def mix_tracks(tracks: list[tuple[float, list[float]]], sr: int = 44100) -> list[float]:
    total = max(int(offset * sr) + len(data) for offset, data in tracks)
    buf = [0.0] * total
    for offset, data in tracks:
        start = int(offset * sr)
        for i, v in enumerate(data):
            buf[start + i] += v
    peak = max((abs(x) for x in buf), default=1.0)
    if peak > 0.92:
        scale = 0.92 / peak
        buf = [x * scale for x in buf]
    return buf


def generate_sounds() -> None:
    print("Synthesizing 1984 Tokyo FM/Synth UI Sound Effects...")
    write_wav(SOUNDS_DIR / "Change.wav", fm_tone(659.25, 0.09, mod_ratio=3.0, mod_index=1.4, decay=38.0, volume=0.42))
    write_wav(SOUNDS_DIR / "Option.wav", mix_tracks([
        (0.0, fm_tone(880.0, 0.08, mod_ratio=2.0, mod_index=1.2, decay=30.0, volume=0.40)),
        (0.035, fm_tone(1108.73, 0.11, mod_ratio=2.0, mod_index=1.0, decay=24.0, volume=0.42)),
    ]))
    notes = [369.99, 466.16, 554.37, 698.46, 830.61]
    write_wav(SOUNDS_DIR / "Start.wav", mix_tracks([
        (i * 0.048, fm_tone(f, 0.55, mod_ratio=2.0, mod_index=1.6, decay=5.5, volume=0.35))
        for i, f in enumerate(notes)
    ]))
    write_wav(SOUNDS_DIR / "Back.wav", mix_tracks([
        (0.0, fm_tone(659.25, 0.09, mod_ratio=1.5, mod_index=0.9, decay=26.0, volume=0.38)),
        (0.045, fm_tone(493.88, 0.14, mod_ratio=1.5, mod_index=0.7, decay=20.0, volume=0.36)),
    ]))
    write_wav(SOUNDS_DIR / "Click.wav", mix_tracks([
        (0.0, fm_tone(1320.0, 0.045, mod_ratio=3.5, mod_index=2.2, decay=70.0, volume=0.42)),
        (0.004, fm_tone(220.0, 0.05, mod_ratio=1.0, mod_index=0.5, decay=55.0, volume=0.25)),
    ]))
    sr = 44100
    dur = 0.24
    n = int(dur * sr)
    swoosh = []
    phase = 0.0
    for i in range(n):
        t = i / sr
        freq = lerp(240.0, 920.0, (t / dur) ** 0.7)
        phase += 2.0 * math.pi * freq / sr
        env = math.sin(math.pi * (t / dur)) ** 1.4
        swoosh.append(math.sin(phase + 0.6 * math.sin(phase * 2.0)) * env * 0.34)
    write_wav(SOUNDS_DIR / "Swoosh.wav", swoosh)


# ---------------------------------------------------------------------------
# Complete USDX Texture Set
# ---------------------------------------------------------------------------
def generate_textures() -> None:
    print("Rendering complete UltraStar Deluxe Tokyo84 texture set...")

    # --- UI Buttons & Surfaces (Rounded Rectangles + High-Contrast Neon Accent Border) ---
    write_png(THEME_DIR / "ui" / "button.png", 280, 52, make_colorizable_pill(280, 52, radius=10.0, soft_glow=True, high_contrast_border=True))
    # `ButtonFade` is a 1x1 transparent PNG so Fade=1 works cleanly without stray white artifacts
    write_png(THEME_DIR / "ui" / "button_fade.png", 1, 1, make_transparent_pixel())
    write_png(THEME_DIR / "ui" / "main_bar.png", 160, 36, make_colorizable_pill(160, 36, radius=8.0, soft_glow=True, high_contrast_border=True))
    write_png(THEME_DIR / "ui" / "select_bg.png", 400, 36, make_colorizable_pill(400, 36, radius=8.0, soft_glow=True, high_contrast_border=True))
    write_png(THEME_DIR / "ui" / "select_frame.png", 140, 140, make_colorizable_pill(140, 140, radius=18.0, border_only=True))

    # Bottom Legend Bars (Leiste1 = Colorizable left accent bar, Leiste2 = Dark M3 right bar)
    write_png(THEME_DIR / "ui" / "leiste1.png", 250, 32, make_colorizable_pill(250, 32, radius=0.0))
    write_png(THEME_DIR / "ui" / "leiste2.png", 550, 32, make_surface_card(550, 32, radius=0.0, alpha_fill=235.0, border_accent=COL_OUTLINE))

    # Dialogs, Popups & Cards
    write_png(THEME_DIR / "ui" / "popup_bg.png", 420, 240, make_surface_card(420, 240, radius=20.0, alpha_fill=244.0, border_accent=COL_CYAN, top_accent_bar=True))
    write_png(THEME_DIR / "ui" / "popup_fg.png", 420, 44, make_gradient_bar(420, 44, COL_MAGENTA, COL_CYAN, radius=12.0, alpha=210.0))
    write_png(THEME_DIR / "ui" / "card_surface.png", 360, 220, make_surface_card(360, 220, radius=18.0, alpha_fill=224.0, border_accent=COL_OUTLINE))
    write_png(THEME_DIR / "ui" / "card_accent.png", 360, 220, make_surface_card(360, 220, radius=18.0, alpha_fill=232.0, border_accent=COL_CYAN, top_accent_bar=True))
    write_png(THEME_DIR / "ui" / "white_rect.png", 32, 32, make_colorizable_pill(32, 32, radius=0.0))
    write_png(THEME_DIR / "ui" / "bg_fade.png", 64, 64, make_surface_card(64, 64, radius=0.0, alpha_fill=234.0, border_accent=COL_BG_DEEP))

    # Cursor, Arrows & Distinct Bottom-Bar Shortcut Keycaps
    write_png(THEME_DIR / "ui" / "cursor.png", 48, 48, make_cursor(48, pressed=False))
    write_png(THEME_DIR / "ui" / "cursor_pressed.png", 48, 48, make_cursor(48, pressed=True))
    write_png(THEME_DIR / "ui" / "arrow_left.png", 48, 48, make_arrow(48, "left"))
    write_png(THEME_DIR / "ui" / "arrow_right.png", 48, 48, make_arrow(48, "right"))

    keycap_specs = [
        ("key_navi.png", "NAVI", COL_CYAN),
        ("key_enter.png", "ENTER", COL_MAGENTA),
        ("key_esc.png", "ESC", COL_AMBER),
        ("key_c.png", "C", COL_CYAN),
        ("key_p.png", "P", COL_CYAN),
        ("key_m.png", "M", COL_CYAN),
        ("key_j.png", "J", COL_CYAN),
        ("key_alt.png", "ALT", COL_CYAN),
        ("key_az.png", "A-Z", COL_CYAN),
        ("key_13.png", "1-3", COL_CYAN),
        ("key_ins.png", "INS", COL_EMERALD),
        ("key_del.png", "DEL", COL_AMBER),
    ]
    for fname, lbl, col in keycap_specs:
        write_png(THEME_DIR / "ui" / fname, 44, 34, make_keycap(lbl, col, 44, 34))

    # Song Cover & Selection Indicators
    write_png(THEME_DIR / "ui" / "song_cover_default.png", 320, 320, make_default_cover(320))
    write_png(THEME_DIR / "ui" / "song_selection.png", 240, 240, make_colorizable_pill(240, 240, radius=16.0, border_only=True))
    write_png(THEME_DIR / "ui" / "avatar_frame.png", 128, 128, make_surface_card(128, 128, radius=18.0, alpha_fill=40.0, border_accent=COL_CYAN))
    write_png(THEME_DIR / "ui" / "no_avatar.png", 128, 128, make_menu_icon(128, "sing", COL_CYAN))

    # --- Singing Screen (ALL Colorizable Pitch Bars + Dark M3 HUD) ---
    # Sung notes (GrayLeft/Mid/Right)
    write_png(THEME_DIR / "sing" / "notes_sung_left.png", 32, 32, make_colorizable_note(32, 32, "sung", "left"))
    write_png(THEME_DIR / "sing" / "notes_sung_mid.png", 32, 32, make_colorizable_note(32, 32, "sung", "mid"))
    write_png(THEME_DIR / "sing" / "notes_sung_right.png", 32, 32, make_colorizable_note(32, 32, "sung", "right"))
    # Unsung notes (NotePlainLeft/Mid/Right)
    write_png(THEME_DIR / "sing" / "notes_plain_left.png", 32, 32, make_colorizable_note(32, 32, "plain", "left"))
    write_png(THEME_DIR / "sing" / "notes_plain_mid.png", 32, 32, make_colorizable_note(32, 32, "plain", "mid"))
    write_png(THEME_DIR / "sing" / "notes_plain_right.png", 32, 32, make_colorizable_note(32, 32, "plain", "right"))
    # Neon bloom glow (NoteBGLeft/Mid/Right)
    write_png(THEME_DIR / "sing" / "notes_bg_left.png", 32, 36, make_colorizable_note(32, 36, "glow", "left"))
    write_png(THEME_DIR / "sing" / "notes_bg_mid.png", 32, 36, make_colorizable_note(32, 36, "glow", "mid"))
    write_png(THEME_DIR / "sing" / "notes_bg_right.png", 32, 36, make_colorizable_note(32, 36, "glow", "right"))

    # Stars, Lyric Ball & Pause
    write_png(THEME_DIR / "sing" / "star_golden.png", 48, 48, make_star(48, COL_AMBER, filled=True, glow=True))
    write_png(THEME_DIR / "sing" / "star_perfect.png", 64, 64, make_star(64, COL_AMBER, filled=True, glow=True))
    write_png(THEME_DIR / "sing" / "star_filled.png", 48, 48, make_star(48, COL_CYAN, filled=True, glow=True))
    write_png(THEME_DIR / "sing" / "star_empty.png", 48, 48, make_star(48, COL_OUTLINE, filled=False, glow=False))
    write_png(THEME_DIR / "sing" / "lyrics_ball.png", 32, 32, make_glow_orb(32, COL_CYAN))
    write_png(THEME_DIR / "sing" / "lyric_active.png", 32, 32, make_glow_orb(32, COL_PURE_WHITE))
    write_png(THEME_DIR / "sing" / "lyric_inactive.png", 32, 32, make_glow_orb(32, COL_OUTLINE))

    # Singing HUD Bars
    write_png(THEME_DIR / "sing" / "lyric_bar.png", 780, 86, make_surface_card(780, 86, radius=16.0, alpha_fill=218.0, border_accent=COL_OUTLINE))
    write_png(THEME_DIR / "sing" / "lyric_bar_duet.png", 780, 74, make_surface_card(780, 74, radius=14.0, alpha_fill=214.0, border_accent=COL_CYAN))
    write_png(THEME_DIR / "sing" / "timebar_bg.png", 780, 22, make_surface_card(780, 22, radius=11.0, alpha_fill=220.0, border_accent=COL_OUTLINE))
    write_png(THEME_DIR / "sing" / "timebar_fill.png", 400, 12, make_gradient_bar(400, 12, COL_MAGENTA, COL_CYAN, radius=6.0))
    write_png(THEME_DIR / "sing" / "score_hud.png", 260, 56, make_surface_card(260, 56, radius=14.0, alpha_fill=224.0, border_accent=COL_CYAN))
    write_png(THEME_DIR / "sing" / "singbar_back.png", 200, 18, make_surface_card(200, 18, radius=9.0, alpha_fill=210.0, border_accent=COL_OUTLINE))
    write_png(THEME_DIR / "sing" / "singbar_bar.png", 200, 18, make_gradient_bar(200, 18, COL_MAGENTA, COL_AMBER, radius=9.0))
    write_png(THEME_DIR / "sing" / "player_badge.png", 44, 44, make_colorizable_pill(44, 44, radius=12.0))
    write_png(THEME_DIR / "sing" / "pause.png", 96, 96, make_surface_card(96, 96, radius=24.0, alpha_fill=230.0, border_accent=COL_AMBER))

    # --- Score & Rating Assets ---
    write_png(THEME_DIR / "score" / "score_level.png", 64, 240, make_colorizable_pill(64, 240, radius=12.0))
    write_png(THEME_DIR / "score" / "score_level_round.png", 64, 32, make_colorizable_pill(64, 32, radius=16.0))
    write_png(THEME_DIR / "score" / "score_glass_box.png", 360, 120, make_surface_card(360, 120, radius=18.0, alpha_fill=190.0, border_accent=COL_CYAN))
    write_png(THEME_DIR / "score" / "score_bar_box.png", 24, 24, make_colorizable_pill(24, 24, radius=6.0))
    write_png(THEME_DIR / "score" / "medal_gold.png", 96, 96, make_medal(96, COL_AMBER))
    write_png(THEME_DIR / "score" / "medal_silver.png", 96, 96, make_medal(96, COL_CYAN))
    write_png(THEME_DIR / "score" / "medal_bronze.png", 96, 96, make_medal(96, COL_MAGENTA))

    # Rating_0..7 badges (progressively brighter neon colors)
    rating_cols = [
        COL_OUTLINE, COL_OUTLINE, COL_VIOLET, COL_CYAN,
        COL_CYAN, COL_EMERALD, COL_MAGENTA, COL_AMBER,
    ]
    for i, rc in enumerate(rating_cols):
        write_png(THEME_DIR / "score" / f"rating_{i}.png", 64, 64, make_medal(64, rc))

    # --- Icons ---
    icon_specs = [
        ("icon_sing.png", "sing", COL_MAGENTA),
        ("icon_party.png", "party", COL_CYAN),
        ("icon_stats.png", "stats", COL_EMERALD),
        ("icon_options.png", "options", COL_VIOLET),
        ("icon_quit.png", "quit", COL_AMBER),
        ("icon_duet.png", "duet", COL_MAGENTA),
        ("icon_video.png", "video", COL_CYAN),
        ("icon_medley.png", "medley", COL_AMBER),
    ]
    for fname, kind, accent in icon_specs:
        write_png(THEME_DIR / "icons" / fname, 64, 64, make_menu_icon(64, kind, accent))

    # --- Color Picker ---
    write_png(THEME_DIR / "ui" / "color_picker.png", 128, 128, make_color_picker(128))


def main() -> None:
    generate_textures()
    generate_sounds()
    print("Done! All Tokyo84 USDX textures & 80s FM synth sounds generated.")


if __name__ == "__main__":
    main()
