# LifeLine AI

LifeLine AI is a patient-friendly health decision-support app built with Streamlit. It helps users check symptoms, learn about health and medicine topics, create a health report PDF, review saved cases, and check basic medication safety concerns.

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
- Scenario Challenge for practice
- Sam assistant bubble for navigation help
- Multi-language dropdown support
- Offline mode for local rules, local SQLite storage, and no cloud calls

## Safety

LifeLine AI is general health education and decision support. It does not diagnose, prescribe medicine, calculate personal dosage, or replace doctors, pharmacists, or emergency services.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open:

```text
http://127.0.0.1:8501
```

## Tech Stack

- Python
- Streamlit
- scikit-learn
- ReportLab
- SQLite
- deep-translator

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

If Supabase secrets are missing, the app uses a local SQLite fallback for testing.

## Offline Mode

Turn on **Offline mode** in the sidebar, or set:

```toml
LIFELINE_OFFLINE_MODE = "true"
```

Offline mode disables OpenAI, Supabase, Google Translate, and YouTube embeds. The app still runs with local triage rules, local Q&A fallbacks, PDF generation, and SQLite storage.
