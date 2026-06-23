#!/bin/zsh
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${CODEX_MN_COMPANION_HOME:-$HOME/.codex/marginnote-assistant}"
DEFAULT_LABEL="com.codex.paper-companion"
LEGACY_LABEL="com.liuwhale.codex-marginnote-assistant"
LABEL="${CODEX_MN_LAUNCH_LABEL:-$DEFAULT_LABEL}"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LEGACY_PLIST="$HOME/Library/LaunchAgents/$LEGACY_LABEL.plist"
DRY_RUN="${CODEX_MN_DRY_RUN:-0}"

mkdir -p "$TARGET" "$TARGET/logs" "$TARGET/backups" "$HOME/Library/LaunchAgents"

if [[ "$SOURCE_DIR" != "$TARGET" ]]; then
  /usr/bin/rsync -a \
    --exclude '__pycache__' \
    --exclude 'logs' \
    --exclude 'sessions' \
    --exclude 'queue' \
    --exclude 'backups' \
    --exclude 'events.jsonl' \
    --exclude 'companion.pid' \
    "$SOURCE_DIR/" "$TARGET/"
fi

cat >"$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$TARGET/companion.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$TARGET</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>CODEX_MN_COMPANION_HOME</key>
    <string>$TARGET</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$TARGET/logs/companion.launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>$TARGET/logs/companion.launchd.err.log</string>
</dict>
</plist>
PLIST

DOMAIN="gui/$(id -u)"
if [[ "$DRY_RUN" == "1" ]]; then
  echo "Dry-run: would bootstrap LaunchAgent $PLIST"
  echo "Installed Codex Companion files at $TARGET"
  exit 0
fi
if [[ "$LABEL" != "$LEGACY_LABEL" ]]; then
  launchctl bootout "$DOMAIN" "$LEGACY_PLIST" >/dev/null 2>&1 || true
  launchctl bootout "$DOMAIN/$LEGACY_LABEL" >/dev/null 2>&1 || true
  rm -f "$LEGACY_PLIST"
fi
launchctl bootout "$DOMAIN" "$PLIST" >/dev/null 2>&1 || true
launchctl bootstrap "$DOMAIN" "$PLIST"
launchctl enable "$DOMAIN/$LABEL" >/dev/null 2>&1 || true

for _ in {1..40}; do
  if /usr/bin/curl -fsS http://127.0.0.1:48761/health >/dev/null 2>&1; then
    echo "Installed Codex Companion at $TARGET"
    echo "LaunchAgent: $PLIST"
    exit 0
  fi
  sleep 0.25
done

echo "Installed files, but Companion did not become ready. Check $TARGET/logs/companion.launchd.err.log" >&2
exit 1
