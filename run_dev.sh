#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$ROOT_DIR"

echo "▶ Magus Search — one-command dev server"
echo "   - Backend: http://localhost:8000"
echo "   - Frontend: http://localhost:3000"

PY_BIN="${PY_BIN:-python3}"
if command -v python3.11 >/dev/null 2>&1; then
  PY_BIN=python3.11
fi

# --- Python venv & deps (backend + pipeline) ---
if [ ! -d ".venv" ]; then
  echo "• Creating Python venv (.venv)"
  "$PY_BIN" -m venv .venv
fi
source .venv/bin/activate

# Backend deps
pip install -q -r backend/requirements.txt requests pyyaml pypdf || true

# System dep checks (best-effort)
if ! command -v tesseract >/dev/null 2>&1; then
  echo "⚠ tesseract not found (OCR). Install with 'brew install tesseract' or 'apt-get install tesseract-ocr' if you plan to OCR."
fi
if ! command -v pdftoppm >/dev/null 2>&1; then
  echo "⚠ pdftoppm not found (PDF→images for OCR). Install with 'brew install poppler' or 'apt-get install poppler-utils'."
fi

export PYTHONPATH="$PWD"

# macOS SWC quarantine auto-fix (Gatekeeper can flag Next SWC binaries from zips)
if [[ "$OSTYPE" == "darwin"* ]] && command -v xattr >/dev/null 2>&1; then
  if [ -d "frontend/node_modules/@next" ]; then
    echo "• Checking for macOS quarantine flags on Next SWC binaries (may show warnings if already clean)…"
    xattr -dr com.apple.quarantine "frontend/node_modules/@next" || true
  fi
fi


# --- Launch backend ---
echo "• Starting backend (uvicorn)..."
uvicorn backend.app:app --reload --port 8000 &
BACK_PID=$!

# Ensure backend is stopped on exit
cleanup() {
  echo ""
  echo "• Shutting down backend (pid $BACK_PID)…"
  kill $BACK_PID >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

# --- Frontend deps & dev server ---
# --- Node / npm check ---
if ! command -v npm >/dev/null 2>&1; then
  echo "✖ Node.js (npm) is required for the frontend."
  echo "  Install with Homebrew:  brew install node"
  echo "  or set up nvm:          brew install nvm && nvm install --lts"
  echo "Then re-run: bash run_dev.sh"
  exit 1
fi
echo "• Installing frontend deps (if needed) & starting Next.js..."

cd frontend
npm i --silent || true
npm run dev
