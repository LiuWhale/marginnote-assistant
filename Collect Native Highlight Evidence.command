#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "Collecting Codex Companion native highlight evidence..."
echo
echo "Open MarginNote 4 to the target PDF. You may start with text already selected,"
echo "or run this command first and then select a short text span in the PDF within 90 seconds."
echo "The command asks the MN4 plugin to run 高亮下一选区, keeps waiting through the"
echo "next-selection armed state, then collects posted/failed and ZHIGHLIGHTS evidence."
echo

STAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT="$HOME/Desktop/codex-companion-native-highlight-evidence-$STAMP.json"

echo "Evidence output:"
echo "  $OUTPUT"
echo

/usr/bin/python3 "$ROOT/release_acceptance.py" \
  --collect-native-highlight-evidence "$OUTPUT" \
  --try-native-highlight \
  --native-highlight-timeout 90

echo
echo "Evidence command finished."
echo "Use this JSON with:"
echo "  python3 release_acceptance.py --native-highlight-evidence \"$OUTPUT\""
echo
read -r "?Press Return to close..."
