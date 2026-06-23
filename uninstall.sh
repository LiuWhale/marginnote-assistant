#!/bin/zsh
set -euo pipefail

PACKAGE_ROOT="$(cd "$(dirname "$0")" && pwd)"
COMPANION_SOURCE="$PACKAGE_ROOT/companion"
INSTALLED_HOME="${CODEX_MN_COMPANION_HOME:-$HOME/.codex/marginnote-assistant}"
EXT_TARGET="$HOME/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant"
DRY_RUN="${CODEX_MN_DRY_RUN:-0}"

if [[ -f "$COMPANION_SOURCE/uninstall_companion.sh" ]]; then
  /bin/zsh "$COMPANION_SOURCE/uninstall_companion.sh"
elif [[ -f "$INSTALLED_HOME/uninstall_companion.sh" ]]; then
  /bin/zsh "$INSTALLED_HOME/uninstall_companion.sh"
else
  LABEL="${CODEX_MN_LAUNCH_LABEL:-com.codex.paper-companion}"
  PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
  DOMAIN="gui/$(id -u)"
  launchctl bootout "$DOMAIN" "$PLIST" >/dev/null 2>&1 || true
  rm -f "$PLIST" "$INSTALLED_HOME/companion.pid"
  echo "Unloaded LaunchAgent $LABEL."
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "Dry-run: would remove MarginNote extension at $EXT_TARGET."
elif [[ "${CODEX_MN_KEEP_EXTENSION:-0}" == "1" ]]; then
  echo "Kept MarginNote extension at $EXT_TARGET because CODEX_MN_KEEP_EXTENSION=1."
elif [[ -d "$EXT_TARGET" ]]; then
  rm -rf "$EXT_TARGET"
  echo "Removed MarginNote extension at $EXT_TARGET."
else
  echo "MarginNote extension was not installed at $EXT_TARGET."
fi

echo "Companion data remains at $INSTALLED_HOME unless you remove that directory manually."
