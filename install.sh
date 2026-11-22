#!/usr/bin/env bash
# ============================================================================
# Tokyo84 — UltraStar Deluxe Theme & Sound Pack Installer (Linux & macOS)
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEME_NAME="Tokyo84"
SKIN_NAME="KabukichoMidnight"

TARGET_DIR=""
INSTALL_SOUNDS=true
ACTIVATE_THEME=true
NON_INTERACTIVE=false

# ANSI colors (Kabukicho Midnight vibe)
MAGENTA='\033[1;35m'
CYAN='\033[1;36m'
AMBER='\033[1;33m'
GREEN='\033[1;32m'
DIM='\033[2m'
RESET='\033[0m'

print_banner() {
  printf "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
  printf "${CYAN}  TOKYO84${RESET} ${DIM}東京 ’84${RESET}  —  UltraStar Deluxe Theme Installer\n"
  printf "${DIM}  Kabukicho Midnight · Material Design 3 × 1984 Shinjuku Neon${RESET}\n"
  printf "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n\n"
}

usage() {
  cat <<EOF
Usage: ./install.sh [OPTIONS]

Options:
  --path <dir>       Path to UltraStar Deluxe root or user config directory
  --no-sounds        Skip installing custom 1984 FM/synth UI sound effects
  --no-activate      Do not modify config.ini to activate Tokyo84 automatically
  -y, --yes          Non-interactive mode (accept detected defaults)
  -h, --help         Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --path) TARGET_DIR="${2:-}"; shift 2 ;;
    --no-sounds) INSTALL_SOUNDS=false; shift ;;
    --no-activate) ACTIVATE_THEME=false; shift ;;
    -y|--yes) NON_INTERACTIVE=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

detect_usdx_dir() {
  local candidates=(
    "$HOME/.ultrastardx"
    "$HOME/.local/share/ultrastardx"
    "$HOME/.var/app/eu.usdx.UltraStarDeluxe/config/ultrastardx"
    "$HOME/Library/Application Support/UltraStarDeluxe"
    "/Applications/UltraStarDeluxe.app/Contents/Resources"
    "/usr/local/share/ultrastardx"
    "/usr/share/ultrastardx"
  )
  for dir in "${candidates[@]}"; do
    if [[ -d "$dir" ]]; then
      echo "$dir"
      return 0
    fi
  done
  return 1
}

activate_in_config() {
  local base_dir="$1"
  local config_candidates=(
    "$base_dir/config.ini"
    "$HOME/.ultrastardx/config.ini"
    "$HOME/.var/app/eu.usdx.UltraStarDeluxe/config/ultrastardx/config.ini"
    "$HOME/Library/Application Support/UltraStarDeluxe/config.ini"
  )
  local cfg=""
  for c in "${config_candidates[@]}"; do
    if [[ -f "$c" ]]; then
      cfg="$c"
      break
    fi
  done

  if [[ -z "$cfg" ]]; then
    printf "${AMBER}  [!] config.ini not found — select 'Tokyo84' -> 'KabukichoMidnight' in USDX Options > Themes.${RESET}\n"
    return 0
  fi

  cp "$cfg" "${cfg}.tokyo84.bak"
  python3 - "$cfg" "$THEME_NAME" "$SKIN_NAME" <<'PY'
import re, sys
from pathlib import Path

cfg_path = Path(sys.argv[1])
theme, skin = sys.argv[2], sys.argv[3]
text = cfg_path.read_text(encoding="utf-8", errors="ignore")

def set_key(src: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^{key}\s*=.*$", re.MULTILINE | re.IGNORECASE)
    if pattern.search(src):
        return pattern.sub(f"{key}={value}", src, count=1)
    if "[Themes]" in src:
        return src.replace("[Themes]", f"[Themes]\n{key}={value}", 1)
    return src.rstrip() + f"\n\n[Themes]\n{key}={value}\n"

text = set_key(text, "Theme", theme)
text = set_key(text, "Skin", skin)
cfg_path.write_text(text, encoding="utf-8")
PY
  printf "${GREEN}  [✓] Activated Tokyo84 / KabukichoMidnight in:${RESET} %s\n" "$cfg"
  printf "${DIM}      Backup saved to: %s.tokyo84.bak${RESET}\n" "$cfg"
}

print_banner

if [[ -z "$TARGET_DIR" ]]; then
  if DETECTED="$(detect_usdx_dir)"; then
    TARGET_DIR="$DETECTED"
    printf "${CYAN}  Detected UltraStar Deluxe directory:${RESET} %s\n" "$TARGET_DIR"
  else
    TARGET_DIR="$HOME/.ultrastardx"
    printf "${AMBER}  [!] Could not auto-detect an existing USDX installation.${RESET}\n"
    printf "${DIM}      Defaulting to user profile path: %s${RESET}\n" "$TARGET_DIR"
  fi

  if [[ "$NON_INTERACTIVE" == false ]]; then
    printf "\nPress Enter to install to [%s], or enter a custom path: " "$TARGET_DIR"
    read -r CUSTOM_PATH
    if [[ -n "$CUSTOM_PATH" ]]; then
      TARGET_DIR="$CUSTOM_PATH"
    fi
  fi
fi

THEMES_DEST="$TARGET_DIR/themes"
SOUNDS_DEST="$TARGET_DIR/sounds"

printf "\n${CYAN}Installing theme files...${RESET}\n"
mkdir -p "$THEMES_DEST/$THEME_NAME"
cp "$SCRIPT_DIR/themes/Tokyo84.ini" "$THEMES_DEST/Tokyo84.ini"
cp -R "$SCRIPT_DIR/themes/Tokyo84/." "$THEMES_DEST/$THEME_NAME/"
printf "${GREEN}  [✓] Theme installed to:${RESET} %s\n" "$THEMES_DEST/$THEME_NAME"

if [[ "$INSTALL_SOUNDS" == true ]] && [[ -d "$SCRIPT_DIR/sounds" ]]; then
  mkdir -p "$SOUNDS_DEST"
  if [[ ! -d "$SOUNDS_DEST/.tokyo84_backup" ]]; then
    mkdir -p "$SOUNDS_DEST/.tokyo84_backup"
    for wav in "$SCRIPT_DIR/sounds/"*.wav; do
      base="$(basename "$wav")"
      if [[ -f "$SOUNDS_DEST/$base" ]]; then
        cp "$SOUNDS_DEST/$base" "$SOUNDS_DEST/.tokyo84_backup/$base"
      fi
    done
  fi
  cp "$SCRIPT_DIR/sounds/"*.wav "$SOUNDS_DEST/"
  printf "${GREEN}  [✓] 1984 Tokyo FM/Synth UI sounds installed to:${RESET} %s\n" "$SOUNDS_DEST"
fi

if [[ "$ACTIVATE_THEME" == true ]]; then
  activate_in_config "$TARGET_DIR"
fi

printf "\n${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${GREEN}  Installation complete! Launch UltraStar Deluxe and enjoy Tokyo84.${RESET}\n"
printf "${DIM}  Tip: Open preview/index.html in any browser to inspect all screens.${RESET}\n"
printf "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
