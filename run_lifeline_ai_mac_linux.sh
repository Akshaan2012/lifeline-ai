#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "Starting LifeLine AI for macOS/Linux..."

PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -m venv .venv
. ".venv/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
