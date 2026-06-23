#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "Installing Codex Companion..."
echo
"$ROOT/install.sh"
echo
echo "Install command finished. You can close this window after reviewing the output."
read -r "?Press Return to close..."
