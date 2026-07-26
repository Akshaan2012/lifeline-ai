#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "Starting LifeLine AI for macOS/Linux..."

if [ ! -f "requirements.txt" ]; then
  echo
  echo "ERROR: requirements.txt was not found."
  echo
  echo "Please run this script from the extracted LifeLine AI folder."
  echo "If you downloaded the ZIP, unzip it first, then open Terminal in the extracted lifeline-ai-main folder."
  echo
  exit 1
fi

if [ ! -f "app.py" ]; then
  echo
  echo "ERROR: app.py was not found."
  echo "Please run this script from the extracted LifeLine AI folder."
  echo
  exit 1
fi

FREE_KB="$(df -Pk . | awk 'NR==2 {print $4}')"
if [ -n "$FREE_KB" ] && [ "$FREE_KB" -lt 1048576 ]; then
  echo
  echo "WARNING: Less than 1 GB of disk space is free."
  echo "Dependency installation may fail. Free some disk space, then run this script again."
  echo
  read -r -p "Press Enter to continue anyway, or press Ctrl+C to stop. "
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3.10 or newer is required."
  echo "Install Python from https://www.python.org/downloads/ or your system package manager."
  exit 1
fi

if ! "$PYTHON_BIN" -m venv .venv; then
  echo
  echo "Could not create the Python virtual environment."
  echo "On Ubuntu/Debian, install venv support with: sudo apt install python3-venv"
  echo "On macOS, install Python from https://www.python.org/downloads/ if needed."
  echo
  exit 1
fi

. ".venv/bin/activate"

python -m pip install --upgrade pip
if ! python -m pip install -r requirements.txt; then
  echo
  echo "Dependency installation failed. Check your internet connection, then run this script again."
  echo
  exit 1
fi

echo "Opening LifeLine AI at http://localhost:8501"
python -m streamlit run app.py
