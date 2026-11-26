#!/usr/bin/env bash
# Create .venv using the Python version pinned in .python-version, then install deps.
# Assumes uv is installed. Usage: ./setup.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || dirname "$0")"

uv python install          # installs the version from .python-version if missing
uv venv --clear .venv      # uv picks up .python-version automatically

if [[ -f pyproject.toml ]]; then
  uv sync
elif [[ -f requirements.txt ]]; then
  uv pip install -r requirements.txt
fi

echo "Done: $(.venv/bin/python --version)"
echo "Activate with: source .venv/bin/activate"