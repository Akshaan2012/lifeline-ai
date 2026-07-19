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
2. Download the repo ZIP from GitHub.
3. Right-click the ZIP and choose **Extract All...**.
4. Open the extracted `lifeline-ai-main` folder.
5. Double-click `run_lifeline_ai_windows.bat`.
6. Do not run the `.bat` file directly from inside the ZIP window. Windows will extract only that one file and the app will not find `requirements.txt`.
7. Wait for dependencies to install. The app opens at `http://localhost:8501`.

## Optional Gemini Features

Sam, Patient Health Checker, Health & Medicine Q&A, Medication Safety, and Scenario Challenge can use Gemini. Use a backend/server-side Gemini API key. Do not put the key in frontend JavaScript, mobile app code, public GitHub repositories, or public environment files.

To enable Gemini locally:

1. Copy `.env.example` to a new file named `.env`.
2. Set `LIFELINE_ENV=development`.
3. Replace `GEMINI_API_KEY` with a valid Gemini API key.
4. Restart the launcher.

```text
AI_PROVIDER=gemini
GEMINI_API_KEY=your-private-gemini-key
GEMINI_MODEL=gemini-3.5-flash
```

Do not add real keys to GitHub. For the hosted Streamlit app, put `AI_PROVIDER`, `GEMINI_API_KEY`, and `GEMINI_MODEL` in the app's **Settings > Secrets** instead. Immediately revoke and replace any key that has ever been committed or shared publicly.

LifeLine AI uses Gemini only as an optional assistant for language, summarisation, and education. Emergency red flags stay in local rules, and clinical records still require clinician review.

## macOS / Linux

1. Install Python 3.10 or newer.
2. Download the repo ZIP from GitHub.
3. Unzip the downloaded folder.
4. Open Terminal in the extracted `lifeline-ai-main` folder.
5. On Ubuntu/Debian Linux, install venv support if needed:

```bash
sudo apt install python3-venv
```

6. Run:

```bash
chmod +x run_lifeline_ai_mac_linux.sh
./run_lifeline_ai_mac_linux.sh
```

7. Wait for dependencies to install. The app opens at `http://localhost:8501`.

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
- If Gemini is missing or unavailable, AI-enhanced pages use their built-in local fallback.
- LifeLine AI is general health education and decision support. It does not diagnose, prescribe, or replace medical care.
