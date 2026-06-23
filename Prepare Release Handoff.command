#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"

cd "$SCRIPT_DIR"
"$PYTHON_BIN" prepare_release_handoff.py

echo
echo "Release handoff bundle prepared. Press any key to close."
read -k 1 -s || true
