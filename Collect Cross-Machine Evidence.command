#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "Collecting Codex Companion cross-machine install evidence..."
echo

PACKAGE_ZIP=""
for candidate in "$ROOT"/CodexCompanion-*-dist.zip "$ROOT"/../CodexCompanion-*-dist.zip "$ROOT"/../../CodexCompanion-*-dist.zip; do
  if [[ -f "$candidate" ]]; then
    PACKAGE_ZIP="$candidate"
    break
  fi
done

if [[ -z "$PACKAGE_ZIP" ]]; then
  echo "Could not find the original CodexCompanion-*-dist.zip next to this folder."
  echo "Keep the downloaded zip beside the extracted CodexCompanion folder, then run this command again."
  echo
  read -r "?Press Return to close..."
  exit 1
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT="$HOME/Desktop/codex-companion-cross-machine-evidence-$STAMP.json"

echo "Package zip:"
echo "  $PACKAGE_ZIP"
echo
echo "Evidence output:"
echo "  $OUTPUT"
echo

/usr/bin/python3 "$ROOT/release_acceptance.py" "$PACKAGE_ZIP" --collect-cross-machine-evidence "$OUTPUT"

echo
echo "Evidence command finished."
echo "Copy this JSON file back to the primary machine and run:"
echo "  python3 release_acceptance.py --cross-machine-evidence \"$OUTPUT\""
echo
read -r "?Press Return to close..."
