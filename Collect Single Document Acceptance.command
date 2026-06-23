#!/bin/zsh
set -euo pipefail
setopt NULL_GLOB

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

TOPICID="$(/usr/bin/defaults read QReader.MarginStudy.easy mindbooks_lasttopicid 2>/dev/null || true)"
BOOKMD5="$(/usr/bin/defaults read QReader.MarginStudy.easy mindbooks_lastbookmd5 2>/dev/null || true)"
TOPICID="${TOPICID//\"/}"
BOOKMD5="${BOOKMD5//\"/}"

if [[ -z "$TOPICID" || -z "$BOOKMD5" ]]; then
  echo "Codex Companion could not read the current MarginNote topic/book."
  echo "Open the target notebook/PDF in MarginNote 4, then run this command again."
  exit 1
fi

STAMP="$(/bin/date +%Y%m%d-%H%M%S)"
OUTPUT="$HOME/Desktop/codex-companion-single-document-acceptance-$STAMP.json"
ACTION_RESULTS="$SCRIPT_DIR/release/evidence/action-results.jsonl"
NATIVE_EVIDENCE=""

for candidate in \
  "$SCRIPT_DIR"/release/evidence/codex-companion-native-highlight-evidence-*.json \
  "$SCRIPT_DIR"/release/codex-companion-native-highlight-evidence-*.json \
  "$HOME"/Desktop/codex-companion-native-highlight-evidence-*.json \
  "$HOME"/Desktop/native-highlight-evidence*.json; do
  if [[ -f "$candidate" ]]; then
    NATIVE_EVIDENCE="$candidate"
    break
  fi
done

ARGS=(
  "single_document_acceptance.py"
  "--topicid" "$TOPICID"
  "--bookmd5" "$BOOKMD5"
  "--events" "$SCRIPT_DIR/events.jsonl"
  "--output" "$OUTPUT"
)

if [[ -f "$ACTION_RESULTS" ]]; then
  ARGS+=("--action-results" "$ACTION_RESULTS")
fi

if [[ -n "$NATIVE_EVIDENCE" ]]; then
  ARGS+=("--native-highlight-evidence" "$NATIVE_EVIDENCE")
fi

echo "Running Codex Companion single-document acceptance..."
echo "topicid=$TOPICID"
echo "bookmd5=$BOOKMD5"
echo "output=$OUTPUT"
echo ""

/usr/bin/python3 "${ARGS[@]}"

echo ""
echo "Wrote: $OUTPUT"
echo "Use it with:"
echo "python3 release_acceptance.py --single-document-evidence '$OUTPUT'"
