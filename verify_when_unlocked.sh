#!/bin/zsh
set -euo pipefail

CHECK_INTERVAL_SECONDS="${CHECK_INTERVAL_SECONDS:-5}"
ROOT="${CODEX_MN_COMPANION_HOME:-$HOME/.codex/marginnote-assistant}"
VERIFY_SCRIPT="$ROOT/verify_after_unlock.py"

is_locked() {
  /usr/sbin/ioreg -n Root -d1 | /usr/bin/grep -Eq 'CGSSessionScreenIsLocked"=Yes|CGSSessionScreenIsLocked" = Yes'
}

echo "Waiting for macOS screen unlock, then running MarginNote/Codex Assistant verification..."
while is_locked; do
  sleep "$CHECK_INTERVAL_SECONDS"
done

echo "Screen appears unlocked. Opening MarginNote 4 and running verification..."
/usr/bin/open -a "MarginNote 4"
sleep 8
exec "$VERIFY_SCRIPT"
