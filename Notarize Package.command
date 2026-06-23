#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "Notarizing a signed Codex Companion pkg..."
echo

PACKAGE_PKG=""
for candidate in "$ROOT"/release/CodexCompanion-*-latest.pkg "$ROOT"/CodexCompanion-*-latest.pkg "$ROOT"/../CodexCompanion-*-latest.pkg "$ROOT"/CodexCompanion-*.pkg "$ROOT"/../CodexCompanion-*.pkg; do
  if [[ -f "$candidate" ]]; then
    PACKAGE_PKG="$candidate"
    break
  fi
done

if [[ -z "$PACKAGE_PKG" ]]; then
  echo "Could not find a CodexCompanion signed pkg."
  echo "Build a signed pkg first, then run this command again."
  echo
  read -r "?Press Return to close..."
  exit 1
fi

echo "Package pkg:"
echo "  $PACKAGE_PKG"
echo
echo "Credential options:"
echo "  1. Set NOTARYTOOL_KEYCHAIN_PROFILE to a notarytool profile name."
echo "  2. Or set APPLE_ID, APPLE_TEAM_ID, and APPLE_APP_SPECIFIC_PASSWORD."
echo

/usr/bin/python3 "$ROOT/notarize_pkg.py" "$PACKAGE_PKG"

echo
echo "Notarization command finished."
echo
read -r "?Press Return to close..."
