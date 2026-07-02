#!/bin/zsh
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -d "$SOURCE_DIR/extension/codex.mn.assistant" ]]; then
  EXT_SOURCE="$SOURCE_DIR/extension/codex.mn.assistant"
else
  EXT_SOURCE="$SOURCE_DIR/../extension/codex.mn.assistant"
fi
EXT_TARGET="$HOME/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant"
DRY_RUN="${CODEX_MN_DRY_RUN:-0}"

if [[ ! -d "$EXT_SOURCE" ]]; then
  echo "Cannot find extension source: $EXT_SOURCE" >&2
  echo "Run this script from the packaged companion directory, next to ../extension/codex.mn.assistant." >&2
  exit 1
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "Dry-run: would install MN4 extension from $EXT_SOURCE to $EXT_TARGET"
  exit 0
fi

mkdir -p "$(dirname "$EXT_TARGET")" "$EXT_TARGET"
/usr/bin/rsync -a --delete "$EXT_SOURCE/" "$EXT_TARGET/"

echo "Installed MN4 extension to $EXT_TARGET"
echo "Restart MarginNote 4 to load the extension."
