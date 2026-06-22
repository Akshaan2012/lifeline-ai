# LifeLine AI

LifeLine AI is a patient-friendly health decision-support app built with Streamlit. It helps users check symptoms, learn about health and medicine topics, create a health report PDF, review saved cases, and check basic medication safety concerns.

## Features

- Patient Health Checker with risk levels and red flags
- Downloadable Health Report PDF
- Health & Medicine Q&A in simple language
- Medication Safety Checker for common cautions and pharmacist questions
- Doctor Dashboard for saved cases
- Scenario Challenge for practice
- Sam assistant bubble for navigation help
- Multi-language dropdown support

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
