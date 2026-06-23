#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "Uninstalling Codex Companion..."
echo
"$ROOT/uninstall.sh"
echo
echo "Uninstall command finished. You can close this window after reviewing the output."
read -r "?Press Return to close..."
