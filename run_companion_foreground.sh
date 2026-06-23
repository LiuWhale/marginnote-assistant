#!/bin/zsh
set -euo pipefail

ROOT="/Users/liuwhale/.codex/marginnote-assistant"
mkdir -p "$ROOT/logs" "$ROOT/backups"
exec /usr/bin/python3 "$ROOT/companion.py"
