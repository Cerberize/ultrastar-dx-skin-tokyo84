#!/usr/bin/env bash
# ============================================================================
# Tokyo84 — UltraStar Deluxe Theme Uninstaller (Linux & macOS)
# ============================================================================
set -euo pipefail

TARGET_DIR="${1:-}"
THEME_NAME="Tokyo84"

if [[ -z "$TARGET_DIR" ]]; then
  for dir in \
    "$HOME/.ultrastardx" \
    "$HOME/.local/share/ultrastardx" \
    "$HOME/.var/app/eu.usdx.UltraStarDeluxe/config/ultrastardx" \
    "$HOME/Library/Application Support/UltraStarDeluxe" \
    "/Applications/UltraStarDeluxe.app/Contents/Resources" \
    "/usr/local/share/ultrastardx" \
    "/usr/share/ultrastardx"; do
    if [[ -d "$dir/themes/$THEME_NAME" ]] || [[ -f "$dir/themes/$THEME_NAME.ini" ]]; then
      TARGET_DIR="$dir"
      break
    fi
  done
fi

if [[ -z "$TARGET_DIR" ]]; then
  echo "Tokyo84 installation not found automatically. Pass the USDX directory as an argument:"
  echo "  ./uninstall.sh /path/to/ultrastardx"
  exit 1
fi

echo "Removing Tokyo84 from: $TARGET_DIR"
rm -rf "$TARGET_DIR/themes/$THEME_NAME" "$TARGET_DIR/themes/$THEME_NAME.ini"

if [[ -d "$TARGET_DIR/sounds/.tokyo84_backup" ]]; then
  cp -R "$TARGET_DIR/sounds/.tokyo84_backup/." "$TARGET_DIR/sounds/"
  rm -rf "$TARGET_DIR/sounds/.tokyo84_backup"
  echo "  [✓] Restored original sound files."
fi

for cfg in \
  "$TARGET_DIR/config.ini.tokyo84.bak" \
  "$HOME/.ultrastardx/config.ini.tokyo84.bak" \
  "$HOME/Library/Application Support/UltraStarDeluxe/config.ini.tokyo84.bak"; do
  if [[ -f "$cfg" ]]; then
    orig="${cfg%.tokyo84.bak}"
    mv "$cfg" "$orig"
    echo "  [✓] Restored original config.ini: $orig"
  fi
done

echo "Done! Tokyo84 has been cleanly uninstalled."
