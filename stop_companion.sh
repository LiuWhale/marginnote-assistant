#!/bin/zsh
set -euo pipefail

ROOT="${CODEX_MN_COMPANION_HOME:-$HOME/.codex/marginnote-assistant}"
PIDFILE="$ROOT/companion.pid"
DEFAULT_LABEL="com.codex.paper-companion"
LEGACY_LABEL="com.liuwhale.codex-marginnote-assistant"
LABEL="${CODEX_MN_LAUNCH_LABEL:-$DEFAULT_LABEL}"
DOMAIN="gui/$(id -u)"
PLIST="${CODEX_MN_COMPANION_PLIST:-$HOME/Library/LaunchAgents/$LABEL.plist}"

if [[ ! -f "$PLIST" && -f "$HOME/Library/LaunchAgents/$LEGACY_LABEL.plist" ]]; then
  LABEL="$LEGACY_LABEL"
  PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
fi

if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "$DOMAIN" "$PLIST"
  echo "Stopped Codex MarginNote Companion LaunchAgent"
else
  echo "Codex MarginNote Companion LaunchAgent is not loaded"
fi
rm -f "$PIDFILE"
