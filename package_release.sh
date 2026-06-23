#!/bin/bash
set -euo pipefail

ROOT="${CODEX_MN_COMPANION_HOME:-$HOME/.codex/marginnote-assistant}"
exec /usr/bin/python3 "$ROOT/package_release.py" "$@"
