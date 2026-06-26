#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "Starting LifeLine AI for macOS/Linux..."

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3.10 or newer is required."
  echo "Install Python from https://www.python.org/downloads/ or your system package manager."
  exit 1
fi

"$PYTHON_BIN" -m venv .venv
. ".venv/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
