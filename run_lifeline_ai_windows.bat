@echo off
setlocal
cd /d "%~dp0"
echo Starting LifeLine AI for Windows...

py -3 -m venv .venv 2>NUL
if errorlevel 1 python -m venv .venv

if not exist ".venv\Scripts\python.exe" (
  echo Python 3.10 or newer is required. Install it from https://www.python.org/downloads/
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
echo Opening LifeLine AI at http://localhost:8501
".venv\Scripts\python.exe" -m streamlit run app.py
pause
