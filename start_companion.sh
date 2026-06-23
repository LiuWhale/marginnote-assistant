#!/bin/zsh
set -euo pipefail

ROOT="${CODEX_MN_COMPANION_HOME:-$HOME/.codex/marginnote-assistant}"
LOG="$ROOT/logs/companion.log"
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

mkdir -p "$ROOT/logs" "$ROOT/backups"

PRINT_OUTPUT="$(launchctl print "$DOMAIN/$LABEL" 2>&1 || true)"
if [[ "$PRINT_OUTPUT" == *"Could not find service"* ]] || [[ "$PRINT_OUTPUT" == *"Bad request"* ]]; then
  (
    launchctl bootout "$DOMAIN" "$PLIST" >/dev/null 2>&1 || true
    launchctl bootstrap "$DOMAIN" "$PLIST"
  ) >"$ROOT/logs/launchctl-bootstrap.log" 2>&1 &
fi

launchctl enable "$DOMAIN/$LABEL" >/dev/null 2>&1 || true

for _ in {1..30}; do
  if /usr/bin/curl -fsS http://127.0.0.1:48761/health >/dev/null 2>&1; then
    PID="$(cat "$PIDFILE" 2>/dev/null || true)"
    echo "Codex MarginNote Companion started on http://127.0.0.1:48761${PID:+ (pid $PID)}"
    exit 0
  fi
  sleep 0.2
done

echo "Codex MarginNote Companion failed to become ready; see $LOG" >&2
exit 1
