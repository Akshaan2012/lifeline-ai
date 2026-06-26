@echo off
setlocal
cd /d "%~dp0"
echo Starting LifeLine AI for Windows...

if not exist "requirements.txt" (
  echo.
  echo ERROR: requirements.txt was not found.
  echo.
  echo This usually means the launcher was opened from inside the ZIP file.
  echo Please right-click the downloaded ZIP, choose "Extract All...", open the extracted folder,
  echo then double-click run_lifeline_ai_windows.bat again.
  echo.
  pause
  exit /b 1
)

if not exist "app.py" (
  echo.
  echo ERROR: app.py was not found.
  echo Please run this launcher from the extracted LifeLine AI folder.
  echo.
  pause
  exit /b 1
)

py -3 -m venv .venv 2>NUL
if errorlevel 1 python -m venv .venv

if not exist ".venv\Scripts\python.exe" (
  echo Python 3.10 or newer is required. Install it from https://www.python.org/downloads/
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Dependency installation failed. Check your internet connection, then run this file again.
  echo.
  pause
  exit /b 1
)

echo Opening LifeLine AI at http://localhost:8501
".venv\Scripts\python.exe" -m streamlit run app.py
pause
