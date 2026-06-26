# LifeLine AI Local Install

This repository can be downloaded from GitHub and run locally on Windows, macOS, and Linux.

## Download from GitHub

Use the direct ZIP link:

```text
https://github.com/Akshaan2012/lifeline-ai/archive/refs/heads/main.zip
```

Or download manually:

1. Open the LifeLine AI GitHub repository: `https://github.com/Akshaan2012/lifeline-ai`
2. Click the green **Code** button.
3. Click **Download ZIP**.
4. Unzip the downloaded folder.

## Windows

1. Install Python 3.10 or newer from https://www.python.org/downloads/.
2. Download the repo ZIP from GitHub and unzip it.
3. Double-click `run_lifeline_ai_windows.bat`.
4. Wait for dependencies to install. The app opens at `http://localhost:8501`.

## macOS / Linux

1. Install Python 3.10 or newer.
2. Download the repo ZIP from GitHub and unzip it.
3. Open Terminal in the repository folder.
4. Run:

```bash
chmod +x run_lifeline_ai_mac_linux.sh
./run_lifeline_ai_mac_linux.sh
```

5. Wait for dependencies to install. The app opens at `http://localhost:8501`.

## Git Clone Option

Users who prefer Git can run:

```bash
git clone https://github.com/Akshaan2012/lifeline-ai.git
cd lifeline-ai
```

Then run the launcher for their operating system.

## Notes

- The app opens in your browser at `http://localhost:8501`.
- If Supabase settings are missing, the app uses local SQLite fallback.
- LifeLine AI is general health education and decision support. It does not diagnose, prescribe, or replace medical care.
