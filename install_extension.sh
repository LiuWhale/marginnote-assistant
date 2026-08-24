#!/bin/zsh
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -d "$SOURCE_DIR/extension/codex.mn.assistant" ]]; then
  EXT_SOURCE="$SOURCE_DIR/extension/codex.mn.assistant"
else
  EXT_SOURCE="$SOURCE_DIR/../extension/codex.mn.assistant"
fi
EXT_TARGETS=(
  "$HOME/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant"
  "$HOME/Library/Containers/QReader.MarginStudyMac/Data/Library/MarginNote Extensions/codex.mn.assistant"
)
DRY_RUN="${CODEX_MN_DRY_RUN:-0}"
COMPANION_HOME="${CODEX_MN_COMPANION_HOME:-$HOME/.codex/marginnote-assistant}"
ACTION_TOKEN_PATH="$COMPANION_HOME/control/web-action-token"

if [[ ! -d "$EXT_SOURCE" ]]; then
  echo "Cannot find extension source: $EXT_SOURCE" >&2
  echo "Run this script from the packaged companion directory, next to ../extension/codex.mn.assistant." >&2
  exit 1
fi

if [[ "$DRY_RUN" == "1" ]]; then
  for EXT_TARGET in "${EXT_TARGETS[@]}"; do
    echo "Dry-run: would install MN4 extension from $EXT_SOURCE to $EXT_TARGET"
  done
  exit 0
fi

if [[ ! -f "$ACTION_TOKEN_PATH" ]] || ! /usr/bin/grep -Eq '^[A-Fa-f0-9]{64}$' "$ACTION_TOKEN_PATH"; then
  echo "Missing or invalid Companion Web action token: $ACTION_TOKEN_PATH" >&2
  echo "Install/start Companion before installing the MarginNote extension." >&2
  exit 1
fi

for EXT_TARGET in "${EXT_TARGETS[@]}"; do
  mkdir -p "$(dirname "$EXT_TARGET")" "$EXT_TARGET"
  /usr/bin/rsync -a --delete "$EXT_SOURCE/" "$EXT_TARGET/"
  /usr/bin/install -m 600 "$ACTION_TOKEN_PATH" "$EXT_TARGET/web-action-token"
  echo "Installed MN4 extension to $EXT_TARGET"
done

echo "Restart MarginNote 4 to load the extension."
