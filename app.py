from __future__ import annotations

import random
import json
from html import escape
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from backend.database import clear_cases, database_backend, database_error_message, delete_patient_cases, list_cases, save_case, update_case_review
from backend.disease_qa import answer_question
from backend.doctor_summary import build_doctor_summary
from backend.followup import evaluate_follow_up
from backend.medication_safety import analyze_medication_safety
from backend.recommender import build_recommendations
from backend.report import generate_health_report_pdf
from backend.sam import answer_message
from backend.translator import (
    preload_translations_async,
    translate_answer,
    translate_items,
    translate_text,
    translate_text_cached,
)
from backend.triage_engine import RISK_ORDER, analyze_patient


st.set_page_config(
    page_title="LifeLine AI",
    page_icon="L",
    layout="wide",
    initial_sidebar_state="expanded",
)


SYMPTOM_OPTIONS = [
    "Fever",
    "High fever",
    "Cough",
    "Sore throat",
    "Shortness of breath",
    "Severe breathing difficulty",
    "Chest pain",
    "Sweating",
    "Headache",
    "Severe headache",
    "Dizziness",
    "Confusion",
    "Stroke signs",
    "Stomach pain",
    "Severe stomach pain",
    "Nausea",
    "Diarrhea",
    "Persistent vomiting",
    "Fatigue",
    "Body pain",
    "Dehydration",
    "Frequent urination",
    "Excessive thirst",
    "Blurred vision",
    "Rash",
    "Itching",
    "Swelling",
    "Severe allergic reaction",
]

CONDITION_OPTIONS = [
    "Diabetes",
    "Heart disease",
    "Asthma",
    "COPD",
    "Kidney disease",
    "High blood pressure",
    "Pregnancy",
    "Weak immune system",
]

REVIEW_STATUSES = ["New", "Reviewed", "Referred", "Resolved"]

FOLLOW_UP_RULES = [
    {
        "triggers": {"chest pain", "palpitations", "sweating"},
        "question": "Is the pain spreading to the arm, jaw, back, or happening with heavy sweating?",
        "signal": "sweating",
        "reason": "Chest pain with spreading pain or sweating can be a serious heart warning.",
    },
    {
        "triggers": {"chest pain", "dizziness", "shortness of breath"},
        "question": "Has the patient fainted, nearly fainted, or become unusually weak?",
        "signal": "fainting",
        "reason": "Fainting with these symptoms needs faster medical attention.",
    },
    {
        "triggers": {"shortness of breath", "severe breathing difficulty", "wheezing"},
        "question": "Are the lips or face turning blue, or is speaking full sentences difficult?",
        "signal": "blue lips",
        "reason": "Blue lips or trouble speaking can mean low oxygen.",
    },
    {
        "triggers": {"headache", "severe headache", "dizziness", "confusion"},
        "question": "Is there face drooping, arm weakness, speech trouble, seizure, or sudden confusion?",
        "signal": "stroke signs",
        "reason": "Sudden nerve or speech changes can be emergency warning signs.",
    },
    {
        "triggers": {"rash", "itching", "swelling"},
        "question": "Did swelling of the lips/face or breathing trouble start after food, medicine, or a bite?",
        "signal": "severe allergic reaction",
        "reason": "Swelling with breathing trouble can be a severe allergic reaction.",
    },
    {
        "triggers": {"diarrhea", "persistent vomiting", "nausea", "high fever"},
        "question": "Is the patient unable to keep fluids down, very thirsty, or passing very little urine?",
        "signal": "dehydration",
        "reason": "Dehydration can become serious, especially with vomiting, diarrhea, or fever.",
    },
    {
        "triggers": {"frequent urination", "excessive thirst", "blurred vision", "fatigue"},
        "question": "Is there extreme thirst, frequent urination, vomiting, or unusual sleepiness together?",
        "signal": "very high sugar symptoms",
        "reason": "These symptoms together can suggest a high blood sugar warning pattern.",
    },
]

PAGES = [
    "Home",
    "Patient Health Checker",
    "Health Timeline",
    "Disease Q&A Assistant",
    "Medication Safety Checker",
    "Doctor Dashboard",
    "Scenario Challenge",
    "Safety Videos",
]

LANGUAGE_OPTIONS = [
    "\U0001f1fa\U0001f1f8 English", "\U0001f1ee\U0001f1f3 Hindi", "\U0001f1f7\U0001f1fa Russian", "\U0001f1e9\U0001f1ea German", "\U0001f1eb\U0001f1f7 French",
    "\U0001f1ea\U0001f1f8 Spanish", "\U0001f1ee\U0001f1ea Gaelic", "\U0001f1ee\U0001f1f3 Sanskrit", "\U0001f1ee\U0001f1f3 Marathi", "\U0001f1ee\U0001f1f3 Kannada",
    "\U0001f1ee\U0001f1f3 Tamil", "\U0001f1ee\U0001f1f3 Malayalam", "\U0001f1ee\U0001f1f3 Telugu", "\U0001f1ee\U0001f1f3 Gujarati", "\U0001f1ee\U0001f1f3 Bhojpuri",
    "\U0001f1e8\U0001f1f3 Mandarin", "\U0001f1f9\U0001f1ed Thai", "\U0001f1ef\U0001f1f5 Japanese", "\U0001f1f3\U0001f1f4 Norwegian", "\U0001f1f8\U0001f1ea Swedish",
    "\U0001f1eb\U0001f1ee Finnish", "\U0001f1f5\U0001f1f9 Portuguese", "\U0001f1f7\U0001f1f4 Romanian", "\U0001f1ee\U0001f1f9 Italian", "\U0001f1ee\U0001f1f8 Icelandic",
    "\U0001f1f3\U0001f1f1 Dutch", "\U0001f1f2\U0001f1fe Malay", "\U0001f1f0\U0001f1ea Swahili", "\U0001f1ff\U0001f1e6 Afrikaans", "\U0001f1ee\U0001f1f1 Hebrew", "\U0001f1f8\U0001f1e6 Arabic",
]

COMMON_TRANSLATION_TEXTS = [
    *PAGES,
    *SYMPTOM_OPTIONS,
    *CONDITION_OPTIONS,
    "LifeLine AI workspace is ready",
    "Use Sam or the sidebar to move between tools",
    "Smart inside. Simple outside.",
    "Navigation",
    "Decision support. Not a replacement for doctors.",
    "AI health guidance",
    "A simple health risk and doctor-visit advisor. It helps users check symptoms, learn about diseases, get precautions, and understand when medical help is needed.",
    "Prediction",
    "Recommendations",
    "Simple language",
    "Sam bubble assistant",
    "Risk Prediction",
    "Advanced Advice",
    "Sam Assistant",
    "Click the bottom-right bubble to ask for help.",
    "Basic details",
    "Symptoms",
    "Choose symptoms from list",
    "Write any other symptoms",
    "Existing conditions",
    "Current medicines or allergies",
    "Analyze Health",
    "Clear profile",
    "Save patient profile",
    "Live result",
    "Care Level",
    "Risk Score",
    "Pattern",
    "Timeframe",
    "How this score works",
    "Self-Care",
    "Doctor Visit Recommended",
    "Urgent Care",
    "Emergency",
    "Likely health pattern",
    "Why the app thinks this",
    "What to do now",
    "Home care support",
    "Precautions",
    "What to avoid",
    "Prevention tips",
    "Red Flags",
    "Questions to ask a doctor",
    "Health & Medicine Q&A",
    "Medication Safety Checker",
    "Doctor / Hospital Dashboard",
    "Scenario Challenge",
    "Safety Videos",
    "Language",
    "Offline mode",
    "Check",
    "Track",
    "Share",
    "Symptoms and red flags",
    "Risk and vitals over time",
    "Doctor-ready summaries",
    "Start Health Check",
    "View Timeline",
    "Open Doctor Dashboard",
    "Correct choice",
    "Needs review",
    "Why this care level fits",
    "Your choice",
    "Safest care level",
    "The safest care level is",
    "Key reasons",
    "Recommended next step",
    "How the answer was decided",
    "Selected symptoms",
    "Risk score",
    "Risk score range",
    "Likely pattern",
    "Important measurements",
    "Existing conditions",
    "This score falls in the range for",
    "That is why the safest answer is",
    "No important measurements were provided.",
    "No existing conditions were provided.",
    "Home command center",
    "Saved cases",
    "High-priority cases",
    "New reviews",
    "Resolved",
    "Ready for the next check",
    "Start with a symptom check, review saved cases, or practice care-level decisions.",
    "Care action plan",
    "Immediate safety steps",
    "Emergency action plan",
    "This result includes emergency warning signs. Treat it as time-sensitive.",
    "Call local emergency services or go to emergency care now.",
    "Do not drive yourself if there is chest pain, fainting, severe breathing difficulty, confusion, or stroke signs.",
    "Keep the patient sitting or lying down and monitor breathing.",
    "Have medicines, allergies, symptoms, and recent measurements ready for clinicians.",
    "Same-day care plan",
    "This result needs fast medical review, especially if symptoms continue or worsen.",
    "Arrange clinic or hospital care as soon as possible today.",
    "Recheck breathing, fever, pain, oxygen, pulse, or blood pressure if available.",
    "Avoid heavy activity until a clinician has reviewed the situation.",
    "Use the doctor summary when speaking with the care team.",
    "Doctor visit prep plan",
    "This result is not usually an emergency, but it should be checked by a doctor.",
    "Book a doctor visit and bring the saved health summary.",
    "Track whether symptoms improve, stay the same, or get worse.",
    "Write down current medicines, allergies, and questions before the visit.",
    "Seek faster care if any red flag appears.",
    "Home monitoring plan",
    "This result looks lower risk right now, but symptoms should still be watched.",
    "Rest, drink fluids if appropriate, and follow basic home care steps.",
    "Check symptoms again if the condition changes or lasts longer than expected.",
    "Avoid mixing medicines without asking a doctor or pharmacist.",
    "Move to faster care if red flags appear.",
    "Queue insights",
    "Cases needing attention",
    "Most common pattern",
    "Review priority",
    "No urgent queue pressure right now.",
    "Review emergency and urgent cases first.",
    "Review new cases before resolved cases.",
    "Using local fallback storage. To use Supabase, run supabase_schema.sql in Supabase SQL Editor and reboot.",
]


def tr(text: str) -> str:
    return translate_text_cached(text, st.session_state.language)


def prepare_language(selected_language: str) -> None:
    if selected_language == "🇺🇸 English" or st.session_state.get("offline_mode"):
        return
    prepared_languages = st.session_state.setdefault("prepared_languages", [])
    if selected_language in prepared_languages:
        return
    preload_translations_async(COMMON_TRANSLATION_TEXTS, selected_language)
    prepared_languages.append(selected_language)


def h(text: str) -> str:
    return escape(tr(text))


def split_free_text_items(text: str) -> list[str]:
    if not text.strip():
        return []
    normalized = text.replace("\n", ",").replace(";", ",")
    return [item.strip().title() for item in normalized.split(",") if item.strip()]


def unique_items(items: list[str]) -> list[str]:
    seen: set[str] = set()
    clean_items: list[str] = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            clean_items.append(item.strip())
    return clean_items


def key_fragment(text: str) -> str:
    cleaned = "".join(char if char.isalnum() else "_" for char in text.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def adaptive_followup_rules(symptoms: list[str]) -> list[dict[str, Any]]:
    selected = {symptom.strip().lower() for symptom in symptoms}
    return [
        rule
        for rule in FOLLOW_UP_RULES
        if selected.intersection(rule["triggers"])
        and str(rule["signal"]).lower() not in selected
    ]


def render_adaptive_followups(symptoms: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    answers: list[dict[str, str]] = []
    safety_signals: list[str] = []
    rules = adaptive_followup_rules(symptoms)
    if not rules:
        return answers, safety_signals

    st.markdown(f"**{tr('Smart follow-up questions')}**")
    st.caption(tr("These questions appear based on the symptoms selected above. They help catch red flags earlier."))
    for index, rule in enumerate(rules):
        answer = st.radio(
            tr(rule["question"]),
            ["No", "Yes", "Not sure"],
            horizontal=True,
            key=f"adaptive_followup_{index}_{key_fragment(rule['signal'])}",
            format_func=tr,
        )
        answer_record = {
            "question": str(rule["question"]),
            "answer": str(answer),
            "reason": str(rule["reason"]),
            "signal": str(rule["signal"]),
        }
        answers.append(answer_record)
        if answer == "Yes":
            safety_signals.append(str(rule["signal"]).title())
            st.warning(tr(rule["reason"]))
        elif answer == "Not sure":
            st.info(tr("If you are unsure and symptoms feel serious, choose faster medical care."))

    return answers, safety_signals


def parse_case_raw_data(raw_data: Any) -> dict[str, Any]:
    if isinstance(raw_data, dict):
        return raw_data
    if isinstance(raw_data, str) and raw_data.strip():
        try:
            parsed = json.loads(raw_data)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def safe_number(value: Any) -> float | None:
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return None
    return float(number)


def split_known_conditions(conditions: list[str]) -> tuple[list[str], list[str]]:
    known = [item for item in conditions if item in CONDITION_OPTIONS]
    custom = [item for item in conditions if item not in CONDITION_OPTIONS]
    return known, custom


def load_profile_into_form(profile: dict[str, Any]) -> None:
    known_conditions, custom_conditions = split_known_conditions(list(profile.get("conditions", [])))
    st.session_state.patient_name_input = str(profile.get("patient_name", ""))
    st.session_state.patient_age_input = int(profile.get("age") if profile.get("age") is not None else 25)
    st.session_state.patient_gender_input = str(profile.get("gender") or "Prefer not to say")
    st.session_state.patient_conditions_input = known_conditions
    st.session_state.patient_custom_conditions_input = ", ".join(custom_conditions)
    st.session_state.patient_medications_input = str(profile.get("medications", ""))


def clear_profile_form() -> None:
    for key in [
        "patient_name_input",
        "patient_age_input",
        "patient_gender_input",
        "patient_symptoms_input",
        "patient_custom_symptoms_input",
        "patient_duration_input",
        "patient_pain_input",
        "patient_temperature_input",
        "patient_know_heart_rate_input",
        "patient_heart_rate_input",
        "patient_know_bp_input",
        "patient_systolic_input",
        "patient_diastolic_input",
        "patient_know_oxygen_input",
        "patient_oxygen_input",
        "patient_conditions_input",
        "patient_custom_conditions_input",
        "patient_medications_input",
        "checker_result",
        "checker_patient_data",
        "followup_result",
    ]:
        st.session_state.pop(key, None)
    for key in list(st.session_state.keys()):
        if str(key).startswith("adaptive_followup_"):
            st.session_state.pop(key, None)


SCENARIOS = [
    {
        "case": "A 20-year-old has mild fever, sore throat, and body pain for 1 day. Oxygen is 98%.",
        "data": {"age": 20, "symptoms": ["Fever", "Sore throat", "Body pain"], "duration_days": 1, "pain_level": 3, "temperature": 38.2, "heart_rate": 86, "systolic_bp": 118, "diastolic_bp": 76, "oxygen": 98, "conditions": []},
    },
    {
        "case": "A 67-year-old has chest pain, sweating, and shortness of breath. Oxygen is 93%.",
        "data": {"age": 67, "symptoms": ["Chest pain", "Sweating", "Shortness of breath"], "duration_days": 1, "pain_level": 8, "temperature": 37.0, "heart_rate": 118, "systolic_bp": 150, "diastolic_bp": 95, "oxygen": 93, "conditions": ["Heart disease"]},
    },
    {
        "case": "A 35-year-old has frequent urination, excessive thirst, fatigue, and blurred vision for 10 days.",
        "data": {"age": 35, "symptoms": ["Frequent urination", "Excessive thirst", "Fatigue", "Blurred vision"], "duration_days": 10, "pain_level": 2, "temperature": 36.9, "heart_rate": 82, "systolic_bp": 126, "diastolic_bp": 82, "oxygen": 98, "conditions": []},
    },
    {
        "case": "A 9-year-old has rash, itching, swelling of lips, and breathing trouble after eating unknown food.",
        "data": {"age": 9, "symptoms": ["Rash", "Itching", "Swelling", "Severe allergic reaction", "Severe breathing difficulty"], "duration_days": 1, "pain_level": 6, "temperature": 37.1, "heart_rate": 122, "systolic_bp": 95, "diastolic_bp": 62, "oxygen": 91, "conditions": []},
    },
]


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #eef6f4;
            --surface: #fbfffd;
            --surface-2: #e7f0ee;
            --panel: #ffffff;
            --line: #c2d8d3;
            --line-strong: #8fb4ae;
            --line-soft: rgba(14, 43, 48, .12);
            --text: #102528;
            --muted: #627777;
            --mint: #10b8a6;
            --mint-dim: rgba(16, 184, 166, .13);
            --blue: #2b6f93;
            --leaf: #4f7d54;
            --amber: #c98723;
            --copper: #b86247;
            --red: #cb3f54;
            --violet: #6d587f;
            --ink: #061e27;
            --shadow: 0 24px 70px rgba(8, 36, 43, .16);
            --shadow-soft: 0 12px 30px rgba(8, 36, 43, .10);
            --shadow-tight: 0 8px 16px rgba(8, 36, 43, .08);
        }
        .stApp {
            background:
                linear-gradient(90deg, rgba(43, 111, 147, .055) 1px, transparent 1px),
                linear-gradient(0deg, rgba(16, 184, 166, .05) 1px, transparent 1px),
                linear-gradient(180deg, #f9fdfb 0%, #eef6f4 48%, #e4efec 100%);
            background-size: 36px 36px, 36px 36px, auto;
            color: var(--text);
            font-family: "Noto Sans Devanagari", "Mangal", "Nirmala UI", "Segoe UI", Arial, sans-serif;
        }
        header[data-testid="stHeader"] { background: rgba(248, 252, 251, .86); backdrop-filter: blur(12px); }
        #MainMenu, footer { visibility: hidden; }
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stAppDeployButton"],
        [data-testid="stDeployButton"],
        [data-testid="stManageAppButton"],
        [data-testid="manage-app-button"],
        button[aria-label*="Manage"],
        a[aria-label*="Manage"],
        div[aria-label*="Manage"],
        [aria-label="Manage app"],
        [aria-label*="Manage app"],
        [title="Manage app"],
        [title*="Manage app"],
        [class*="stDeployButton"],
        [class*="stAppDeployButton"],
        [class*="deployButton"],
        [class*="ManageApp"],
        [class*="manageApp"],
        .stDeployButton {
            display: none !important;
            visibility: hidden !important;
        }
        div:has(> [aria-label*="Manage app"]),
        div:has(> [title*="Manage app"]),
        div:has(> [data-testid="stAppDeployButton"]),
        div:has(> [data-testid="stManageAppButton"]) {
            right: auto !important;
            left: 16px !important;
            bottom: 16px !important;
        }
        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, #092d37 0%, #071d25 56%, #041318 100%);
            border-right: 1px solid rgba(255,255,255,.1);
            box-shadow: 18px 0 42px rgba(8, 38, 49, .14);
        }
        [data-testid="stSidebar"] * { color: #efffff; }
        .sidebar-brand {
            border: 1px solid rgba(255, 255, 255, .14);
            background:
                linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px),
                linear-gradient(0deg, rgba(255,255,255,.04) 1px, transparent 1px),
                rgba(255, 255, 255, .06);
            background-size: 22px 22px;
            border-radius: 8px;
            padding: 14px 14px 13px;
            margin-bottom: 18px;
        }
        .brand-row {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .brand-mark {
            width: 38px;
            height: 38px;
            border-radius: 10px;
            display: grid;
            place-items: center;
            color: #042029 !important;
            font-weight: 950;
            background: linear-gradient(135deg, #f4fff9, #22dfc9);
            box-shadow: 0 0 0 4px rgba(34, 223, 201, .16);
        }
        .brand-name {
            display: block;
            color: #ffffff;
            font-size: 1.16rem;
            font-weight: 900;
            line-height: 1;
        }
        .brand-sub {
            display: block;
            color: rgba(232, 255, 251, .68);
            font-size: .78rem;
            margin-top: 5px;
        }
        [data-testid="stSidebar"] h2 {
            font-size: 1.35rem;
            margin: 0 0 1rem 0;
            letter-spacing: .01em;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label {
            border: 1px solid rgba(255, 255, 255, .08);
            border-radius: 8px;
            padding: 10px 11px;
            margin: 5px 0;
            background: rgba(255, 255, 255, .06);
            transition: border-color .16s ease, background .16s ease, transform .16s ease;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            border-color: rgba(98, 224, 204, .6);
            background: rgba(98, 224, 204, .14);
            transform: translateX(2px);
        }
        .block-container { padding-top: 1rem; padding-bottom: 3rem; max-width: 1260px; }
        h1, h2, h3 { letter-spacing: 0; color: var(--text); }
        h1 { font-size: clamp(2.25rem, 4vw, 4.25rem); line-height: .98; margin-bottom: .6rem; font-weight: 900; }
        h2 { font-size: 1.38rem; }
        h3 { font-size: 1.05rem; }
        p, li, label, .stMarkdown { color: var(--text); }
        .stCaptionContainer, [data-testid="stCaptionContainer"] { color: var(--muted); }
        .muted { color: var(--muted); }
        .command-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            border: 1px solid var(--line);
            background: rgba(251, 255, 253, .82);
            backdrop-filter: blur(14px);
            border-radius: 8px;
            padding: 10px 13px;
            margin: 0 0 14px;
            box-shadow: var(--shadow-tight);
        }
        .command-text {
            color: var(--muted);
            font-size: .94rem;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            display: inline-block;
            border-radius: 999px;
            background: var(--mint);
            box-shadow: 0 0 18px rgba(69, 224, 199, .8);
            margin-right: 8px;
        }
        .page-head {
            border: 1px solid rgba(255,255,255,.28);
            background:
                linear-gradient(90deg, rgba(255,255,255,.055) 1px, transparent 1px),
                linear-gradient(0deg, rgba(255,255,255,.045) 1px, transparent 1px),
                linear-gradient(135deg, #082631 0%, #145765 58%, #276e61 100%);
            background-size: 30px 30px, 30px 30px, auto;
            border-radius: 8px;
            padding: 25px 28px;
            margin-bottom: 20px;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }
        .page-head h1 { color: #ffffff; }
        .page-head p { margin-bottom: 0; color: rgba(239, 255, 252, .82); max-width: 860px; }
        .clinical-rail {
            height: 24px;
            display: flex;
            align-items: end;
            gap: 4px;
            margin: 0 0 12px;
        }
        .clinical-rail span {
            width: 5px;
            border-radius: 999px 999px 0 0;
            background: linear-gradient(180deg, var(--mint), rgba(69, 224, 199, .18));
            opacity: .86;
        }
        .clinical-rail span:nth-child(1) { height: 8px; }
        .clinical-rail span:nth-child(2) { height: 16px; background: linear-gradient(180deg, var(--blue), rgba(126, 183, 255, .14)); }
        .clinical-rail span:nth-child(3) { height: 11px; }
        .clinical-rail span:nth-child(4) { height: 24px; background: linear-gradient(180deg, var(--amber), rgba(244, 189, 95, .14)); }
        .clinical-rail span:nth-child(5) { height: 9px; }
        .clinical-rail span:nth-child(6) { height: 18px; }
        .pulse-line {
            width: min(360px, 65%);
            height: 24px;
            margin: 13px 0 0;
            border-bottom: 1px solid rgba(255,255,255,.26);
            position: relative;
        }
        .pulse-line:before {
            content: "";
            position: absolute;
            inset: 8px auto auto 0;
            width: 100%;
            height: 2px;
            background:
                linear-gradient(90deg,
                    rgba(255,255,255,.22) 0 18%,
                    var(--mint) 18% 24%,
                    rgba(255,255,255,.22) 24% 34%,
                    var(--amber) 34% 39%,
                    rgba(255,255,255,.22) 39% 58%,
                    var(--copper) 58% 63%,
                    rgba(255,255,255,.22) 63% 100%);
            border-radius: 999px;
        }
        .hero {
            border: 1px solid rgba(255,255,255,.28);
            background:
                linear-gradient(90deg, rgba(255,255,255,.06) 1px, transparent 1px),
                linear-gradient(0deg, rgba(255,255,255,.045) 1px, transparent 1px),
                linear-gradient(135deg, #082631 0%, #145765 56%, #276e61 100%);
            background-size: 32px 32px, 32px 32px, auto;
            border-radius: 8px;
            padding: 34px;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }
        .hero-layout {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(280px, 360px);
            gap: 28px;
            align-items: end;
        }
        .hero h1 { color: #ffffff; }
        .hero .muted { color: rgba(239,255,252,.84); }
        .hero-copy .muted {
            max-width: 780px;
            font-size: 1.08rem;
            line-height: 1.65;
        }
        .hero h1, .page-head h1 {
            text-wrap: balance;
        }
        .hero-stats {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px;
            margin-top: 22px;
            max-width: 720px;
        }
        .hero-stat {
            border: 1px solid rgba(255,255,255,.2);
            background: rgba(255,255,255,.1);
            border-radius: 8px;
            padding: 10px 12px;
            color: rgba(239,255,252,.9);
            min-height: 66px;
        }
        .monitor-card {
            border: 1px solid rgba(255,255,255,.22);
            background:
                linear-gradient(90deg, rgba(255,255,255,.055) 1px, transparent 1px),
                linear-gradient(0deg, rgba(255,255,255,.045) 1px, transparent 1px),
                rgba(3, 22, 28, .36);
            background-size: 18px 18px;
            border-radius: 8px;
            padding: 18px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.12), 0 18px 42px rgba(0,0,0,.18);
        }
        .monitor-top {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            color: rgba(239,255,252,.72);
            font-size: .78rem;
            text-transform: uppercase;
            font-weight: 800;
            letter-spacing: .08em;
            margin-bottom: 20px;
        }
        .monitor-wave {
            height: 72px;
            border-top: 1px solid rgba(255,255,255,.12);
            border-bottom: 1px solid rgba(255,255,255,.12);
            position: relative;
            margin-bottom: 18px;
        }
        .monitor-wave:before {
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            top: 34px;
            height: 3px;
            background:
                linear-gradient(90deg,
                    rgba(255,255,255,.20) 0 9%,
                    var(--mint) 9% 16%,
                    rgba(255,255,255,.20) 16% 25%,
                    var(--amber) 25% 29%,
                    rgba(255,255,255,.20) 29% 44%,
                    var(--red) 44% 49%,
                    rgba(255,255,255,.20) 49% 68%,
                    #7eb8ff 68% 74%,
                    rgba(255,255,255,.20) 74% 100%);
            border-radius: 999px;
            box-shadow: 0 0 24px rgba(16,184,166,.3);
        }
        .monitor-readouts {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 8px;
        }
        .monitor-readouts div {
            border: 1px solid rgba(255,255,255,.14);
            border-radius: 7px;
            padding: 9px;
            background: rgba(255,255,255,.07);
        }
        .monitor-readouts span {
            display: block;
            color: rgba(239,255,252,.62);
            font-size: .72rem;
            margin-bottom: 3px;
        }
        .monitor-readouts b {
            color: #ffffff;
            font-size: 1.12rem;
        }
        .hero-stat b {
            color: #ffffff;
            display: block;
            font-size: 1.08rem;
            margin-bottom: 4px;
        }
        .st-key-home_actions {
            margin-top: 6px;
        }
        .st-key-home_actions .stButton>button {
            background:
                linear-gradient(180deg, rgba(255,255,255,.98), rgba(244,250,248,.98)) !important;
            border: 1px solid var(--line) !important;
            border-left: 4px solid var(--mint) !important;
            color: var(--text) !important;
            min-height: 3.25rem;
            border-radius: 8px;
            box-shadow: var(--shadow-soft);
            font-weight: 750;
        }
        .st-key-home_actions .stButton>button p,
        .st-key-home_actions .stButton>button span {
            color: var(--text) !important;
        }
        .st-key-home_actions .stButton>button:hover {
            background:
                linear-gradient(180deg, #ffffff, #eef8f4) !important;
            border-color: rgba(10, 168, 148, .42) !important;
            border-left-color: var(--copper) !important;
            color: var(--text) !important;
            transform: translateY(-2px);
            box-shadow: 0 16px 32px rgba(20, 55, 58, .13);
        }
        .hero:after, .page-head:after {
            content: "";
            position: absolute;
            inset: auto 22px 18px auto;
            width: 168px;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,.55), var(--mint), transparent);
        }
        .panel {
            border: 1px solid var(--line);
            background: var(--surface);
            border-radius: 8px;
            padding: 20px;
            min-height: 100%;
            box-shadow: var(--shadow-soft);
        }
        .metric-card {
            border: 1px solid var(--line);
            background:
                linear-gradient(180deg, rgba(255,255,255,.92) 0%, rgba(244,250,248,.96) 100%);
            border-radius: 8px;
            padding: 16px 16px 15px;
            min-height: 104px;
            box-shadow: var(--shadow-soft);
            position: relative;
            overflow: hidden;
            transition: border-color .16s ease, transform .16s ease, box-shadow .16s ease;
        }
        .metric-card:before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: linear-gradient(180deg, var(--mint), var(--copper));
        }
        .metric-card:hover {
            border-color: rgba(69, 224, 199, .38);
            transform: translateY(-2px);
            box-shadow: 0 20px 40px rgba(20, 55, 58, .14);
        }
        .metric-card b {
            display: block;
            margin-bottom: 8px;
            color: var(--text);
        }
        .metric-card .token {
            color: var(--blue);
            font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
            font-size: .82rem;
            font-weight: 850;
        }
        .command-center {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin: 10px 0 16px;
        }
        .command-card {
            border: 1px solid var(--line);
            background: linear-gradient(180deg, rgba(255,255,255,.97), rgba(244,250,248,.96));
            border-radius: 8px;
            padding: 15px 16px;
            min-height: 104px;
            box-shadow: var(--shadow-soft);
            position: relative;
            overflow: hidden;
        }
        .command-card:before {
            content: "";
            position: absolute;
            inset: 0 0 auto;
            height: 3px;
            background: linear-gradient(90deg, var(--mint), var(--copper));
        }
        .command-card span {
            color: var(--muted);
            display: block;
            font-size: .8rem;
            font-weight: 750;
            text-transform: uppercase;
            letter-spacing: .06em;
            margin-bottom: 8px;
        }
        .command-card b {
            display: block;
            color: var(--text);
            font-size: clamp(1.5rem, 2.4vw, 2.3rem);
            line-height: 1;
            margin-bottom: 8px;
        }
        .command-card small {
            color: var(--muted);
            font-size: .9rem;
        }
        .care-plan {
            border: 1px solid var(--line);
            background:
                linear-gradient(90deg, rgba(10,168,148,.045) 1px, transparent 1px),
                linear-gradient(0deg, rgba(10,168,148,.035) 1px, transparent 1px),
                #fbfefe;
            background-size: 24px 24px;
            border-radius: 8px;
            padding: 16px 17px;
            margin: 14px 0 16px;
            box-shadow: var(--shadow-soft);
            border-left-width: 5px;
        }
        .care-plan h3 {
            margin: 4px 0 6px;
            font-size: 1.15rem;
        }
        .care-plan p {
            margin: 0 0 10px;
            color: var(--muted);
        }
        .care-plan ul {
            margin: 0;
            padding-left: 20px;
        }
        .care-plan li {
            margin: 6px 0;
        }
        .care-emergency { border-left-color: var(--red); }
        .care-urgent { border-left-color: var(--amber); }
        .care-doctor { border-left-color: var(--blue); }
        .care-home { border-left-color: var(--leaf); }
        .risk {
            display: inline-block;
            border: 1px solid rgba(69, 224, 199, .45);
            color: #06100e;
            background: var(--mint);
            border-radius: 999px;
            padding: 8px 12px;
            font-weight: 800;
            margin: 6px 0 12px 0;
        }
        .danger-banner {
            border-radius: 8px;
            padding: 17px 18px;
            margin: 0 0 16px 0;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
        }
        .danger-banner h2 {
            margin: 0 0 4px 0;
            font-size: 1.35rem;
        }
        .danger-banner p { margin: 0; color: rgba(255,255,255,.82); }
        .danger-low {
            background: linear-gradient(135deg, #e8f8ef, #ffffff);
            border-color: #8bdfb9;
        }
        .danger-moderate {
            background: linear-gradient(135deg, #fff3dc, #ffffff);
            border-color: #e9bd69;
        }
        .danger-high {
            background: linear-gradient(135deg, #ffe7eb, #ffffff);
            border-color: #e7909a;
        }
        .danger-banner h2, .danger-banner p { color: var(--text); }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-bottom: 14px;
        }
        .summary-item {
            background: #fbfefe;
            border: 1px solid var(--line-soft);
            border-radius: 8px;
            padding: 11px 12px;
            box-shadow: 0 6px 18px rgba(20, 55, 58, .05);
        }
        .summary-item span {
            display: block;
            color: var(--muted);
            font-size: .76rem;
            text-transform: uppercase;
            letter-spacing: .05em;
            margin-bottom: 4px;
        }
        .empty-result {
            border: 1px dashed #b9cfcc;
            background:
                linear-gradient(90deg, rgba(10,168,148,.045) 1px, transparent 1px),
                linear-gradient(0deg, rgba(10,168,148,.04) 1px, transparent 1px),
                #fbfefe;
            background-size: 26px 26px;
            border-radius: 8px;
            padding: 22px;
            color: var(--muted);
        }
        [data-testid="stExpander"] {
            border: 1px solid var(--line) !important;
            border-radius: 8px !important;
            background: rgba(255, 255, 255, .72) !important;
            overflow: hidden;
            box-shadow: var(--shadow-soft);
        }
        [data-testid="stExpander"] details {
            border: 0 !important;
        }
        [data-testid="stExpander"] summary {
            background: linear-gradient(180deg, #ffffff 0%, #f2faf7 100%) !important;
            border-bottom: 1px solid var(--line-soft) !important;
        }
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary * {
            color: #10252c !important;
            -webkit-text-fill-color: #10252c !important;
            opacity: 1 !important;
        }
        [data-testid="stExpander"] svg {
            color: #0d8f81 !important;
            fill: #0d8f81 !important;
        }
        .soft-badge {
            display: inline-block;
            border: 1px solid rgba(255,255,255,.35);
            background: rgba(255,255,255,.14);
            color: #ffffff;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: .82rem;
            font-weight: 700;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        .sam-box {
            border: 1px solid rgba(10, 168, 148, .46);
            background:
                linear-gradient(180deg, rgba(10, 36, 42, .98), rgba(8, 24, 29, .98));
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 0 0 1px rgba(70, 214, 191, .06), 0 20px 60px rgba(0,0,0,.22);
            position: sticky;
            top: 18px;
        }
        div[data-testid="stPopover"] {
            position: fixed;
            right: 24px;
            bottom: 24px;
            z-index: 100000 !important;
            width: 72px !important;
            min-width: 72px !important;
            max-width: 72px !important;
        }
        div[data-testid="stPopover"] button,
        div[data-testid="stPopover"] > button,
        div[data-testid="stPopover"] button[kind],
        div[data-testid="stPopover"] [role="button"] {
            width: 72px !important;
            height: 72px !important;
            min-width: 72px !important;
            border-radius: 999px !important;
            border: 3px solid #ffffff !important;
            background: linear-gradient(180deg, #21e0c8, #078f82) !important;
            box-shadow: 0 18px 46px rgba(10, 81, 92, .36), 0 0 0 7px rgba(33, 224, 200, .28) !important;
            color: #ffffff !important;
            font-weight: 900 !important;
        }
        div[data-testid="stPopover"] button *,
        div[data-testid="stPopover"] p,
        div[data-testid="stPopover"] span {
            color: #ffffff !important;
            opacity: 1 !important;
        }
        div[data-testid="stPopover"] button:hover {
            border-color: #ffffff !important;
            transform: translateY(-2px);
            box-shadow: 0 24px 60px rgba(10, 81, 92, .42), 0 0 0 8px rgba(33, 224, 200, .34) !important;
        }
        [data-testid="stPopoverBody"],
        [data-testid="stPopoverBody"] * {
            color: #ffffff !important;
        }
        [data-testid="stPopoverBody"] {
            background: #0f141c !important;
        }
        [data-testid="stPopoverBody"] input {
            background: #ffffff !important;
            color: #10252c !important;
            border-color: #21e0c8 !important;
        }
        [data-testid="stPopoverBody"] input::placeholder {
            color: #6f8588 !important;
            opacity: 1 !important;
        }
        [data-testid="stPopoverBody"] button {
            color: #ffffff !important;
            background: linear-gradient(180deg, #21c7b4, #0f8f83) !important;
            border-color: #21e0c8 !important;
        }
        .small-title {
            color: var(--mint);
            text-transform: uppercase;
            font-size: .78rem;
            letter-spacing: .09em;
            font-weight: 800;
        }
        .section-label {
            color: var(--mint);
            font-size: .78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .09em;
            margin: 8px 0 10px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .section-label:after {
            content: "";
            width: 42px;
            height: 1px;
            background: linear-gradient(90deg, var(--mint), transparent);
        }
        .stButton>button,
        [data-testid="stFormSubmitButton"] button {
            border-radius: 6px;
            border: 1px solid var(--line);
            background:
                linear-gradient(180deg, rgba(255,255,255,.98), rgba(244,250,248,.98));
            color: var(--text);
            font-weight: 700;
            min-height: 2.45rem;
            box-shadow: 0 6px 16px rgba(20, 55, 58, .08);
        }
        .stButton>button *,
        .stButton>button p,
        [data-testid="stFormSubmitButton"] button *,
        [data-testid="stFormSubmitButton"] button p {
            color: var(--text);
        }
        .stButton>button:hover,
        [data-testid="stFormSubmitButton"] button:hover {
            border-color: rgba(10, 168, 148, .45);
            color: var(--text);
            background:
                linear-gradient(180deg, #ffffff, #eef8f4);
            box-shadow: 0 10px 22px rgba(20, 55, 58, .12);
            transform: translateY(-1px);
        }
        .stButton>button[kind="primary"],
        [data-testid="stDownloadButton"] button {
            border-radius: 6px;
            border: 1px solid #0a897b;
            background: linear-gradient(180deg, #13aa98, #08796d);
            color: #ffffff;
            font-weight: 750;
            min-height: 2.45rem;
            box-shadow: 0 8px 18px rgba(8, 121, 109, .18);
        }
        .stButton>button[kind="primary"] *,
        .stButton>button[kind="primary"] p,
        [data-testid="stDownloadButton"] button *,
        [data-testid="stDownloadButton"] button p {
            color: #ffffff;
        }
        .stButton>button[kind="primary"]:hover,
        [data-testid="stDownloadButton"] button:hover {
            border-color: var(--mint);
            color: #ffffff;
            background: #086f66;
            box-shadow: 0 12px 24px rgba(8, 121, 109, .22);
        }
        .stButton>button:focus, [data-testid="stDownloadButton"] button:focus, .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
            outline: 2px solid rgba(181, 109, 74, .5) !important;
            outline-offset: 2px;
        }
        .stTextInput input, .stNumberInput input, .stTextArea textarea {
            background: rgba(255,255,255,.96);
            color: var(--text);
            border: 1px solid var(--line);
            border-radius: 7px;
            box-shadow: 0 1px 0 rgba(10, 25, 32, .03), inset 0 1px 0 rgba(255,255,255,.7);
        }
        div[data-baseweb="select"] > div {
            background: rgba(255,255,255,.96);
            border-color: var(--line);
            border-radius: 7px;
            color: var(--text);
        }
        [data-testid="stSidebar"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] div[data-baseweb="select"] span {
            color: #10252c !important;
            background: #ffffff !important;
        }
        [data-testid="stSidebar"] div[data-baseweb="select"] > div * {
            color: #10252c !important;
            -webkit-text-fill-color: #10252c !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] div[data-baseweb="select"] input {
            color: #10252c !important;
            -webkit-text-fill-color: #10252c !important;
        }
        [data-testid="stSidebar"] div[data-baseweb="select"] svg {
            color: #0d8f81 !important;
            fill: #0d8f81 !important;
        }
        [data-testid="stMultiSelect"] div {
            color: var(--text);
        }
        [data-testid="stMetric"] {
            border: 1px solid var(--line);
            background: linear-gradient(180deg, #ffffff, #f4faf8);
            border-radius: 8px;
            padding: 14px;
            box-shadow: var(--shadow-tight);
        }
        [data-testid="stMetricValue"] {
            font-size: clamp(1.6rem, 3vw, 2.45rem);
            line-height: 1.08;
            white-space: normal;
            overflow-wrap: anywhere;
        }
        .snapshot-card {
            border: 1px solid var(--line);
            background:
                linear-gradient(180deg, rgba(255,255,255,.96), rgba(246,251,249,.96));
            border-radius: 8px;
            padding: 16px 18px;
            min-height: 118px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 10px;
            box-shadow: var(--shadow-soft);
        }
        .snapshot-label {
            color: var(--muted);
            font-size: .96rem;
            font-weight: 650;
        }
        .snapshot-value {
            color: var(--text);
            font-size: clamp(1.8rem, 2.6vw, 2.65rem);
            line-height: 1.05;
            font-weight: 550;
            white-space: normal;
            overflow-wrap: anywhere;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: var(--shadow-soft);
        }
        .stAlert {
            border-radius: 8px;
            border: 1px solid var(--line-soft);
        }
        .element-container:has(.section-label) + div [data-testid="stVerticalBlock"],
        [data-testid="stForm"] {
            border-radius: 8px;
        }
        code {
            color: #075e57;
            background: #edf8f6;
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: 2px 5px;
        }
        hr { border-color: var(--line-soft); }
        .dashboard-shell {
            display: grid;
            gap: 18px;
        }
        .app-hero {
            border: 1px solid var(--line);
            background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(246,252,249,.94));
            border-radius: 8px;
            padding: 22px 24px;
            box-shadow: var(--shadow-soft);
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 18px;
        }
        .app-hero h1 {
            margin: 3px 0 8px;
            font-size: clamp(2.2rem, 4vw, 3.8rem);
            line-height: 1;
            color: var(--ink);
        }
        .app-hero p {
            margin: 0;
            max-width: 720px;
            color: var(--muted);
            font-size: 1.02rem;
            line-height: 1.55;
        }
        .safety-badge {
            border: 1px solid #f0c7bc;
            background: #fff4f1;
            color: #8b3f31;
            border-radius: 999px;
            padding: 8px 12px;
            font-size: .78rem;
            font-weight: 800;
            white-space: nowrap;
        }
        .home-workspace {
            display: grid;
            grid-template-columns: minmax(0, 1.14fr) minmax(320px, .86fr);
            gap: 18px;
            align-items: stretch;
        }
        .workspace-panel {
            border: 1px solid var(--line);
            background: rgba(255,255,255,.95);
            border-radius: 8px;
            padding: 18px;
            box-shadow: var(--shadow-soft);
            min-height: 100%;
        }
        .workspace-panel h2 {
            margin: 3px 0 6px;
            font-size: 1.18rem;
        }
        .panel-row {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
            margin-top: 12px;
        }
        .field-preview {
            border: 1px solid var(--line-soft);
            background: #fbfffd;
            border-radius: 8px;
            padding: 12px;
            min-height: 70px;
        }
        .field-preview span {
            display: block;
            color: var(--muted);
            font-size: .75rem;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }
        .clinical-chip {
            border: 1px solid #b8dcd6;
            background: #eefaf7;
            color: #0d5d58;
            border-radius: 999px;
            padding: 6px 10px;
            font-size: .82rem;
            font-weight: 750;
        }
        .slider-preview {
            height: 8px;
            border-radius: 999px;
            background: linear-gradient(90deg, #17b6a5 0 62%, #e7ecea 62% 100%);
            margin-top: 10px;
            position: relative;
        }
        .slider-preview:after {
            content: "";
            position: absolute;
            left: 62%;
            top: 50%;
            width: 18px;
            height: 18px;
            border-radius: 999px;
            background: #ffffff;
            border: 3px solid #17b6a5;
            transform: translate(-50%, -50%);
            box-shadow: 0 4px 12px rgba(13, 93, 88, .22);
        }
        .primary-preview {
            margin-top: 16px;
            border-radius: 6px;
            background: linear-gradient(180deg, #13aa98, #08796d);
            color: #ffffff;
            min-height: 44px;
            display: grid;
            place-items: center;
            font-weight: 850;
            box-shadow: 0 12px 24px rgba(8, 121, 109, .18);
        }
        .home-live-form [data-testid="stVerticalBlock"] {
            gap: .75rem;
        }
        .home-live-form .stButton>button {
            min-height: 4.15rem;
            font-size: 1.15rem;
            border-radius: 8px;
        }
        .result-preview {
            border-left: 5px solid var(--amber);
        }
        .score-ring {
            width: 132px;
            height: 132px;
            border-radius: 999px;
            background:
                radial-gradient(circle at center, #ffffff 0 58%, transparent 59%),
                conic-gradient(var(--amber) 0 62%, #e5efec 62% 100%);
            display: grid;
            place-items: center;
            margin: 14px auto 16px;
            box-shadow: inset 0 0 0 1px var(--line-soft);
        }
        .score-ring b {
            font-size: 1.65rem;
            color: var(--ink);
        }
        .urgency-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            background: #fff3dc;
            border: 1px solid #e8bd69;
            color: #7b4d0f;
            padding: 7px 11px;
            font-size: .82rem;
            font-weight: 850;
        }
        .doctor-strip {
            display: grid;
            grid-template-columns: minmax(0, 1.1fr) minmax(280px, .9fr);
            gap: 18px;
        }
        .mini-table {
            width: 100%;
            border-collapse: collapse;
            overflow: hidden;
            border-radius: 8px;
            font-size: .88rem;
        }
        .mini-table th,
        .mini-table td {
            border-bottom: 1px solid var(--line-soft);
            padding: 10px 9px;
            text-align: left;
        }
        .mini-table th {
            color: var(--muted);
            font-size: .74rem;
            text-transform: uppercase;
        }
        .trend-card {
            border: 1px solid var(--line-soft);
            border-radius: 8px;
            background: #fbfffd;
            padding: 14px;
        }
        .trend-line {
            height: 120px;
            border-left: 1px solid #d7e6e2;
            border-bottom: 1px solid #d7e6e2;
            background:
                linear-gradient(180deg, transparent 24%, rgba(16,184,166,.08) 24% 25%, transparent 25% 49%, rgba(16,184,166,.08) 49% 50%, transparent 50% 74%, rgba(16,184,166,.08) 74% 75%, transparent 75%),
                linear-gradient(135deg, transparent 0 18%, rgba(16,184,166,.18) 18% 19%, transparent 19% 38%, rgba(16,184,166,.25) 38% 39%, transparent 39% 61%, rgba(201,135,35,.28) 61% 62%, transparent 62% 82%, rgba(184,98,71,.32) 82% 83%, transparent 83%);
        }
        @media (max-width: 720px) {
            h1 { font-size: 2.35rem; }
            .hero, .page-head, .panel { padding: 18px; }
            .hero-layout { grid-template-columns: 1fr; }
            .hero-stats { grid-template-columns: 1fr; }
            .monitor-card { display: none; }
            .command-center { grid-template-columns: 1fr; }
            .app-hero,
            .home-workspace,
            .doctor-strip,
            .panel-row {
                grid-template-columns: 1fr;
            }
            .app-hero {
                display: grid;
            }
            .pulse-line { width: 100%; }
            .command-bar { align-items: flex-start; flex-direction: column; }
            .summary-grid { grid-template-columns: 1fr; }
            div[data-testid="stPopover"] {
                right: 16px;
                bottom: 16px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    st.session_state.setdefault("page", "Home")
    pending_page = st.session_state.pop("pending_page", None)
    if pending_page in PAGES:
        st.session_state.page = pending_page
        st.session_state.page_picker = pending_page
    if st.session_state.page not in PAGES:
        st.session_state.page = "Home"
    st.session_state.setdefault("page_picker", st.session_state.page)
    if st.session_state.page_picker not in PAGES:
        st.session_state.page_picker = st.session_state.page
    st.session_state.setdefault("score", 0)
    st.session_state.setdefault("scenario_index", 0)
    st.session_state.setdefault("checker_result", None)
    st.session_state.setdefault("checker_patient_data", None)
    st.session_state.setdefault("patient_profile", {})
    st.session_state.setdefault("language", "🇺🇸 English")
    if st.session_state.language not in LANGUAGE_OPTIONS:
        st.session_state.language = "🇺🇸 English"
    st.session_state.setdefault("language_picker", st.session_state.language)
    if st.session_state.language_picker not in LANGUAGE_OPTIONS:
        st.session_state.language_picker = st.session_state.language
    st.session_state.setdefault("offline_mode", False)
    st.session_state.setdefault("preloaded_languages", [])
    st.session_state.setdefault("prepared_languages", [])


def sidebar() -> None:
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-row">
                <div class="brand-mark">L</div>
                <div>
                    <span class="brand-name">LifeLine AI</span>
                    <span class="brand-sub">Triage workspace</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_language = st.sidebar.selectbox(
        "Language",
        LANGUAGE_OPTIONS,
        key="language_picker",
    )
    language_changed = selected_language != st.session_state.language
    if language_changed:
        st.session_state.language = selected_language
        prepare_language(st.session_state.language)
        st.rerun()
    offline_mode = st.sidebar.checkbox(
        "Offline mode",
        value=bool(st.session_state.offline_mode),
    )
    if offline_mode != st.session_state.offline_mode:
        st.session_state.offline_mode = offline_mode
        st.rerun()
    if st.session_state.offline_mode:
        st.sidebar.caption("Offline mode: local rules only.")
    st.sidebar.caption(tr("Smart inside. Simple outside."))
    selected_page = st.sidebar.radio(
        tr("Navigation"),
        PAGES,
        key="page_picker",
        label_visibility="collapsed",
        format_func=lambda page: tr(page),
    )
    page_changed = selected_page != st.session_state.page
    if page_changed:
        st.session_state.page = selected_page
    st.sidebar.divider()
    st.sidebar.caption(tr("Decision support. Not a replacement for doctors."))


def switch_page(page: str) -> None:
    if page in PAGES:
        st.session_state.page = page
        st.session_state.pending_page = page
        st.rerun()


def stable_key(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")


def render_quick_jumps(prefix: str, exclude: str | None = None) -> None:
    targets = [
        ("Health Checker", "Patient Health Checker"),
        ("Timeline", "Health Timeline"),
        ("Health & Medicine Q&A", "Disease Q&A Assistant"),
        ("Medication Safety", "Medication Safety Checker"),
        ("Doctor Dashboard", "Doctor Dashboard"),
        ("Scenario Challenge", "Scenario Challenge"),
    ]
    cols = st.columns(len(targets))
    for index, (label, page) in enumerate(targets):
        disabled = page == exclude
        if cols[index].button(tr(label), key=f"{prefix}_{stable_key(page)}", disabled=disabled, width="stretch"):
            switch_page(page)


def danger_status(risk_level: str) -> dict[str, str]:
    if risk_level == "Self-Care":
        return {
            "label": "LOW DANGER",
            "class": "danger-low",
            "text": "Home monitoring may be enough for now, but watch for changes.",
        }
    if risk_level == "Doctor Visit Recommended":
        return {
            "label": "MODERATE DANGER",
            "class": "danger-moderate",
            "text": "A doctor visit is recommended, especially if symptoms continue or worsen.",
        }
    return {
        "label": "HIGH DANGER",
        "class": "danger-high",
        "text": "This needs urgent attention. Do not delay medical help.",
    }


def compact_risk_label(risk_level: str) -> str:
    if risk_level == "Emergency":
        return "Critical"
    if risk_level == "Doctor Visit Recommended":
        return "Doctor Visit"
    return risk_level


def patient_case_name(case: dict[str, Any]) -> str:
    return str(case.get("patient_name") or "Anonymous")


def patient_data_name(patient_data: dict[str, Any]) -> str:
    return str(patient_data.get("patient_name") or "Anonymous")


def latest_previous_case(patient_data: dict[str, Any]) -> dict[str, Any] | None:
    patient_name = patient_data_name(patient_data)
    matching_cases = [
        case
        for case in list_cases()
        if patient_case_name(case) == patient_name
    ]
    if not matching_cases:
        return None
    matching_cases.sort(key=lambda case: str(case.get("created_at", "")))
    return matching_cases[-1]


def describe_number_change(label: str, previous: float | None, current: float | None, unit: str = "") -> str | None:
    if previous is None or current is None:
        return None
    delta = current - previous
    if abs(delta) < 0.01:
        return f"{label} stayed the same at {current:g}{unit}."
    direction = "increased" if delta > 0 else "decreased"
    return f"{label} {direction} from {previous:g}{unit} to {current:g}{unit}."


def build_previous_check_comparison(
    patient_data: dict[str, Any],
    result: Any,
    previous_case: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not previous_case:
        return None

    previous_raw = parse_case_raw_data(previous_case.get("raw_data"))
    previous_symptoms = {str(item).strip().lower() for item in previous_raw.get("symptoms", []) if str(item).strip()}
    current_symptoms = {str(item).strip().lower() for item in patient_data.get("symptoms", []) if str(item).strip()}
    new_symptoms = sorted(current_symptoms - previous_symptoms)
    resolved_symptoms = sorted(previous_symptoms - current_symptoms)

    previous_risk = str(previous_case.get("risk_level") or "Unknown")
    current_risk = str(result.risk_level)
    previous_score = safe_number(previous_case.get("score")) or 0
    current_score = safe_number(result.score) or 0
    previous_pain = safe_number(previous_raw.get("pain_level"))
    current_pain = safe_number(patient_data.get("pain_level"))
    previous_rank = RISK_ORDER.get(previous_risk, 0)
    current_rank = RISK_ORDER.get(current_risk, 0)

    highlights: list[str] = []
    if current_rank > previous_rank:
        highlights.append(f"Care level increased from {compact_risk_label(previous_risk)} to {compact_risk_label(current_risk)}.")
    elif current_rank < previous_rank:
        highlights.append(f"Care level decreased from {compact_risk_label(previous_risk)} to {compact_risk_label(current_risk)}.")
    else:
        highlights.append(f"Care level stayed at {compact_risk_label(current_risk)}.")

    for note in [
        describe_number_change("Risk score", previous_score, current_score),
        describe_number_change("Pain level", previous_pain, current_pain, "/10"),
    ]:
        if note:
            highlights.append(note)
    if new_symptoms:
        highlights.append(f"New symptoms: {', '.join(item.title() for item in new_symptoms[:6])}.")
    if resolved_symptoms:
        highlights.append(f"No longer listed: {', '.join(item.title() for item in resolved_symptoms[:6])}.")

    return {
        "previous_created_at": previous_case.get("created_at", ""),
        "previous_risk": previous_risk,
        "current_risk": current_risk,
        "previous_score": previous_score,
        "current_score": current_score,
        "highlights": highlights,
    }


def snapshot_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="snapshot-card">
            <div class="snapshot-label">{h(label)}</div>
            <div class="snapshot-value">{h(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_timeline_trend_frame(cases: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, case in enumerate(cases, start=1):
        raw = parse_case_raw_data(case.get("raw_data"))
        rows.append(
            {
                "Check": index,
                "Created": pd.to_datetime(case.get("created_at"), errors="coerce"),
                "Risk score": safe_number(case.get("score")) or 0,
                "Pain level": safe_number(raw.get("pain_level")),
                "Temperature": safe_number(raw.get("temperature")),
                "Oxygen": safe_number(raw.get("oxygen")),
                "Pulse": safe_number(raw.get("heart_rate")),
                "Systolic BP": safe_number(raw.get("systolic_bp")),
                "Diastolic BP": safe_number(raw.get("diastolic_bp")),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    chart_columns = ["Risk score", "Pain level", "Temperature", "Oxygen", "Pulse", "Systolic BP", "Diastolic BP"]
    frame[chart_columns] = frame[chart_columns].apply(pd.to_numeric, errors="coerce")
    return frame.set_index("Check")


def render_zero_based_line_chart(frame: pd.DataFrame) -> None:
    chart_data = (
        frame.reset_index()
        .melt(id_vars="Check", var_name="Metric", value_name="Value")
        .dropna(subset=["Value"])
    )
    chart = (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("Check:O", title="Check"),
            y=alt.Y("Value:Q", title=None, scale=alt.Scale(zero=True)),
            color=alt.Color("Metric:N", title=None),
            tooltip=[
                alt.Tooltip("Check:O", title="Check"),
                alt.Tooltip("Metric:N", title="Metric"),
                alt.Tooltip("Value:Q", title="Value"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(chart, use_container_width=True)


def case_queue_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    high_priority = [
        case
        for case in cases
        if str(case.get("risk_level")) in {"Emergency", "Urgent Care"}
    ]
    new_reviews = [
        case
        for case in cases
        if str(case.get("review_status") or "New") == "New"
    ]
    resolved = [
        case
        for case in cases
        if str(case.get("review_status") or "") == "Resolved"
    ]
    categories = [str(case.get("category") or "General Health") for case in cases]
    most_common = "N/A"
    if categories:
        most_common = pd.Series(categories).value_counts().index[0]
    return {
        "total": len(cases),
        "high_priority": len(high_priority),
        "new_reviews": len(new_reviews),
        "resolved": len(resolved),
        "most_common": most_common,
    }


def action_plan_for_result(result: Any) -> dict[str, Any]:
    if result.risk_level == "Emergency":
        return {
            "class": "care-emergency",
            "badge": "Immediate safety steps",
            "title": "Emergency action plan",
            "summary": "This result includes emergency warning signs. Treat it as time-sensitive.",
            "steps": [
                "Call local emergency services or go to emergency care now.",
                "Do not drive yourself if there is chest pain, fainting, severe breathing difficulty, confusion, or stroke signs.",
                "Keep the patient sitting or lying down and monitor breathing.",
                "Have medicines, allergies, symptoms, and recent measurements ready for clinicians.",
            ],
        }
    if result.risk_level == "Urgent Care":
        return {
            "class": "care-urgent",
            "badge": "Care action plan",
            "title": "Same-day care plan",
            "summary": "This result needs fast medical review, especially if symptoms continue or worsen.",
            "steps": [
                "Arrange clinic or hospital care as soon as possible today.",
                "Recheck breathing, fever, pain, oxygen, pulse, or blood pressure if available.",
                "Avoid heavy activity until a clinician has reviewed the situation.",
                "Use the doctor summary when speaking with the care team.",
            ],
        }
    if result.risk_level == "Doctor Visit Recommended":
        return {
            "class": "care-doctor",
            "badge": "Care action plan",
            "title": "Doctor visit prep plan",
            "summary": "This result is not usually an emergency, but it should be checked by a doctor.",
            "steps": [
                "Book a doctor visit and bring the saved health summary.",
                "Track whether symptoms improve, stay the same, or get worse.",
                "Write down current medicines, allergies, and questions before the visit.",
                "Seek faster care if any red flag appears.",
            ],
        }
    return {
        "class": "care-home",
        "badge": "Care action plan",
        "title": "Home monitoring plan",
        "summary": "This result looks lower risk right now, but symptoms should still be watched.",
        "steps": [
            "Rest, drink fluids if appropriate, and follow basic home care steps.",
            "Check symptoms again if the condition changes or lasts longer than expected.",
            "Avoid mixing medicines without asking a doctor or pharmacist.",
            "Move to faster care if red flags appear.",
        ],
    }


def render_command_center_cards(items: list[tuple[str, str, str]]) -> None:
    cards = "".join(
        f'<div class="command-card"><span>{h(label)}</span><b>{h(value)}</b><small>{h(detail)}</small></div>'
        for label, value, detail in items
    )
    st.markdown(f'<div class="command-center">{cards}</div>', unsafe_allow_html=True)


def render_home_command_center() -> None:
    cases = list_cases()
    summary = case_queue_summary(cases)
    render_command_center_cards(
        [
            ("Saved cases", str(summary["total"]), "Ready for the next check"),
            ("High-priority cases", str(summary["high_priority"]), "Cases needing attention"),
            ("New reviews", str(summary["new_reviews"]), "Review priority"),
            ("Resolved", str(summary["resolved"]), "Doctor Dashboard"),
        ]
    )


def render_care_action_plan(result: Any) -> None:
    plan = action_plan_for_result(result)
    steps = "\n".join(f"<li>{h(step)}</li>" for step in plan["steps"])
    st.markdown(
        f"""
        <div class="care-plan {plan['class']}">
            <div class="small-title">{h(plan['badge'])}</div>
            <h3>{h(plan['title'])}</h3>
            <p>{h(plan['summary'])}</p>
            <ul>{steps}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_queue_insights(cases: list[dict[str, Any]]) -> None:
    summary = case_queue_summary(cases)
    priority = "Review emergency and urgent cases first." if summary["high_priority"] else "No urgent queue pressure right now."
    if summary["new_reviews"] and not summary["high_priority"]:
        priority = "Review new cases before resolved cases."
    render_command_center_cards(
        [
            ("Cases needing attention", str(summary["high_priority"]), priority),
            ("New reviews", str(summary["new_reviews"]), "Review priority"),
            ("Most common pattern", str(summary["most_common"]), "Likely pattern"),
            ("Resolved", str(summary["resolved"]), "Doctor Dashboard"),
        ]
    )


def render_count_bar_chart(counts: pd.Series, label: str) -> None:
    if counts.empty:
        st.info(tr("No matching data to chart."))
        return

    chart_df = counts.rename_axis(label).reset_index(name="Cases")
    chart_df[label] = chart_df[label].fillna("Unknown").astype(str)
    signed_axis = {
        "title": tr("Cases"),
        "labelExpr": "datum.value < 0 ? '-' + abs(datum.value) : '' + datum.value",
        "labelPadding": 10,
        "grid": True,
    }
    spec = {
        "height": 250,
        "mark": {
            "type": "bar",
            "color": "#7cc8f4",
            "cornerRadiusTopLeft": 4,
            "cornerRadiusTopRight": 4,
        },
        "encoding": {
            "x": {
                "field": label,
                "type": "nominal",
                "sort": "-y",
                "axis": {"title": None, "labelAngle": -65, "labelLimit": 150},
            },
            "y": {
                "field": "Cases",
                "type": "quantitative",
                "scale": {"zero": True},
                "axis": signed_axis,
            },
            "tooltip": [
                {"field": label, "type": "nominal", "title": tr(label)},
                {"field": "Cases", "type": "quantitative", "title": tr("Cases")},
            ],
        },
        "config": {
            "view": {"stroke": None},
            "axis": {
                "domainColor": "#343c46",
                "gridColor": "#28313b",
                "labelColor": "#eaf6f6",
                "titleColor": "#eaf6f6",
                "tickColor": "#343c46",
            },
        },
    }
    st.vega_lite_chart(chart_df, spec, width="stretch")


def fast_analyze_patient(data: dict[str, Any]) -> Any:
    try:
        return analyze_patient(data, use_ml=False)
    except TypeError:
        return analyze_patient(data)


def risk_score_range(risk_level: str) -> str:
    ranges = {
        "Self-Care": "0-21",
        "Doctor Visit Recommended": "22-44",
        "Urgent Care": "45-69",
        "Emergency": "70-100",
    }
    return ranges.get(risk_level, "0-100")


def challenge_measurement_summary(data: dict[str, Any]) -> list[str]:
    measurements: list[str] = []
    if data.get("temperature"):
        temperature = float(data["temperature"])
        if temperature >= 39.4:
            note = "very high fever"
        elif temperature >= 38:
            note = "fever"
        else:
            note = "normal temperature"
        measurements.append(f"Temperature {temperature:g} C ({note})")
    if data.get("pain_level") is not None:
        pain = int(data["pain_level"])
        if pain >= 8:
            note = "severe pain"
        elif pain >= 5:
            note = "moderate pain"
        else:
            note = "mild pain"
        measurements.append(f"Pain {pain}/10 ({note})")
    if data.get("oxygen"):
        oxygen = int(data["oxygen"])
        if oxygen < 90:
            note = "dangerously low"
        elif oxygen < 94:
            note = "lower than expected"
        else:
            note = "normal"
        measurements.append(f"Oxygen {oxygen}% ({note})")
    if data.get("heart_rate"):
        heart_rate = int(data["heart_rate"])
        note = "outside usual resting range" if heart_rate < 50 or heart_rate > 120 else "usual resting range"
        measurements.append(f"Pulse {heart_rate}/min ({note})")
    if data.get("systolic_bp") and data.get("diastolic_bp"):
        systolic = int(data["systolic_bp"])
        diastolic = int(data["diastolic_bp"])
        if systolic >= 180 or diastolic >= 120:
            note = "danger range"
        elif systolic >= 140 or diastolic >= 90:
            note = "high"
        else:
            note = "not high"
        measurements.append(f"Blood pressure {systolic}/{diastolic} ({note})")
    if data.get("duration_days") is not None:
        days = int(data["duration_days"])
        note = "needs checking if not improving" if days >= 3 else "short duration"
        measurements.append(f"Duration {days} day(s) ({note})")
    return measurements


def care_level_explanation(level: str) -> str:
    explanations = {
        "Self-Care": "Self-Care means symptoms look lower-risk right now, but the patient should still watch for changes.",
        "Doctor Visit Recommended": "Doctor Visit Recommended means it is not usually an emergency, but a clinician should check it.",
        "Urgent Care": "Urgent Care means the patient should be seen quickly, usually the same day.",
        "Emergency": "Emergency means there may be danger signs, so it is safest to get medical help immediately.",
    }
    return explanations.get(level, level)


def symptom_clue_summary(result: Any) -> list[str]:
    clues = [str(signal) for signal in result.signals if str(signal).strip()]
    if not clues:
        return ["The app did not find major danger signs from the symptoms shown."]
    return clues


def render_challenge_feedback(choice: str, result: Any, scenario_data: dict[str, Any]) -> None:
    correct = choice == result.risk_level
    if correct:
        st.success(tr("Correct choice"))
    else:
        st.warning(tr("Needs review"))
        st.write(f"**{tr('Your choice')}:** {tr(choice)}")
        if RISK_ORDER.get(choice, 0) < RISK_ORDER.get(result.risk_level, 0):
            st.write(tr("Your answer was too low for the warning signs in this case."))
        else:
            st.write(tr("Your answer was more urgent than the case needs based on the details shown."))
        st.write(tr(care_level_explanation(choice)))
    st.write(f"**{tr('Safest care level')}:** {tr(result.risk_level)}")
    st.write(tr(care_level_explanation(result.risk_level)))
    st.markdown(f"**{tr('How the answer was decided')}**")
    st.write(f"**{tr('Selected symptoms')}:** {', '.join(translate_items(list(scenario_data.get('symptoms', [])), st.session_state.language))}")
    st.markdown(f"**{tr('Clues anyone can notice')}**")
    for clue in translate_items(symptom_clue_summary(result), st.session_state.language):
        st.write(f"- {clue}")
    st.write(f"**{tr('Risk score')}:** {result.score}/100")
    st.write(f"**{tr('Risk score range')}:** {risk_score_range(result.risk_level)}")
    st.write(f"**{tr('Likely pattern')}:** {tr(result.possible_category)}")
    measurements = challenge_measurement_summary(scenario_data)
    if measurements:
        st.markdown(f"**{tr('Optional measurements')}**")
        st.caption(tr("These are extra clues if available. A normal user does not need these devices to choose a safer care level."))
        for measurement in translate_items(measurements, st.session_state.language):
            st.write(f"- {measurement}")
    else:
        st.write(f"**{tr('Important measurements')}:** {tr('No important measurements were provided.')}")
    conditions = list(scenario_data.get("conditions", []))
    if conditions:
        st.write(f"**{tr('Existing conditions')}:** {', '.join(translate_items(conditions, st.session_state.language))}")
    else:
        st.write(f"**{tr('Existing conditions')}:** {tr('No existing conditions were provided.')}")
    st.write(f"{tr('This score falls in the range for')} {tr(result.risk_level)}. {tr('That is why the safest answer is')} {tr(result.risk_level)}.")
    st.markdown(f"**{tr('Key reasons')}**")
    for signal in translate_items(result.signals, st.session_state.language):
        st.write(f"- {signal}")
    st.markdown(f"**{tr('Recommended next step')}**")
    st.write(tr(result.recommendation))


def render_command_bar() -> None:
    ready = h("LifeLine AI workspace is ready")
    move = h("Use Sam or the sidebar to move between tools")
    st.markdown(
        f"""
        <div class="command-bar">
            <div class="command-text"><span class="status-dot"></span>{ready}</div>
            <div class="command-text">{move}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, badge: str) -> None:
    title = h(title)
    subtitle = h(subtitle)
    badge = h(badge)
    st.markdown(
        f"""
        <div class="page-head">
            <div class="clinical-rail"><span></span><span></span><span></span><span></span><span></span><span></span></div>
            <div class="small-title">{badge}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <div class="pulse-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sam() -> None:
    with st.popover("Sam"):
        st.markdown(f'<div class="small-title">{h("Sam assistant")}</div>', unsafe_allow_html=True)
        st.write(tr("Hello, I'm Sam. I'm here to help you."))
        with st.form("sam_chat_form", clear_on_submit=True):
            message = st.text_input(
                tr("Type to Sam"),
                placeholder=tr("Example: explain diabetes simply"),
                key="sam_bubble_input",
            )
            submitted = st.form_submit_button(tr("Ask Sam"), width="stretch")
        if submitted and message.strip():
            with st.spinner(tr("Sam is thinking...")):
                command = answer_message(message.strip())
            st.session_state.sam_last_reply = command.to_json()
        last_reply = st.session_state.get("sam_last_reply")
        if last_reply:
            st.write(translate_text(str(last_reply.get("message", "")), st.session_state.language))
            target_page = last_reply.get("target_page")
            if target_page and st.button(tr(f"Open {target_page}"), key=f"sam_bubble_open_{target_page}", width="stretch"):
                switch_page(str(target_page))


def render_home() -> None:
    cases = list_cases()
    summary = case_queue_summary(cases)
    recent_cases = sorted(cases, key=lambda case: str(case.get("created_at", "")), reverse=True)[:4]
    if not recent_cases:
        recent_cases = [
            {"patient_name": "Patient 001", "risk_level": "Urgent Care", "review_status": "New", "score": 62},
            {"patient_name": "Patient 002", "risk_level": "Doctor Visit Recommended", "review_status": "Reviewed", "score": 38},
            {"patient_name": "Patient 003", "risk_level": "Self-Care", "review_status": "Resolved", "score": 18},
        ]
    rows = "".join(
        f"""
        <tr>
            <td>{h(str(case.get('patient_name') or 'Anonymous'))}</td>
            <td><span class="clinical-chip">{h(compact_risk_label(str(case.get('risk_level', 'Unknown'))))}</span></td>
            <td>{h(str(case.get('review_status') or 'New'))}</td>
            <td>{h(str(case.get('score', 0)))}/100</td>
        </tr>
        """
        for case in recent_cases
    )
    st.markdown(
        f"""
        <div class="dashboard-shell">
            <div class="app-hero">
                <div>
                    <div class="small-title">{h("AI health guidance")}</div>
                    <h1>LifeLine AI</h1>
                    <p>{h("Patient-friendly risk guidance for safer next steps. Check symptoms, review saved cases, and keep doctor-ready summaries in one calm workspace.")}</p>
                </div>
                <div class="safety-badge">{h("Decision support only")}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_command_center_cards(
        [
            ("Saved cases", str(summary["total"]), "Ready for the next check"),
            ("Priority cases", str(summary["high_priority"]), "Emergency and urgent"),
            ("New reviews", str(summary["new_reviews"]), "Waiting for review"),
            ("Last check", "Stable" if not summary["high_priority"] else "Needs attention", "Queue signal"),
        ]
    )
    st.markdown(
        f"""
        <div class="doctor-strip">
            <div class="workspace-panel">
                <div class="small-title">{h("Doctor Dashboard")}</div>
                <h2>{h("Patient cases")}</h2>
                <table class="mini-table">
                    <thead><tr><th>{h("Patient")}</th><th>{h("Risk")}</th><th>{h("Status")}</th><th>{h("Score")}</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
            <div class="workspace-panel">
                <div class="small-title">{h("Health Timeline")}</div>
                <h2>{h("Risk and vitals over time")}</h2>
                <div class="trend-card">
                    <div class="trend-line"></div>
                </div>
                <p class="muted">{h("Saved checks become trend charts for risk score, pain, and optional measurements.")}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    with st.container(key="home_actions"):
        action1, action2, action3 = st.columns(3)
        if action1.button(tr("Start Health Check"), width="stretch"):
            switch_page("Patient Health Checker")
        if action2.button(tr("View Timeline"), width="stretch"):
            switch_page("Health Timeline")
        if action3.button(tr("Open Doctor Dashboard"), width="stretch"):
            switch_page("Doctor Dashboard")


def patient_form() -> dict[str, Any]:
    profile = st.session_state.get("patient_profile", {})
    profile_conditions = list(profile.get("conditions", []))
    known_conditions, custom_conditions = split_known_conditions(profile_conditions)
    st.markdown(f"**{tr('Basic details')}**")
    patient_name = st.text_input(
        tr("Patient name or ID"),
        value=str(profile.get("patient_name", "")),
        placeholder=tr("Example: Patient 001"),
        key="patient_name_input",
    )
    b1, b2 = st.columns(2)
    with b1:
        age = st.number_input(
            tr("Age"),
            min_value=0,
            max_value=120,
            value=int(profile.get("age") if profile.get("age") is not None else 25),
            key="patient_age_input",
        )
    with b2:
        gender_options = ["Prefer not to say", "Female", "Male", "Other"]
        profile_gender = str(profile.get("gender") or "Prefer not to say")
        gender = st.selectbox(
            tr("Gender"),
            gender_options,
            index=gender_options.index(profile_gender) if profile_gender in gender_options else 0,
            format_func=tr,
            key="patient_gender_input",
        )
    st.markdown(f"**{tr('Symptoms')}**")
    selected_symptoms = st.multiselect(
        tr("Choose symptoms from list"),
        SYMPTOM_OPTIONS,
        placeholder=tr("Choose or type symptoms"),
        accept_new_options=True,
        format_func=tr,
        key="patient_symptoms_input",
    )
    typed_symptoms = st.text_area(
        tr("Write any other symptoms"),
        placeholder=tr("Example: ear pain, burning urination, neck stiffness"),
        key="patient_custom_symptoms_input",
    )
    symptoms = unique_items(selected_symptoms + split_free_text_items(typed_symptoms))
    followup_answers, followup_signals = render_adaptive_followups(symptoms)
    symptoms = unique_items(symptoms + followup_signals)
    s1, s2 = st.columns(2)
    with s1:
        duration_days = st.number_input(
            tr("Symptom duration in days"),
            min_value=0,
            max_value=90,
            value=1,
            key="patient_duration_input",
        )
    with s2:
        pain_level = st.slider(tr("Pain level"), 0, 10, 3, key="patient_pain_input")

    st.markdown(f"**{tr('Optional measurements')}**")
    with st.expander(tr("Add temperature, pulse, blood pressure, or oxygen"), expanded=True):
        temperature = st.number_input(
            tr("Temperature in Celsius"),
            min_value=32.0,
            max_value=43.0,
            value=37.0,
            step=0.1,
            key="patient_temperature_input",
        )
        know_heart_rate = st.checkbox(tr("I know my heart rate / pulse"), value=False, key="patient_know_heart_rate_input")
        heart_rate = 0
        if know_heart_rate:
            heart_rate = st.number_input(
                tr("Heart rate / pulse per minute"),
                min_value=0,
                max_value=240,
                value=80,
                key="patient_heart_rate_input",
            )
        know_bp = st.checkbox(tr("I know my blood pressure numbers"), value=False, key="patient_know_bp_input")
        systolic_bp = 0
        diastolic_bp = 0
        if know_bp:
            systolic_bp = st.number_input(
                tr("Blood pressure top number"),
                min_value=0,
                max_value=260,
                value=120,
                key="patient_systolic_input",
            )
            diastolic_bp = st.number_input(
                tr("Blood pressure bottom number"),
                min_value=0,
                max_value=180,
                value=80,
                key="patient_diastolic_input",
            )
            st.caption(tr("If your BP machine shows 120/80, enter 120 as top number and 80 as bottom number."))
        know_oxygen = st.checkbox(tr("I know my oxygen level"), value=False, key="patient_know_oxygen_input")
        oxygen = 0
        if know_oxygen:
            oxygen = st.number_input(
                tr("Oxygen level from pulse oximeter"),
                min_value=0,
                max_value=100,
                value=98,
                key="patient_oxygen_input",
            )
            st.caption(tr("Most people at home will only know this if they have a pulse oximeter."))

    st.markdown(f"**{tr('Existing conditions')}**")
    selected_conditions = st.multiselect(
        tr("Choose existing conditions from list"),
        CONDITION_OPTIONS,
        default=known_conditions,
        placeholder=tr("Choose or type existing conditions"),
        accept_new_options=True,
        format_func=tr,
        key="patient_conditions_input",
    )
    typed_conditions = st.text_area(
        tr("Write any other existing conditions"),
        value=", ".join(custom_conditions),
        placeholder=tr("Example: thyroid problem, anemia, migraine"),
        key="patient_custom_conditions_input",
    )
    conditions = unique_items(selected_conditions + split_free_text_items(typed_conditions))
    medications = st.text_area(
        tr("Current medicines or allergies"),
        value=str(profile.get("medications", "")),
        placeholder=tr("Example: allergic to penicillin, taking asthma inhaler"),
        key="patient_medications_input",
    )
    return {
        "patient_name": patient_name,
        "age": age,
        "gender": gender,
        "symptoms": symptoms,
        "duration_days": duration_days,
        "pain_level": pain_level,
        "temperature": temperature,
        "heart_rate": heart_rate,
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "oxygen": oxygen,
        "conditions": conditions,
        "medications": medications,
        "followup_answers": followup_answers,
    }


def render_previous_check_comparison(comparison: dict[str, Any] | None) -> None:
    if not comparison:
        st.info(tr("No previous saved check found for this patient yet. This result will become the baseline for next time."))
        return

    st.markdown(f"**{tr('Compared with previous check')}**")
    previous_date = str(comparison.get("previous_created_at") or "earlier check")
    st.caption(tr(f"Previous saved check: {previous_date}"))
    c1, c2 = st.columns(2)
    with c1:
        snapshot_card("Previous", f"{compact_risk_label(str(comparison['previous_risk']))} - {comparison['previous_score']:g}/100")
    with c2:
        snapshot_card("Current", f"{compact_risk_label(str(comparison['current_risk']))} - {comparison['current_score']:g}/100")
    for item in comparison.get("highlights", []):
        st.write(f"- {tr(str(item))}")


def render_result_panel(
    result: Any,
    advice: dict[str, Any],
    patient_data: dict[str, Any] | None = None,
    comparison: dict[str, Any] | None = None,
) -> None:
    danger = danger_status(result.risk_level)
    st.markdown(
        f"""
        <div class="danger-banner {danger['class']}">
            <h2>{h(danger['label'])}</h2>
            <p>{h(danger['text'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="section-label">{h("AI recommendation")}</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="summary-grid">
            <div class="summary-item"><span>{h('Care Level')}</span>{h(result.risk_level)}</div>
            <div class="summary-item"><span>{h('Risk Score')}</span>{result.score}/100</div>
            <div class="summary-item"><span>{h('Pattern')}</span>{h(result.possible_category)}</div>
            <div class="summary-item"><span>{h('Timeframe')}</span>{h(advice['timeframe'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander(tr("How this score works")):
        st.write(f"- {tr('0-21')}: {tr('Self-Care')}")
        st.write(f"- {tr('22-44')}: {tr('Doctor Visit Recommended')}")
        st.write(f"- {tr('45-69')}: {tr('Urgent Care')}")
        st.write(f"- {tr('70-100')}: {tr('Emergency')}")
    st.subheader(tr(result.recommendation))
    st.info(tr(advice["risk_summary"]))
    st.write(tr(advice["simple_explanation"]))
    render_care_action_plan(result)
    render_previous_check_comparison(comparison)
    if result.model_prediction:
        st.caption(tr(f"ML model prediction: {result.model_prediction} | Confidence: {result.model_confidence}"))
    followup_answers = list((patient_data or {}).get("followup_answers", []))
    positive_followups = [item for item in followup_answers if item.get("answer") in {"Yes", "Not sure"}]
    if positive_followups:
        st.markdown(f"**{tr('Smart follow-up answers')}**")
        for item in positive_followups:
            st.write(f"- {tr(item['question'])}: {tr(item['answer'])}")
    st.markdown(f"**{tr('Likely health pattern')}**")
    st.write(tr(advice["likely_pattern"]))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{tr('Why the app thinks this')}**")
        for signal in translate_items(result.signals, st.session_state.language):
            st.write(f"- {signal}")
        st.markdown(f"**{tr('What to do now')}**")
        for step in translate_items(advice["care_steps"], st.session_state.language):
            st.write(f"- {step}")
        st.markdown(f"**{tr('Home care support')}**")
        for step in translate_items(advice["home_care"], st.session_state.language):
            st.write(f"- {step}")
    with col2:
        st.markdown(f"**{tr('Precautions')}**")
        for item in translate_items(advice["precautions"], st.session_state.language):
            st.write(f"- {item}")
        st.markdown(f"**{tr('What to avoid')}**")
        for item in translate_items(advice["avoid"], st.session_state.language):
            st.write(f"- {item}")
        st.markdown(f"**{tr('Prevention tips')}**")
        for item in translate_items(advice["prevention"], st.session_state.language):
            st.write(f"- {item}")
        st.markdown(f"**{tr('Red Flags')}**")
        for item in translate_items(advice["red_flags"], st.session_state.language):
            st.write(f"- {item}")
    st.markdown(f"**{tr('Questions to ask a doctor')}**")
    for item in translate_items(advice["doctor_questions"], st.session_state.language):
        st.write(f"- {item}")
    st.warning(tr(advice["disclaimer"]))


def render_followup_and_summary(patient_data: dict[str, Any], result: Any, advice: dict[str, Any]) -> None:
    st.write("")
    st.markdown(f'<div class="section-label">{h("Follow-up and doctor summary")}</div>', unsafe_allow_html=True)
    follow_col, summary_col = st.columns([1, 1], gap="large")
    with follow_col:
        st.markdown(f"**{tr('Follow-up checker')}**")
        st.caption(tr("Use this after some time has passed to check if the situation is improving or needs faster care."))
        status = st.radio(
            tr("Compared with the first check, how is the patient now?"),
            ["Better", "Same", "Worse"],
            horizontal=True,
            format_func=tr,
            key="followup_status",
        )
        hours_since_check = st.number_input(
            tr("Hours since the first check"),
            min_value=1,
            max_value=168,
            value=24,
            step=1,
            key="followup_hours",
        )
        new_notes = st.text_area(
            tr("New symptoms or changes"),
            placeholder=tr("Example: fever reduced, chest pain started, breathing worse, vomiting stopped"),
            key="followup_notes",
        )
        if st.button(tr("Check follow-up"), width="stretch"):
            st.session_state.followup_result = evaluate_follow_up(result, status, new_notes, int(hours_since_check))
        followup = st.session_state.get("followup_result")
        if followup:
            st.info(tr(followup["level"]))
            st.write(tr(followup["message"]))
            for step in translate_items(followup["next_steps"], st.session_state.language):
                st.write(f"- {step}")
            st.caption(tr(followup["safety_note"]))
    with summary_col:
        st.markdown(f"**{tr('Doctor summary')}**")
        summary = build_doctor_summary(patient_data, result, advice)
        translated_summary = translate_text(summary, st.session_state.language)
        st.text_area(
            tr("Show this to a doctor"),
            value=translated_summary,
            height=220,
            key="doctor_summary_text",
        )
        st.download_button(
            tr("Download Doctor Summary"),
            data=summary,
            file_name="lifeline_ai_doctor_summary.txt",
            mime="text/plain",
            width="stretch",
        )
        st.caption(tr("This is written to make a doctor visit faster and clearer."))


def render_checker() -> None:
    page_header(
        "Patient Health Checker",
        "Enter symptoms and the details you know. Heart rate, blood pressure, and oxygen are optional for home users.",
        "Prediction workspace",
    )
    form_col, result_col = st.columns([1.05, .95], gap="large")
    with form_col:
        st.markdown(f'<div class="section-label">{h("Patient intake")}</div>', unsafe_allow_html=True)
        data = patient_form()
        p1, p2 = st.columns(2)
        if p1.button(tr("Save patient profile"), width="stretch"):
            st.session_state.patient_profile = {
                "patient_name": data["patient_name"],
                "age": int(data["age"] or 0),
                "gender": data["gender"],
                "conditions": data["conditions"],
                "medications": data["medications"],
            }
            st.success(tr("Patient profile saved for this session."))
        if p2.button(tr("Clear profile"), width="stretch"):
            st.session_state.patient_profile = {}
            clear_profile_form()
            st.success(tr("Patient profile cleared."))
            st.rerun()
        save_to_dashboard = st.checkbox(tr("Save this case to Doctor Dashboard"), value=True)
        if st.button(tr("Analyze Health"), type="primary", width="stretch"):
            if not data["symptoms"]:
                st.error(tr("Please choose at least one symptom."))
            else:
                result = analyze_patient(data, use_ml=False)
                advice = build_recommendations(result, enhance=False)
                previous_case = latest_previous_case(data)
                st.session_state.checker_result = {
                    "result": result,
                    "advice": advice,
                    "saved": bool(save_to_dashboard),
                    "comparison": build_previous_check_comparison(data, result, previous_case),
                }
                st.session_state.checker_patient_data = data
                st.session_state.pop("followup_result", None)
                if save_to_dashboard:
                    save_case(data, result)
                st.rerun()
    with result_col:
        st.markdown(f'<div class="section-label">{h("Live result")}</div>', unsafe_allow_html=True)
        stored = st.session_state.get("checker_result")
        if stored:
            if stored.get("saved"):
                st.success(tr("Case saved to Doctor Dashboard."))
            patient_data = st.session_state.get("checker_patient_data") or {}
            render_result_panel(stored["result"], stored["advice"], patient_data, stored.get("comparison"))
            pdf_bytes = generate_health_report_pdf(patient_data, stored["result"], stored["advice"])
            st.download_button(
                tr("Download Health Report PDF"),
                data=pdf_bytes,
                file_name="lifeline_ai_health_report.pdf",
                mime="application/pdf",
                width="stretch",
            )
        else:
            st.markdown(
                f"""
                <div class="empty-result">
                    <b>{h("No analysis yet.")}</b><br>
                    {h("Fill the patient details on the left and click Analyze Health.")}
                    {h("The danger level will appear here as green, yellow, or red.")}
                </div>
                """,
                unsafe_allow_html=True,
            )
    stored = st.session_state.get("checker_result")
    patient_data = st.session_state.get("checker_patient_data") or {}
    if stored and patient_data:
        render_followup_and_summary(patient_data, stored["result"], stored["advice"])
    st.write("")


def render_timeline() -> None:
    page_header(
        "Health Timeline",
        "See how a patient's symptoms, risk level, and recommendations changed across saved checks.",
        "Patient history",
    )
    cases = list_cases()
    if not cases:
        st.info(tr("No saved cases yet. Use Patient Health Checker and save a case first."))
        return

    patient_names = sorted({str(case.get("patient_name") or "Anonymous") for case in cases})
    default_name = st.session_state.get("patient_profile", {}).get("patient_name")
    selected_index = patient_names.index(default_name) if default_name in patient_names else 0
    selected_patient = st.selectbox(tr("Choose patient"), patient_names, index=selected_index)
    patient_cases = [case for case in cases if str(case.get("patient_name") or "Anonymous") == selected_patient]
    patient_cases.sort(key=lambda case: str(case.get("created_at", "")))
    remove_col, action_col = st.columns([0.65, 0.35])
    confirm_patient_reset = remove_col.checkbox(
        tr(f"Remove all saved timeline entries for {selected_patient}"),
        key=f"confirm_timeline_reset_{selected_patient}",
    )
    if action_col.button(
        tr("Reset selected patient"),
        disabled=not confirm_patient_reset,
        width="stretch",
    ):
        delete_patient_cases(selected_patient)
        profile_name = st.session_state.get("patient_profile", {}).get("patient_name")
        if profile_name == selected_patient:
            st.session_state.patient_profile = {}
        st.success(tr("Selected patient was removed from the timeline."))
        st.rerun()

    latest = patient_cases[-1]
    raw_latest = parse_case_raw_data(latest.get("raw_data"))
    st.markdown(f'<div class="section-label">{h("Patient profile snapshot")}</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        snapshot_card("Saved checks", str(len(patient_cases)))
    with c2:
        snapshot_card("Latest risk", compact_risk_label(str(latest.get("risk_level", "Unknown"))))
    with c3:
        snapshot_card("Latest score", f"{latest.get('score', 0)}/100")
    with c4:
        snapshot_card("Age", str(latest.get("age") or raw_latest.get("age") or "N/A"))

    st.markdown(f"**{tr('Known conditions')}**")
    st.write(", ".join(raw_latest.get("conditions", [])) or tr("Not provided"))
    st.markdown(f"**{tr('Medicines / allergies')}**")
    st.write(raw_latest.get("medications") or tr("Not provided"))

    st.write("")
    st.markdown(f'<div class="section-label">{h("Trend charts")}</div>', unsafe_allow_html=True)
    trend_df = build_timeline_trend_frame(patient_cases)
    if len(trend_df) > 1:
        trend_col1, trend_col2 = st.columns(2)
        with trend_col1:
            st.markdown(f"**{tr('Risk and pain over time')}**")
            risk_pain = trend_df[["Risk score", "Pain level"]].dropna(axis=1, how="all")
            if not risk_pain.empty and risk_pain.shape[1]:
                render_zero_based_line_chart(risk_pain)
            else:
                st.info(tr("No risk or pain values were saved for trend charts yet."))
        vitals = trend_df[["Temperature", "Oxygen", "Pulse", "Systolic BP", "Diastolic BP"]].dropna(axis=1, how="all")
        with trend_col2:
            st.markdown(f"**{tr('Measurements over time')}**")
            if not vitals.empty and vitals.shape[1]:
                render_zero_based_line_chart(vitals)
            else:
                st.info(tr("No optional measurements were saved for trend charts yet."))
    else:
        st.info(tr("Save at least two checks for this patient to see trend charts."))

    st.write("")
    st.markdown(f'<div class="section-label">{h("Timeline")}</div>', unsafe_allow_html=True)
    for index, case in enumerate(patient_cases, start=1):
        raw = parse_case_raw_data(case.get("raw_data"))
        symptoms = case.get("symptoms") or ", ".join(raw.get("symptoms", [])) or "Not provided"
        duration = raw.get("duration_days", "N/A")
        pain = raw.get("pain_level", "N/A")
        vitals = []
        if raw.get("temperature"):
            vitals.append(f"{raw['temperature']} C")
        if raw.get("oxygen"):
            vitals.append(f"O2 {raw['oxygen']}%")
        if raw.get("heart_rate"):
            vitals.append(f"pulse {raw['heart_rate']}")
        if raw.get("systolic_bp") and raw.get("diastolic_bp"):
            vitals.append(f"BP {raw['systolic_bp']}/{raw['diastolic_bp']}")
        risk_label = tr(compact_risk_label(str(case.get("risk_level", "Unknown"))))
        with st.expander(f"{index}. {case.get('created_at', '')} - {risk_label} - {case.get('score', 0)}/100", expanded=index == len(patient_cases)):
            st.write(f"**{tr('Symptoms')}:** {symptoms}")
            st.write(f"**{tr('Duration')}:** {duration} {tr('day(s)')} | **{tr('Pain')}:** {pain}/10")
            st.write(f"**{tr('Measurements')}:** {', '.join(vitals) if vitals else tr('Not provided')}")
            st.write(f"**{tr('Likely pattern')}:** {tr(str(case.get('category', 'General Health')))}")
            st.write(f"**{tr('Recommendation')}:** {tr(str(case.get('recommendation', '')))}")
            followup_answers = list(raw.get("followup_answers", []))
            if followup_answers:
                st.write(f"**{tr('Smart follow-up answers')}:**")
                for item in followup_answers:
                    st.write(f"- {tr(str(item.get('question', '')))}: {tr(str(item.get('answer', '')))}")

    st.write("")
    if st.button(tr("Use latest profile in Health Checker"), width="stretch"):
        profile = {
            "patient_name": selected_patient,
            "age": int(latest.get("age") if latest.get("age") is not None else raw_latest.get("age") or 0),
            "gender": raw_latest.get("gender", "Prefer not to say"),
            "conditions": raw_latest.get("conditions", []),
            "medications": raw_latest.get("medications", ""),
        }
        st.session_state.patient_profile = profile
        load_profile_into_form(profile)
        switch_page("Patient Health Checker")


def render_qa() -> None:
    page_header(
        "Health & Medicine Q&A",
        "Ask about a disease, symptom, or medicine in simple words. Answers stay patient-friendly and include precautions, safe-use tips, and warning signs.",
        "Health education",
    )
    render_quick_jumps("qa_top_jump", exclude="Disease Q&A Assistant")
    st.write("")
    main, helper = st.columns([1.7, .8], gap="large")
    with main:
        st.markdown(f'<div class="section-label">{h("Ask a health question")}</div>', unsafe_allow_html=True)
        pending_question = st.session_state.pop("pending_qa_question", None)
        if pending_question:
            st.session_state.qa_question = pending_question
        st.session_state.setdefault("qa_question", "")
        question = st.text_input(
            tr("Ask in simple words"),
            key="qa_question",
            placeholder=tr("Example: How are antibiotics made?"),
        )
        examples = st.columns(4)
        example_questions = [
            "What is paracetamol used for?",
            "Can I take antibiotics for fever?",
            "Side effects of ibuprofen",
            "How are antibiotics made?",
        ]
        for idx, example in enumerate(example_questions):
            if examples[idx].button(tr(example), key=f"qa_example_{idx}"):
                st.session_state.pending_qa_question = example
                st.rerun()
        if question:
            answer = translate_answer(answer_question(question), st.session_state.language)
            st.subheader(answer["title"])
            st.write(answer["meaning"])
            is_medicine = answer.get("kind") == "medicine"
            is_targeted = answer.get("kind") == "general" or answer.get("intent") not in (None, "overview")
            if is_medicine and answer.get("safety_note"):
                st.info(tr(answer["safety_note"]))
            sections = [
                ("Key points" if is_medicine or is_targeted else "Common symptoms", answer["symptoms"]),
                ("Precautions", answer["precautions"]),
                ("Safe use tips" if is_medicine else "Helpful steps" if is_targeted else "Prevention", answer["prevention"]),
                ("What you can do now", answer.get("what_to_do_now", [])),
                ("What to avoid", answer.get("avoid", [])),
                ("Get medical help if" if is_medicine or is_targeted else "Emergency signs", answer["emergency"]),
                ("Questions to ask a doctor or pharmacist" if is_medicine else "Questions to ask a doctor", answer.get("doctor_questions", [])),
            ]
            for title, items in sections:
                if not items:
                    continue
                st.markdown(f"**{translate_text(title, st.session_state.language)}**")
                for item in items:
                    st.write(f"- {item}")
            doctor_label = "Ask a doctor or pharmacist" if is_medicine else "When to visit a doctor"
            st.markdown(f"**{translate_text(doctor_label, st.session_state.language)}**")
            st.write(answer["doctor"])
            if is_medicine:
                st.warning(tr("Do not start, stop, mix, or change medicine doses without asking a doctor or pharmacist."))
            else:
                st.warning(tr("This is general health education only. A doctor must diagnose and treat medical conditions."))
            if answer.get("source"):
                st.caption(f"{tr('Source')}: {answer['source']}")
            st.markdown(f'<div class="section-label">{h("Next step")}</div>', unsafe_allow_html=True)
            n1, n2, n3 = st.columns(3)
            if n1.button(tr("Check my symptoms"), key="qa_next_checker", width="stretch"):
                switch_page("Patient Health Checker")
            if n2.button(tr("View saved cases"), key="qa_next_dashboard", width="stretch"):
                switch_page("Doctor Dashboard")
            if n3.button(tr("Try a scenario"), key="qa_next_challenge", width="stretch"):
                switch_page("Scenario Challenge")
    with helper:
        st.empty()


def render_medication_safety() -> None:
    page_header(
        "Medication Safety Checker",
        "Enter a medicine and basic safety details. The app gives simple warnings, what to avoid, and questions to ask a pharmacist or doctor.",
        "Medicine safety",
    )
    render_quick_jumps("med_top_jump", exclude="Medication Safety Checker")
    st.write("")
    form, result_area = st.columns([1.0, 1.0], gap="large")
    with form:
        st.markdown(f'<div class="section-label">{h("Medicine details")}</div>', unsafe_allow_html=True)
        medicine_name = st.text_input(tr("Medicine name"), placeholder=tr("Example: ibuprofen, paracetamol, insulin"))
        m1, m2 = st.columns(2)
        with m1:
            age = st.number_input(tr("Age"), min_value=0, max_value=120, value=25, key="med_age")
        with m2:
            pregnant = st.checkbox(tr("Pregnant or possibly pregnant"), value=False)
        conditions = st.multiselect(tr("Existing conditions"), CONDITION_OPTIONS, format_func=tr, key="med_conditions")
        allergies = st.text_area(tr("Allergies"), placeholder=tr("Example: penicillin allergy, aspirin allergy"))
        current_medicines = st.text_area(tr("Other medicines currently taken"), placeholder=tr("Example: blood thinner, diabetes medicine, asthma inhaler"))
        run_check = st.button(tr("Check Medicine Safety"), type="primary", width="stretch")
    with result_area:
        st.markdown(f'<div class="section-label">{h("Safety result")}</div>', unsafe_allow_html=True)
        if run_check:
            if not medicine_name.strip():
                st.error(tr("Please enter a medicine name."))
            else:
                med_result = analyze_medication_safety(
                    medicine_name=medicine_name,
                    age=int(age),
                    allergies=allergies,
                    conditions=conditions,
                    current_medicines=current_medicines,
                    pregnant=pregnant,
                )
                st.subheader(tr(med_result.level))
                st.write(tr(med_result.summary))
                sections = [
                    ("Key points", med_result.key_points),
                    ("Caution flags", med_result.caution_flags),
                    ("What you can do now", med_result.what_to_do),
                    ("Get medical help if", med_result.emergency_signs),
                    ("Questions to ask a doctor or pharmacist", med_result.questions),
                ]
                for title, items in sections:
                    st.markdown(f"**{tr(title)}**")
                    for item in translate_items(items, st.session_state.language):
                        st.write(f"- {item}")
                st.warning(tr("This tool does not prescribe medicine or dosage. Ask a doctor or pharmacist before changing medicines."))
        else:
            st.markdown(
                f"""
                <div class="empty-result">
                    <b>{h("No medicine checked yet.")}</b><br>
                    {h("Enter a medicine name and safety details, then click Check Medicine Safety.")}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_dashboard() -> None:
    page_header(
        "Doctor / Hospital Dashboard",
        "Review saved patient cases, sorted by urgency so serious cases are easier to notice first.",
        "Clinical queue",
    )
    reset_col, _ = st.columns([0.35, 0.65])
    with reset_col:
        confirm_reset = st.checkbox(tr("I understand this will remove saved patient cases"))
        if st.button(tr("Reset patient data"), disabled=not confirm_reset, width="stretch"):
            clear_cases()
            st.session_state.checker_result = None
            st.session_state.checker_patient_data = None
            st.success(tr("Saved patient cases were removed."))
            st.rerun()
    cases = list_cases()
    db_error = database_error_message()
    db_label = database_backend()
    st.caption(f"{tr('Database')}: {db_label}")
    if db_error:
        st.caption(tr(db_error))
        st.caption(tr("To use Supabase, add SUPABASE_URL and SUPABASE_ANON_KEY, run supabase_schema.sql in Supabase SQL Editor, and reboot."))
    if not cases:
        st.info(tr("No saved patient cases yet. Use the Health Checker and save a case."))
        return

    df = pd.DataFrame(cases)
    if "review_status" not in df.columns:
        df["review_status"] = "New"
    if "doctor_notes" not in df.columns:
        df["doctor_notes"] = ""
    df["review_status"] = df["review_status"].fillna("New").replace("", "New")
    df["doctor_notes"] = df["doctor_notes"].fillna("")

    filter_col1, filter_col2 = st.columns(2)
    selected = filter_col1.selectbox(tr("Filter by risk"), ["All", "Self-Care", "Doctor Visit Recommended", "Urgent Care", "Emergency"], format_func=tr)
    status_filter = filter_col2.selectbox(tr("Filter by review status"), ["All", *REVIEW_STATUSES], format_func=tr)
    if selected != "All":
        df = df[df["risk_level"] == selected]
    if status_filter != "All":
        df = df[df["review_status"] == status_filter]
    df["urgency_rank"] = df["risk_level"].map(RISK_ORDER)
    df = df.sort_values(["urgency_rank", "score"], ascending=[False, False])

    st.markdown(f'<div class="section-label">{h("Queue summary")}</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(tr("Total cases"), len(df))
    c2.metric(tr("Emergency"), int((df["risk_level"] == "Emergency").sum()))
    c3.metric(tr("Urgent"), int((df["risk_level"] == "Urgent Care").sum()))
    c4.metric(tr("Doctor visits"), int((df["risk_level"] == "Doctor Visit Recommended").sum()))
    st.markdown(f'<div class="section-label">{h("Queue insights")}</div>', unsafe_allow_html=True)
    render_queue_insights(df.to_dict("records"))

    st.markdown(f'<div class="section-label">{h("Patient cases")}</div>', unsafe_allow_html=True)
    st.dataframe(
        df[["created_at", "patient_name", "age", "symptoms", "category", "risk_level", "review_status", "recommendation", "score"]],
        width="stretch",
        hide_index=True,
    )
    st.write("")
    st.markdown(f'<div class="section-label">{h("Review selected case")}</div>', unsafe_allow_html=True)
    if df.empty:
        st.info(tr("No cases match the selected filters."))
        return

    review_cases = df.to_dict("records")
    selected_case_id = st.selectbox(
        tr("Choose case to review"),
        [case["id"] for case in review_cases],
        format_func=lambda case_id: next(
            (
                f"{case.get('created_at', '')} - {case.get('patient_name', 'Anonymous')} - {case.get('risk_level', '')}"
                for case in review_cases
                if case.get("id") == case_id
            ),
            str(case_id),
        ),
    )
    selected_case = next(case for case in review_cases if case.get("id") == selected_case_id)
    status_value = str(selected_case.get("review_status") or "New")
    if status_value not in REVIEW_STATUSES:
        status_value = "New"
    with st.form(f"case_review_form_{selected_case_id}"):
        new_status = st.selectbox(
            tr("Case status"),
            REVIEW_STATUSES,
            index=REVIEW_STATUSES.index(status_value),
            format_func=tr,
        )
        new_notes = st.text_area(
            tr("Doctor case notes"),
            value=str(selected_case.get("doctor_notes") or ""),
            placeholder=tr("Example: Called patient, advised clinic visit, reviewed allergy history."),
            height=140,
        )
        if st.form_submit_button(tr("Save review"), width="stretch"):
            saved = update_case_review(selected_case_id, new_status, new_notes)
            if saved:
                st.success(tr("Case review saved."))
                st.rerun()
            else:
                st.error(tr("Case review could not be saved. Apply the updated Supabase schema first."))

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown(f'<div class="section-label">{h("Risk levels")}</div>', unsafe_allow_html=True)
        render_count_bar_chart(df["risk_level"].value_counts(), "Risk level")
    with chart_col2:
        st.markdown(f'<div class="section-label">{h("Categories")}</div>', unsafe_allow_html=True)
        render_count_bar_chart(df["category"].value_counts(), "Category")


def render_challenge() -> None:
    page_header(
        "Scenario Challenge",
        "Practice choosing the safest care level for fictional patient cases and compare your choice with LifeLine AI.",
        "Game mode",
    )
    try:
        scenario_index = int(st.session_state.scenario_index)
    except (TypeError, ValueError):
        scenario_index = 0
        st.session_state.scenario_index = 0
    index = scenario_index % len(SCENARIOS)
    scenario = SCENARIOS[index]
    option_key = f"challenge_options_{index}"
    if option_key not in st.session_state:
        options = ["Self-Care", "Doctor Visit Recommended", "Urgent Care", "Emergency"]
        random.Random(index + 17).shuffle(options)
        st.session_state[option_key] = options

    st.markdown(f'<div class="section-label">{h("Current case")}</div>', unsafe_allow_html=True)
    st.subheader(tr("Patient Case"))
    st.write(tr(scenario["case"]))
    choice = st.radio(
        tr("What should this patient do?"),
        st.session_state[option_key],
        format_func=tr,
        key=f"challenge_choice_{index}",
    )
    if st.button(tr("Check My Answer")):
        result = fast_analyze_patient(scenario["data"])
        if choice == result.risk_level:
            st.session_state.score += 10
        render_challenge_feedback(choice, result, scenario["data"])
    if st.button(tr("Next Scenario")):
        st.session_state.scenario_index = random.randint(0, len(SCENARIOS) - 1)
        st.rerun()
    st.metric(tr("Score"), st.session_state.score)


def render_safety_videos() -> None:
    page_header(
        "Safety Videos",
        "Quick patient-friendly learning about prevention, precautions, medicine safety, and disease safety.",
        "Safety learning",
    )
    video_col, guide_col = st.columns([1.2, .8], gap="large")
    with video_col:
        st.markdown(f'<div class="section-label">{h("Featured video")}</div>', unsafe_allow_html=True)
        if st.session_state.offline_mode:
            st.info(tr("Offline mode is on, so online videos are hidden. Use the safety checklist on this page."))
        else:
            st.video("https://www.youtube.com/watch?v=Y6DPDC_Mf90")
            st.caption(tr("Video: What is Public Health? It explains public health, prevention, and how health systems protect communities."))
    with guide_col:
        st.markdown(f'<div class="section-label">{h("Core safety rules")}</div>', unsafe_allow_html=True)
        safety_sections = [
            ("Prevention", ["Wash hands often.", "Keep vaccines up to date.", "Sleep well, drink water, and avoid smoking.", "Stay away from sick people when possible."]),
            ("Precautions", ["Wear a mask if coughing or around high-risk people.", "Do not share towels, bottles, or utensils when sick.", "Clean frequently touched surfaces.", "Watch symptoms for worsening."]),
            ("Medicine safety", ["Do not mix medicines without checking.", "Never take antibiotics for viral fever unless prescribed.", "Check allergies before taking a medicine.", "Follow the label or doctor dose only."]),
            ("Disease safety", ["Know red flags: chest pain, trouble breathing, confusion, fainting, stroke signs.", "Seek care faster for babies, elderly people, pregnancy, or weak immunity.", "Use the Health Checker for symptom guidance.", "Ask a doctor if symptoms continue or worsen."]),
        ]
        for title, items in safety_sections:
            st.markdown(f"**{tr(title)}**")
            for item in translate_items(items, st.session_state.language):
                st.write(f"- {item}")
        st.warning(tr("Videos and tips are for education only. They do not replace medical care."))


def main() -> None:
    inject_css()
    init_state()
    sidebar()

    if st.session_state.page == "Home":
        render_home()
    elif st.session_state.page == "Patient Health Checker":
        render_checker()
    elif st.session_state.page == "Health Timeline":
        render_timeline()
    elif st.session_state.page == "Disease Q&A Assistant":
        render_qa()
    elif st.session_state.page == "Medication Safety Checker":
        render_medication_safety()
    elif st.session_state.page == "Doctor Dashboard":
        render_dashboard()
    elif st.session_state.page == "Scenario Challenge":
        render_challenge()
    elif st.session_state.page == "Safety Videos":
        render_safety_videos()
    render_sam()


if __name__ == "__main__":
    main()
