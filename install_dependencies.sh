#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$ROOT_DIR"

echo "▶ Installing Magus Search dependencies"

# --- Python ---
if [ ! -d ".venv" ]; then
  echo "• Creating Python venv (.venv)"
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip || true

echo "• Installing Python packages"
pip install -r backend/requirements.txt requests pyyaml pypdf

# --- Node / Frontend ---
if command -v npm >/dev/null 2>&1; then
  echo "• Installing frontend packages (npm)"
  cd frontend
  npm install
  cd ..
else
  echo "⚠ npm not found — skipping frontend install."
  echo "  Install Node.js first (e.g., 'brew install node' or use nvm), then run:"
  echo "    cd frontend && npm install"
fi

echo "✔ Dependencies installed."
