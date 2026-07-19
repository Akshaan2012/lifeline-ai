# LifeLine AI

LifeLine AI is a patient-friendly doctor-visit preparation and clinic-intake app built with Streamlit. It helps users record symptoms, create a doctor-ready summary, learn about health and medicine topics, review saved cases, and check basic medication safety concerns. It is not an autonomous diagnosis product.

## Features

- Patient Health Checker with risk levels and red flags
- Smart follow-up questions based on selected symptoms
- Risk-based care action plans for emergency, urgent, doctor-visit, and home-care cases
- Downloadable Health Report PDF
- Health Timeline with trend charts for risk score, pain, and optional measurements
- Health & Medicine Q&A in simple language
- Medication Safety Checker for common cautions and pharmacist questions
- Home command center with saved-case and priority-case status
- Doctor Dashboard for saved cases, queue insights, review status, and doctor notes
- Clinic Pilot Plan with pricing, clinic workflow, pilot checklist, and time-saved / recurring-revenue calculator
- Consent-based clinic handoff with a private case code and patient-visible responses
- Scenario Challenge for practice
- Sam assistant bubble for navigation help
- GitHub repo launch scripts for Windows, macOS, and Linux
- Multi-language dropdown support
- Offline mode for local rules, local SQLite storage, and no cloud calls
- Plain-language red-flag interviews with fail-safe handling for unanswered or uncertain responses
- Emergency action screen with one-tap 112 calling and user-initiated nearby-hospital search
- Medication reconciliation for duplicate ingredients, selected interactions, and allergy matches
- Patient-controlled health passports and separate caregiver profiles
- Care reminders for follow-ups, vaccinations, and medicine-list reviews
- Read-aloud result summaries, larger text, high contrast, and simpler-language preferences
- Clinician evidence traces showing the inputs and rules behind recommendations
- Safety and quality dashboard with anonymous session feedback
- FHIR-style structured JSON exports for clinician and interoperability preparation

## Safety

LifeLine AI is general health education, doctor-visit preparation, and decision support. It does not diagnose, prescribe medicine, calculate personal dosage, or replace doctors, pharmacists, clinics, hospitals, or emergency services.

## Product Direction

The safest first business version is a doctor-visit preparation and digital clinic-intake workflow:

1. Patient records symptoms, timing, medicines, allergies, conditions, and optional measurements.
2. LifeLine AI creates an organized timeline, warning signs, questions for the doctor, and a downloadable report.
3. Patient chooses whether to share the case with a clinic.
4. Clinic staff review a structured queue and measure whether intake time improves.

Do not market the app as “AI diagnosis.” Before real clinic use, get adult supervision, licensed clinical review, privacy review, and local regulatory advice.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open:

```text
http://127.0.0.1:8501
```

## Download From GitHub

Anyone can download the app from your GitHub repository:

[Download LifeLine AI ZIP](https://github.com/Akshaan2012/lifeline-ai/archive/refs/heads/main.zip)

1. Open the LifeLine AI GitHub repo: `https://github.com/Akshaan2012/lifeline-ai`
2. Click the green **Code** button.
3. Click **Download ZIP**.
4. Unzip the folder on your computer.
5. Run the launcher for your system:

- `run_lifeline_ai_windows.bat` for Windows
- `run_lifeline_ai_mac_linux.sh` for macOS and Linux

Python 3.10 or newer is required. See `INSTALL.md` for step-by-step setup notes.

## One-Click Local Launchers

After downloading and unzipping the repo:

### Windows

Right-click the downloaded ZIP, choose **Extract All...**, open the extracted `lifeline-ai-main` folder, then double-click:

```text
run_lifeline_ai_windows.bat
```

Do not run the `.bat` file directly from inside the ZIP preview window. Windows will extract only the launcher, so the app will not find `requirements.txt`.

### macOS

Unzip the download first, open Terminal in the extracted `lifeline-ai-main` folder, then run:

```bash
chmod +x run_lifeline_ai_mac_linux.sh
./run_lifeline_ai_mac_linux.sh
```

### Linux

Unzip the download first, open Terminal in the extracted `lifeline-ai-main` folder, then run:

```bash
chmod +x run_lifeline_ai_mac_linux.sh
./run_lifeline_ai_mac_linux.sh
```

On Ubuntu/Debian, install venv support first if the launcher says it cannot create a virtual environment:

```bash
sudo apt install python3-venv
```

## Tech Stack

- Python
- Streamlit
- scikit-learn
- ReportLab
- SQLite
- deep-translator
- Gemini API (optional AI enhancements)

## Gemini Setup

Gemini enhances Sam, Patient Health Checker wording, Health & Medicine Q&A, Medication Safety, and Scenario Challenge coaching. The app continues with local safety rules when Gemini is unavailable. Do not use the AI provider as the sole emergency detector: LifeLine AI keeps urgent red flags in fixed clinician-reviewed rules and uses Gemini only for language help, follow-up wording, summarisation, and education.

Use a project-scoped Gemini API key on the backend/server side only. Do not place provider keys in frontend JavaScript, React/mobile code, public GitHub repositories, or public `.env` files.

For a local install, copy `.env.example` to `.env`, replace only the environment key you are using, and keep `.env` private:

```text
LIFELINE_ENV=development
AI_PROVIDER=gemini
GEMINI_API_KEY=your-private-gemini-key
GEMINI_MODEL=gemini-3.5-flash
AI_TIMEOUT_SECONDS=10
AI_MAX_OUTPUT_TOKENS=620
AI_RATE_LIMIT_PER_MINUTE=30
```

For Streamlit Community Cloud:

1. Open the deployed app settings.
2. Go to **Secrets**.
3. Add the following TOML values.
4. Save and reboot the app.

```toml
LIFELINE_ENV = "production"
AI_PROVIDER = "gemini"
GEMINI_API_KEY = "your-private-gemini-key"
GEMINI_MODEL = "gemini-3.5-flash"
AI_TIMEOUT_SECONDS = "10"
AI_MAX_OUTPUT_TOKENS = "620"
AI_RATE_LIMIT_PER_MINUTE = "30"
```

Never commit `.env` or `.streamlit/secrets.toml`. Both are excluded by `.gitignore`.

The safe production flow should be:

```text
Patient/doctor app
  -> secure backend
  -> AI provider API
  -> backend checks and formats the result
  -> app receives the safe response
```

The backend should authenticate clinics and users, remove unnecessary direct identifiers before provider calls, rate-limit usage, record audit events without storing sensitive prompt text, verify AI responses before showing clinical alerts, and require doctor approval before content becomes the final clinical record. Immediately revoke and replace any key that has ever been committed to GitHub.

For real patient data, confirm the provider's privacy terms, data-retention controls, regional processing options, and healthcare agreements before enabling cloud AI.

## Supabase Setup

LifeLine AI uses Supabase PostgreSQL in production when these secrets are present:

```toml
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_ANON_KEY = "your-public-anon-key"
```

In Streamlit Community Cloud:

1. Open the deployed app settings.
2. Go to **Secrets**.
3. Add `SUPABASE_URL` and `SUPABASE_ANON_KEY`.
4. Reboot the app.

In Supabase:

1. Create a new project.
2. Open **SQL Editor**.
3. Paste and run the SQL from `supabase_schema.sql`.

Run the schema again after updating the app; it safely adds the clinic handoff columns when they are missing.

The updated schema keeps anonymous patient submissions and private-code response lookup working, but blocks anonymous table-wide reads, edits, and deletes. Doctor-dashboard access requires an authenticated Supabase user whose `app_metadata.role` is `staff`. Set that role only from a trusted server or the Supabase administration tools; users must never be allowed to assign it to themselves.

The interface enforces this role too: professional navigation and patient cases stay locked until staff sign-in succeeds. Never place a Supabase service-role key in this app or its Streamlit secrets.

If Supabase secrets are missing, the app uses a local SQLite fallback for testing.

## Offline Mode

Turn on **Offline mode** in the sidebar, or set:

```toml
LIFELINE_OFFLINE_MODE = "true"
```

Offline mode disables Gemini, Supabase, Google Translate, and YouTube embeds. The app still runs with local triage rules, local Q&A fallbacks, PDF generation, and SQLite storage.
