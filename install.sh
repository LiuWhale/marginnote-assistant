#!/bin/zsh
set -euo pipefail

PACKAGE_ROOT="$(cd "$(dirname "$0")" && pwd)"
COMPANION_SOURCE="$PACKAGE_ROOT/companion"
DRY_RUN="${CODEX_MN_DRY_RUN:-0}"

if [[ ! -d "$COMPANION_SOURCE" ]]; then
  echo "Cannot find packaged companion directory: $COMPANION_SOURCE" >&2
  echo "Run this script from the unzipped CodexCompanion package root." >&2
  exit 1
fi

if [[ ! -f "$COMPANION_SOURCE/install_extension.sh" ]]; then
  echo "Missing installer: $COMPANION_SOURCE/install_extension.sh" >&2
  exit 1
fi

if [[ ! -f "$COMPANION_SOURCE/install_companion.sh" ]]; then
  echo "Missing installer: $COMPANION_SOURCE/install_companion.sh" >&2
  exit 1
fi

echo "Installing Codex Companion for MarginNote 4..."
/bin/zsh "$COMPANION_SOURCE/install_extension.sh"
/bin/zsh "$COMPANION_SOURCE/install_companion.sh"

INSTALLED_HOME="${CODEX_MN_COMPANION_HOME:-$HOME/.codex/marginnote-assistant}"
echo
if [[ "$DRY_RUN" == "1" ]]; then
  echo "Skipping doctor in dry-run mode."
else
  echo "Running doctor..."
  /usr/bin/python3 "$INSTALLED_HOME/doctor.py" || true
fi

echo
echo "Install finished. Restart MarginNote 4, open a notebook, then click the Codex Companion toolbar icon."
