# Tokyo84 (`KabukichoMidnight`) — UltraStar Deluxe Theme

> **1984 Shinjuku Rain & Neon (Bubble-Era City Pop) × Google Material Design 3 Dark Tonal**

A complete alternative theme, skin, custom 1984 FM/synth sound pack, cross-platform installer suite, and interactive Material 3 web previewer for **UltraStar Deluxe (`USDX` / `USD 110`)**.

---

## Highlights

- **100% UltraStar Deluxe Source Parity**: Verified against official `UltraStar-Deluxe/USDX` `Modern.ini` (**1,721 / 1,721 sections**) and `Blue.ini` (**225 mapped texture slots**).
- **1984 Shinjuku Rain & Neon Artwork**: Four bespoke 16:9 widescreen hero backdrops (`bg_main.jpg`, `bg_song.jpg`, `bg_sing.jpg`, `bg_score.jpg`).
- **Material Design 3 Dark Tonal + Neon Focus**:
  - Deep midnight indigo surfaces (`#0B0D18`, `#131626`, `#1B1F34`) paired with high-contrast 3px glowing neon accent borders (`#FF2E93` Electric Magenta & `#00E5FF` Cyber Cyan) on selected buttons and sliders.
  - Clean left-rail Main Menu with expandable `Tools` flyout (`Stats`, `Editor`, `Options`) and zero-overlap layouts across all sub-menus.
  - 12 custom crisp glyph shortcut keycaps (`Navigate`, `Enter`, `ESC`, `C`, `P`, `M`, `J`, `ALT`, `A-Z`, `1-3`, `INS`, `DEL`) on the bottom legend bar.
- **Hi-Fi Neon Singing Stage**: Colorizable pill-shaped pitch bars (`Gray*`, `NotePlain*`, `NoteBG*`), golden star bursts, glowing lyric ball, and high-contrast dark M3 HUD.
- **Custom 1984 FM / DX7 Synth Audio**: Six synthesized WAV UI sound effects (`Change.wav`, `Click.wav`, `Option.wav`, `Start.wav`, `Back.wav`, `Swoosh.wav`).

---

## Color Palette (`KabukichoMidnight`)

| Token | Hex | RGB | Role |
|---|---|---|---|
| **Background Base** | `#0B0D18` | `11 13 24` | Deep midnight indigo base |
| **M3 Surface** | `#1B1F34` | `27 31 52` | Unselected buttons, HUD panels, lyric bar |
| **M3 Surface High** | `#2A3050` | `42 48 80` | Elevated cards & dialogs |
| **Shinjuku Magenta** | `#FF2E93` | `255 46 147` | Primary focus border/fill, Player 1 lane |
| **Cyber Rain Cyan** | `#00E5FF` | `0 229 255` | Secondary focus, active lyrics, Player 2 lane |
| **Tokyo Tower Amber** | `#FFB300` | `255 179 0` | Golden Notes, perfect stars, gold medals |
| **Yamanote Emerald** | `#00E6A8` | `0 230 168` | Status badges, Player 4 lane |

---

## Installation

### Linux & macOS
```bash
chmod +x install.sh uninstall.sh
./install.sh
```
Non-interactive installation to a custom path:
```bash
./install.sh --path ~/.ultrastardx --yes
```
Cleanly uninstall and restore backed-up `config.ini` and sound files:
```bash
./uninstall.sh
```

### Windows (Double-Click or PowerShell)
Double-click **`install.bat`**, or run in PowerShell:
```powershell
.\install.ps1
```
To uninstall:
```powershell
.\uninstall.ps1
```

### Building a Native Windows `.exe` Installer (Inno Setup 6)
Install [Inno Setup 6](https://jrsoftware.org/isinfo.php) and compile:
```powershell
iscc installer\Tokyo84-Setup.iss
```
Outputs `dist\Tokyo84-USDX-Setup-1.0.0.exe` with automatic USDX folder detection, component selection (Theme / 1984 Synth Sounds / Auto-Activate), and a built-in uninstaller.

---

## Interactive Web Previewer

Preview all five screens (**Main Menu**, **Song Select**, **Singing Stage**, **Score Results**, and **Options**) — with live playback of the synthesized 1984 FM WAV sound effects — using any local static server:

```bash
python3 -m http.server 8080
```
Open `http://localhost:8080/preview/` in your browser.

---

## Project Structure

```text
ultrastar-tokyo-skin/
├── themes/
│   ├── Tokyo84.ini                        # Complete 1,721-section USDX Theme layout
│   └── Tokyo84/
│       ├── KabukichoMidnight.ini          # 225-entry USDX Skin texture mapping
│       ├── bg/                            # 4 bespoke 16:9 1984 Shinjuku backgrounds
│       ├── ui/                            # M3 neon-bordered pills, 12 keycaps, cards, cursor
│       ├── sing/                          # Colorizable Hi-Fi neon pitch bars, stars, HUD
│       ├── icons/                         # Geometric neon menu & song icons
│       └── score/                         # Score bars, rating badges (0-7), medals
├── sounds/                                # Synthesized 1984 FM/DX7 WAV UI SFX
├── preview/                               # Interactive Material 3 web previewer
├── installer/
│   └── Tokyo84-Setup.iss                  # Inno Setup 6 Windows .exe wizard script
├── scripts/
│   ├── generate_assets.py                 # Zero-dependency Python PNG & WAV generator
│   ├── build_tokyo84_ini.py               # Deterministic USDX INI builder
│   └── validate_usdx_theme.py             # Automated parity validator vs USDX source
├── install.sh / uninstall.sh              # Linux & macOS installers
└── install.ps1 / install.bat / uninstall.ps1  # Windows installers
```

---

## Development & Verification

All procedural PNG textures and WAV sound effects require only Python 3.10+ (standard library, zero external dependencies):

```bash
# Regenerate all UI textures and 1984 FM WAV sound effects
python3 scripts/generate_assets.py

# Validate theme & skin integrity against USDX schema
python3 scripts/validate_usdx_theme.py
```

---

## License & Attribution

This project is licensed under the **GNU General Public License v2.0 or later (`GPL-2.0-or-later`)** — see the [LICENSE](LICENSE) file for the full text.

- **Upstream Attribution**: `themes/Tokyo84.ini` is derived from the official `Modern.ini` theme schema of [UltraStar Deluxe (USDX)](https://github.com/UltraStar-Deluxe/USDX), licensed under `GPL-2.0-or-later`.
