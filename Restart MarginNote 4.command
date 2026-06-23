#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -f "$SCRIPT_DIR/send_action.py" ]]; then
  SCRIPT="$SCRIPT_DIR/send_action.py"
elif [[ -f "$SCRIPT_DIR/companion/send_action.py" ]]; then
  SCRIPT="$SCRIPT_DIR/companion/send_action.py"
elif [[ -f "$HOME/.codex/marginnote-assistant/send_action.py" ]]; then
  SCRIPT="$HOME/.codex/marginnote-assistant/send_action.py"
else
  echo "send_action.py not found." >&2
  exit 1
fi

echo "This will quit and reopen MarginNote 4 to load the latest Codex Companion native handler."
echo "Use this when Refresh MN Runtime still reports stale native handler features."
echo
printf "Continue? [y/N] "
read -r REPLY
case "$REPLY" in
  y|Y|yes|YES)
    ;;
  *)
    echo "Cancelled."
    exit 0
    ;;
esac

/usr/bin/python3 "$SCRIPT" restart_marginnote4 --direct --record "$@"

echo
echo "After MarginNote 4 reopens, open the Codex Companion panel and run Refresh MN Runtime."

if [[ -t 0 ]]; then
  echo
  echo "Press Return to close."
  read -r _
fi
