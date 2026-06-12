#!/usr/bin/env bash
set -euo pipefail
# Removes macOS Gatekeeper quarantine attributes from Next.js SWC binaries
# Use if you see: "Failed to load SWC binary for darwin/arm64" or "code signature invalid (errno=85)"
cd "$( dirname "${BASH_SOURCE[0]}" )"
if [[ "$OSTYPE" != "darwin"* ]]; then
  echo "This fix is only for macOS."
  exit 0
fi
if ! command -v xattr >/dev/null 2>&1; then
  echo "xattr not found."
  exit 1
fi
if [ -d "frontend/node_modules/@next" ]; then
  echo "• Clearing quarantine flags on frontend/node_modules/@next …"
  xattr -dr com.apple.quarantine "frontend/node_modules/@next" || true
  echo "✔ Done. Re-run: bash run_dev.sh"
else
  echo "No @next directory found yet. Run: (cd frontend && npm install) first."
fi
