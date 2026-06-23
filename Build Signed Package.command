#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "Building a signed Codex Companion pkg..."
echo

PACKAGE_ZIP=""
for candidate in "$ROOT"/release/CodexCompanion-*-latest-dist.zip "$ROOT"/CodexCompanion-*-latest-dist.zip "$ROOT"/../CodexCompanion-*-latest-dist.zip "$ROOT"/CodexCompanion-*-dist.zip "$ROOT"/../CodexCompanion-*-dist.zip; do
  if [[ -f "$candidate" ]]; then
    PACKAGE_ZIP="$candidate"
    break
  fi
done

if [[ -z "$PACKAGE_ZIP" ]]; then
  echo "Could not find a CodexCompanion release zip."
  echo "Keep CodexCompanion-*-dist.zip beside this folder, then run this command again."
  echo
  read -r "?Press Return to close..."
  exit 1
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT="$HOME/Desktop/CodexCompanion-signed-$STAMP.pkg"

echo "Package zip:"
echo "  $PACKAGE_ZIP"
echo
echo "Signed pkg output:"
echo "  $OUTPUT"
echo

/usr/bin/python3 "$ROOT/build_pkg.py" "$PACKAGE_ZIP" --output "$OUTPUT" --auto-sign

echo
echo "Signed package command finished."
echo
read -r "?Press Return to close..."
