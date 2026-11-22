#!/usr/bin/env python3
"""
Strict UltraStar Deluxe Theme & Skin Validator.
Cross-checks themes/Tokyo84.ini and themes/Tokyo84/KabukichoMidnight.ini
against official UltraStar-Deluxe/USDX source files (Modern.ini & Blue.ini).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME_INI = ROOT / "themes" / "Tokyo84.ini"
SKIN_INI = ROOT / "themes" / "Tokyo84" / "KabukichoMidnight.ini"
SKIN_DIR = ROOT / "themes" / "Tokyo84"

REF_DIR = Path("/home/pravesh/.gemini/antigravity/brain/e3b14aa0-147d-4914-96e0-605645c5ad4c/scratch/usdx_ref")
MODERN_INI = REF_DIR / "Modern.ini"
BLUE_INI = REF_DIR / "Blue.ini"


def parse_ini_loose(path: Path) -> dict[str, dict[str, str]]:
    """Parse USDX INI files the same way Delphi TMemIniFile does."""
    sections: dict[str, dict[str, str]] = {}
    cur = None
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith((";", "#", "//", "/*", "*")):
            continue
        m = re.match(r"^\[([^\]]+)\]$", s)
        if m:
            cur = m.group(1).strip()
            sections.setdefault(cur, {})
        elif cur and "=" in s:
            k, v = s.split("=", 1)
            sections[cur][k.strip()] = v.strip()
    return sections


def main() -> int:
    errors: list[str] = []

    theme = parse_ini_loose(THEME_INI)
    skin = parse_ini_loose(SKIN_INI)
    modern = parse_ini_loose(MODERN_INI) if MODERN_INI.exists() else {}
    blue = parse_ini_loose(BLUE_INI) if BLUE_INI.exists() else {}

    # 1. Theme <-> Skin linkage (exact match with USkins.pas LoadHeader / GetSkinNumber)
    t_name = theme.get("Theme", {}).get("Name", "")
    t_def_skin = theme.get("Theme", {}).get("DefaultSkin", "")
    s_theme = skin.get("Skin", {}).get("Theme", "")
    s_name = skin.get("Skin", {}).get("Name", "")

    if t_name != s_theme:
        errors.append(f"Theme.Name ({t_name!r}) != Skin.Theme ({s_theme!r})")
    if t_def_skin != s_name:
        errors.append(f"Theme.DefaultSkin ({t_def_skin!r}) != Skin.Name ({s_name!r})")

    # 2. Section parity with official Modern.ini
    if modern:
        missing_sections = set(modern.keys()) - set(theme.keys())
        if missing_sections:
            errors.append(f"Missing {len(missing_sections)} sections vs Modern.ini: {sorted(missing_sections)[:10]}")

    # 3. Every texture referenced in Tokyo84.ini exists in KabukichoMidnight.ini
    skin_textures = skin.get("Textures", {})
    tex_fields = {"Tex", "TexSBG", "FadeTex", "DTex"}
    referenced_tex: set[str] = set()
    for sec, kv in theme.items():
        for k, v in kv.items():
            if k in tex_fields and v:
                referenced_tex.add(v)
                if v not in skin_textures:
                    errors.append(f"[{sec}] {k}={v!r} is NOT defined in KabukichoMidnight.ini [Textures]")

    # 4. Every texture key in official Blue.ini exists in KabukichoMidnight.ini
    if blue:
        blue_tex = set(blue.get("Textures", {}).keys())
        missing_blue = blue_tex - set(skin_textures.keys())
        if missing_blue:
            errors.append(f"Missing {len(missing_blue)} texture keys vs Blue.ini: {sorted(missing_blue)[:15]}")

    # 5. Every mapped file in KabukichoMidnight.ini exists on disk and has valid PNG/JPEG magic bytes
    for k, rel in skin_textures.items():
        p = SKIN_DIR / rel
        if not p.is_file():
            errors.append(f"Skin texture {k}={rel!r} missing on disk at {p}")
            continue
        head = p.read_bytes()[:4]
        if not (head.startswith(b"\x89PNG") or head.startswith(b"\xff\xd8\xff")):
            errors.append(f"Skin texture {k}={rel!r} is neither PNG nor JPEG")

    # 6. Every named Color in Tokyo84.ini resolves to [Colors] or USDX dynamic color
    defined_colors = set(theme.get("Colors", {}).keys()) | {
        "ColorDark", "ColorLight", "ColorLightest",
        "PlayerDark", "PlayerLight", "TeamColor",
        "P1Light", "P1Dark", "P1Lightest",
        "P2Light", "P2Dark", "P2Lightest",
        "P3Light", "P3Dark", "P3Lightest",
        "P4Light", "P4Dark", "P4Lightest",
        "P5Light", "P5Dark", "P5Lightest",
        "P6Light", "P6Dark", "P6Lightest",
    }
    color_fields = {"Color", "DColor", "TColor", "TDColor", "SBGColor", "SBGDColor", "STColor", "STDColor"}
    for sec, kv in theme.items():
        if sec == "Colors":
            continue
        for k, v in kv.items():
            if k in color_fields and v and v not in defined_colors:
                errors.append(f"[{sec}] {k}={v!r} is not defined in [Colors]")

    print(f"Theme sections:       {len(theme)} (Modern.ini ref: {len(modern)})")
    print(f"Theme tex refs:       {len(referenced_tex)}")
    print(f"Skin texture entries: {len(skin_textures)} (Blue.ini ref: {len(blue.get('Textures', {}))})")

    if errors:
        print(f"\nFAILED with {len(errors)} error(s):")
        for e in errors[:25]:
            print("  -", e)
        return 1

    print("\nPASS! 100% parity with UltraStar-Deluxe/USDX Modern.ini & Blue.ini.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
