#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -f "$SCRIPT_DIR/refresh_mn_runtime.py" ]]; then
  SCRIPT="$SCRIPT_DIR/refresh_mn_runtime.py"
elif [[ -f "$SCRIPT_DIR/companion/refresh_mn_runtime.py" ]]; then
  SCRIPT="$SCRIPT_DIR/companion/refresh_mn_runtime.py"
elif [[ -f "$HOME/.codex/marginnote-assistant/refresh_mn_runtime.py" ]]; then
  SCRIPT="$HOME/.codex/marginnote-assistant/refresh_mn_runtime.py"
else
  echo "refresh_mn_runtime.py not found." >&2
  exit 1
fi

/usr/bin/python3 "$SCRIPT" --try-addon-url-reload "$@"

if [[ -t 0 ]]; then
  echo
  echo "Press Return to close."
  read -r _
fi
