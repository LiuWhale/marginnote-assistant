#!/bin/zsh
set -euo pipefail

TARGET="${CODEX_MN_COMPANION_HOME:-$HOME/.codex/marginnote-assistant}"
DEFAULT_LABEL="com.codex.paper-companion"
LEGACY_LABEL="com.liuwhale.codex-marginnote-assistant"
LABEL="${CODEX_MN_LAUNCH_LABEL:-$DEFAULT_LABEL}"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LEGACY_PLIST="$HOME/Library/LaunchAgents/$LEGACY_LABEL.plist"
DOMAIN="gui/$(id -u)"
DRY_RUN="${CODEX_MN_DRY_RUN:-0}"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "Dry-run: would unload LaunchAgent $LABEL and remove $PLIST"
  exit 0
fi

launchctl bootout "$DOMAIN" "$PLIST" >/dev/null 2>&1 || true
if [[ "$LABEL" != "$LEGACY_LABEL" ]]; then
  launchctl bootout "$DOMAIN" "$LEGACY_PLIST" >/dev/null 2>&1 || true
  launchctl bootout "$DOMAIN/$LEGACY_LABEL" >/dev/null 2>&1 || true
  rm -f "$LEGACY_PLIST"
fi
rm -f "$PLIST" "$TARGET/companion.pid"

echo "Unloaded LaunchAgent $LABEL."
echo "Companion files remain at $TARGET; remove that directory manually only if you no longer need sessions/logs."
