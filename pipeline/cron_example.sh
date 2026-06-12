#!/usr/bin/env bash
set -euo pipefail
# Example: run daily at 3:15am via crontab: 15 3 * * * /path/to/cron_example.sh >> /path/to/harvest.log 2>&1
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."
export PYTHONPATH="$PWD"

PY_BIN="${PY_BIN:-python3}"
if command -v python3.11 >/dev/null 2>&1; then
  PY_BIN=python3.11
fi

"$PY_BIN" -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt requests pyyaml
export UNPAYWALL_EMAIL="you@example.com"
pip install requests pyyaml pypdf
python -m pipeline.run_all || python pipeline/run_all.py
