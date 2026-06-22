from __future__ import annotations

import random
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from backend.database import list_cases, save_case
from backend.disease_qa import answer_question
from backend.medication_safety import analyze_medication_safety
from backend.recommender import build_recommendations
from backend.report import generate_health_report_pdf
from backend.sam import route_message
from backend.translator import translate_answer, translate_items, translate_text
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

PAGES = [
    "Home",
    "Patient Health Checker",
    "Disease Q&A Assistant",
    "Medication Safety Checker",
    "Doctor Dashboard",
    "Scenario Challenge",
]

LANGUAGE_OPTIONS = [
    "\U0001f1fa\U0001f1f8 English", "\U0001f1ee\U0001f1f3 Hindi", "\U0001f1f7\U0001f1fa Russian", "\U0001f1e9\U0001f1ea German", "\U0001f1eb\U0001f1f7 French",
    "\U0001f1ea\U0001f1f8 Spanish", "\U0001f1ee\U0001f1ea Gaelic", "\U0001f1ee\U0001f1f3 Sanskrit", "\U0001f1ee\U0001f1f3 Marathi", "\U0001f1ee\U0001f1f3 Kannada",
    "\U0001f1ee\U0001f1f3 Tamil", "\U0001f1ee\U0001f1f3 Malayalam", "\U0001f1ee\U0001f1f3 Telugu", "\U0001f1ee\U0001f1f3 Gujarati", "\U0001f1ee\U0001f1f3 Bhojpuri",
    "\U0001f1e8\U0001f1f3 Mandarin", "\U0001f1f9\U0001f1ed Thai", "\U0001f1ef\U0001f1f5 Japanese", "\U0001f1f3\U0001f1f4 Norwegian", "\U0001f1f8\U0001f1ea Swedish",
    "\U0001f1eb\U0001f1ee Finnish", "\U0001f1f5\U0001f1f9 Portuguese", "\U0001f1f7\U0001f1f4 Romanian", "\U0001f1ee\U0001f1f9 Italian", "\U0001f1ee\U0001f1f8 Icelandic",
    "\U0001f1f3\U0001f1f1 Dutch", "\U0001f1f2\U0001f1fe Malay", "\U0001f1ee\U0001f1f1 Hebrew", "\U0001f1f8\U0001f1e6 Arabic",
]


def tr(text: str) -> str:
    return translate_text(text, st.session_state.language)


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
            --bg: #080c0f;
            --bg-2: #0b1115;
            --panel: #10171c;
            --panel-2: #141d23;
            --panel-3: #18242b;
            --line: #233139;
            --line-soft: rgba(120, 143, 150, .18);
            --text: #edf4f1;
            --muted: #99aaa5;
            --teal: #41d8c3;
            --teal-dim: rgba(65, 216, 195, .12);
            --amber: #f3b84c;
            --red: #ff6c6c;
        }
        .stApp {
            background:
                radial-gradient(circle at 18% 0%, rgba(65, 216, 195, .08), transparent 26%),
                linear-gradient(180deg, #090e11 0%, var(--bg) 45%, #070b0d 100%);
            color: var(--text);
            font-family: "Noto Sans Devanagari", "Mangal", "Nirmala UI", "Segoe UI", Arial, sans-serif;
        }
        header[data-testid="stHeader"] { background: transparent; }
        #MainMenu, footer { visibility: hidden; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d1418 0%, #090e11 100%);
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] * { color: var(--text); }
        [data-testid="stSidebar"] [role="radiogroup"] label {
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 8px 10px;
            margin: 4px 0;
            background: rgba(255, 255, 255, .015);
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            border-color: rgba(65, 216, 195, .28);
            background: rgba(65, 216, 195, .06);
        }
        .block-container { padding-top: 1.05rem; padding-bottom: 2rem; max-width: 1380px; }
        h1, h2, h3 { letter-spacing: 0; color: var(--text); }
        h1 { font-size: 2.35rem; line-height: 1.05; margin-bottom: .35rem; }
        h2 { font-size: 1.35rem; }
        h3 { font-size: 1.05rem; }
        p, li, label, .stMarkdown { color: var(--text); }
        .stCaptionContainer, [data-testid="stCaptionContainer"] { color: var(--muted); }
        .muted { color: var(--muted); }
        .command-bar {
            border: 1px solid var(--line);
            background: rgba(16, 23, 28, .84);
            border-radius: 8px;
            padding: 12px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            box-shadow: 0 16px 44px rgba(0, 0, 0, .18);
            margin-bottom: 18px;
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
            background: var(--teal);
            box-shadow: 0 0 18px rgba(65, 216, 195, .8);
            margin-right: 8px;
        }
        .page-head {
            border: 1px solid var(--line);
            background: linear-gradient(135deg, rgba(20, 29, 35, .95), rgba(13, 20, 24, .96));
            border-radius: 8px;
            padding: 20px 22px;
            margin-bottom: 18px;
        }
        .page-head p { margin-bottom: 0; color: var(--muted); max-width: 860px; }
        .hero {
            border: 1px solid var(--line);
            background:
                linear-gradient(135deg, rgba(19, 29, 35, .96) 0%, rgba(12, 20, 24, .98) 64%, rgba(10, 17, 20, .96) 100%);
            border-radius: 8px;
            padding: 32px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.035), 0 18px 70px rgba(0,0,0,.22);
        }
        .panel {
            border: 1px solid var(--line);
            background: linear-gradient(180deg, rgba(16, 23, 28, .98), rgba(12, 18, 22, .98));
            border-radius: 8px;
            padding: 20px;
            min-height: 100%;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.03);
        }
        .metric-card {
            border: 1px solid var(--line);
            background: linear-gradient(180deg, var(--panel-2), #10181d);
            border-radius: 8px;
            padding: 16px 16px 15px;
            min-height: 112px;
        }
        .metric-card b {
            display: block;
            margin-bottom: 8px;
            color: var(--text);
        }
        .metric-card .token {
            color: var(--teal);
            font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
            font-size: .82rem;
        }
        .risk {
            display: inline-block;
            border: 1px solid rgba(70, 214, 191, .45);
            color: #06100e;
            background: var(--teal);
            border-radius: 999px;
            padding: 8px 12px;
            font-weight: 800;
            margin: 6px 0 12px 0;
        }
        .danger-banner {
            border-radius: 8px;
            padding: 16px;
            margin: 0 0 16px 0;
            border: 1px solid var(--line);
        }
        .danger-banner h2 {
            margin: 0 0 4px 0;
            font-size: 1.35rem;
        }
        .danger-banner p { margin: 0; color: rgba(255,255,255,.82); }
        .danger-low {
            background: linear-gradient(135deg, rgba(41, 190, 125, .24), rgba(16, 23, 28, .96));
            border-color: rgba(41, 190, 125, .65);
        }
        .danger-moderate {
            background: linear-gradient(135deg, rgba(243, 184, 76, .26), rgba(16, 23, 28, .96));
            border-color: rgba(243, 184, 76, .7);
        }
        .danger-high {
            background: linear-gradient(135deg, rgba(255, 108, 108, .28), rgba(16, 23, 28, .96));
            border-color: rgba(255, 108, 108, .72);
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-bottom: 14px;
        }
        .summary-item {
            background: rgba(255,255,255,.025);
            border: 1px solid var(--line-soft);
            border-radius: 8px;
            padding: 10px;
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
            border: 1px dashed rgba(153, 170, 165, .35);
            background: rgba(255,255,255,.018);
            border-radius: 8px;
            padding: 22px;
            color: var(--muted);
        }
        .soft-badge {
            display: inline-block;
            border: 1px solid rgba(65, 216, 195, .28);
            background: var(--teal-dim);
            color: #bffdf2;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: .82rem;
            font-weight: 700;
            margin-right: 8px;
        }
        .sam-box {
            border: 1px solid rgba(70, 214, 191, .45);
            background:
                linear-gradient(180deg, rgba(16, 33, 34, .98), rgba(12, 23, 25, .98));
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 0 0 1px rgba(70, 214, 191, .06), 0 20px 60px rgba(0,0,0,.2);
            position: sticky;
            top: 18px;
        }
        div[data-testid="stPopover"] {
            position: fixed;
            right: 24px;
            bottom: 24px;
            z-index: 9999;
            width: 72px !important;
            min-width: 72px !important;
            max-width: 72px !important;
        }
        div[data-testid="stPopover"] > button {
            width: 72px;
            height: 72px;
            min-width: 72px;
            border-radius: 999px;
            border: 1px solid rgba(65, 216, 195, .75);
            background: linear-gradient(180deg, #1a4b43, #102b27);
            box-shadow: 0 18px 60px rgba(0,0,0,.45), 0 0 34px rgba(65, 216, 195, .25);
            color: #eafffb;
            font-weight: 900;
        }
        div[data-testid="stPopover"] > button:hover {
            border-color: var(--teal);
            transform: translateY(-1px);
            box-shadow: 0 22px 70px rgba(0,0,0,.5), 0 0 44px rgba(65, 216, 195, .35);
        }
        .small-title {
            color: var(--teal);
            text-transform: uppercase;
            font-size: .78rem;
            letter-spacing: .08em;
            font-weight: 800;
        }
        .section-label {
            color: var(--teal);
            font-size: .78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .08em;
            margin: 4px 0 10px;
        }
        .stButton>button {
            border-radius: 6px;
            border: 1px solid rgba(70, 214, 191, .45);
            background: linear-gradient(180deg, #15302c, #102420);
            color: var(--text);
            font-weight: 700;
            min-height: 2.45rem;
        }
        .stButton>button:hover {
            border-color: var(--teal);
            color: #dffff8;
            background: #173c36;
        }
        .stTextInput input, .stNumberInput input, .stTextArea textarea {
            background: #0d1418;
            color: var(--text);
            border: 1px solid var(--line);
            border-radius: 7px;
        }
        div[data-baseweb="select"] > div {
            background: #0d1418;
            border-color: var(--line);
            border-radius: 7px;
        }
        [data-testid="stMultiSelect"] div {
            color: var(--text);
        }
        [data-testid="stMetric"] {
            border: 1px solid var(--line);
            background: var(--panel);
            border-radius: 8px;
            padding: 14px;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
        }
        .stAlert {
            border-radius: 8px;
        }
        code {
            color: #d7fff5;
            background: #0f171b;
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: 2px 5px;
        }
        hr { border-color: var(--line-soft); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    st.session_state.setdefault("page", "Home")
    if st.session_state.page not in PAGES:
        st.session_state.page = "Home"
    st.session_state.setdefault("page_picker", st.session_state.page)
    if st.session_state.page_picker not in PAGES:
        st.session_state.page_picker = st.session_state.page
    st.session_state.setdefault("score", 0)
    st.session_state.setdefault("scenario_index", 0)
    st.session_state.setdefault("checker_result", None)
    st.session_state.setdefault("checker_patient_data", None)
    st.session_state.setdefault("language", "🇺🇸 English")
    if st.session_state.language not in LANGUAGE_OPTIONS:
        st.session_state.language = "🇺🇸 English"
    st.session_state.setdefault("language_picker", st.session_state.language)
    if st.session_state.language_picker not in LANGUAGE_OPTIONS:
        st.session_state.language_picker = st.session_state.language


def sidebar() -> None:
    st.sidebar.markdown("## LifeLine AI")
    selected_language = st.sidebar.selectbox(
        "Language",
        LANGUAGE_OPTIONS,
        key="language_picker",
        help="Search or select a language.",
    )
    language_changed = selected_language != st.session_state.language
    if language_changed:
        st.session_state.language = selected_language
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
    if language_changed or page_changed:
        st.rerun()
    st.sidebar.divider()
    st.sidebar.markdown(f'<span class="soft-badge">{h("V1 prototype")}</span>', unsafe_allow_html=True)
    st.sidebar.write("")
    st.sidebar.caption(tr("Decision-support prototype. Not a replacement for doctors."))


def switch_page(page: str) -> None:
    st.session_state.page = page
    st.rerun()


def render_quick_jumps(prefix: str, exclude: str | None = None) -> None:
    targets = [
        ("Health Checker", "Patient Health Checker"),
        ("Health & Medicine Q&A", "Disease Q&A Assistant"),
        ("Medication Safety", "Medication Safety Checker"),
        ("Doctor Dashboard", "Doctor Dashboard"),
        ("Scenario Challenge", "Scenario Challenge"),
    ]
    cols = st.columns(len(targets))
    for index, (label, page) in enumerate(targets):
        disabled = page == exclude
        if cols[index].button(tr(label), key=f"{prefix}_{page}", disabled=disabled, width="stretch"):
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


def fast_analyze_patient(data: dict[str, Any]) -> Any:
    try:
        return analyze_patient(data, use_ml=False)
    except TypeError:
        return analyze_patient(data)


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
            <div class="small-title">{badge}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sam() -> None:
    with st.popover("Sam"):
        st.markdown(f'<div class="small-title">{h("Sam assistant")}</div>', unsafe_allow_html=True)
        st.write(tr("Hello, I'm Sam. I'm here to help you."))
        message = st.text_input(
            tr("Type to Sam"),
            placeholder=tr("Example: I have fever and cough"),
            key="sam_bubble_input",
        )
        if message:
            command = route_message(message)
            st.write(translate_text(command.message, st.session_state.language))
            if command.target_page and st.button(tr(f"Open {command.target_page}"), key="sam_bubble_open", width="stretch"):
                switch_page(command.target_page)


def render_home() -> None:
    render_command_bar()
    hero_subtitle = h(
        "A simple health risk and doctor-visit advisor. It helps users check symptoms, learn about diseases, get precautions, and understand when medical help is needed."
    )
    st.markdown(
        f"""
        <div class="hero">
            <div class="small-title">{h("AI health guidance")}</div>
            <h1>LifeLine AI</h1>
            <p class="muted">{hero_subtitle}</p>
            <br>
            <span class="soft-badge">{h("Prediction")}</span>
            <span class="soft-badge">{h("Recommendations")}</span>
            <span class="soft-badge">{h("Simple language")}</span>
            <span class="soft-badge">{h("Sam bubble assistant")}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><span class="token">01</span><b>{h("Risk Prediction")}</b><span class="muted">{h("Self-care, doctor visit, urgent care, or emergency.")}</span></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><span class="token">02</span><b>{h("Advanced Advice")}</b><span class="muted">{h("Care steps, prevention, avoid-list, and red flags.")}</span></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><span class="token">03</span><b>{h("Sam Assistant")}</b><span class="muted">{h("Click the bottom-right bubble to ask for help.")}</span></div>', unsafe_allow_html=True)


def patient_form() -> dict[str, Any]:
    st.markdown(f"**{tr('Basic details')}**")
    patient_name = st.text_input(tr("Patient name or ID"), placeholder=tr("Example: Patient 001"))
    b1, b2 = st.columns(2)
    with b1:
        age = st.number_input(tr("Age"), min_value=0, max_value=120, value=25)
    with b2:
        gender = st.selectbox(tr("Gender"), ["Prefer not to say", "Female", "Male", "Other"], format_func=tr)
    st.markdown(f"**{tr('Symptoms')}**")
    selected_symptoms = st.multiselect(tr("Choose symptoms from list"), SYMPTOM_OPTIONS, format_func=tr)
    typed_symptoms = st.text_area(
        tr("Write any other symptoms"),
        placeholder=tr("Example: ear pain, burning urination, neck stiffness"),
        help=tr("Use commas if adding more than one symptom."),
    )
    symptoms = unique_items(selected_symptoms + split_free_text_items(typed_symptoms))
    s1, s2 = st.columns(2)
    with s1:
        duration_days = st.number_input(tr("Symptom duration in days"), min_value=0, max_value=90, value=1)
    with s2:
        pain_level = st.slider(tr("Pain level"), 0, 10, 3)

    st.markdown(f"**{tr('Optional measurements')}**")
    with st.expander(tr("Add temperature, pulse, blood pressure, or oxygen"), expanded=True):
        temperature = st.number_input(tr("Temperature in Celsius"), min_value=32.0, max_value=43.0, value=37.0, step=0.1)
        know_heart_rate = st.checkbox(tr("I know my heart rate / pulse"), value=False)
        heart_rate = 0
        if know_heart_rate:
            heart_rate = st.number_input(
                tr("Heart rate / pulse per minute"),
                min_value=0,
                max_value=240,
                value=80,
                help=tr("You can count your pulse for 60 seconds, or use a smartwatch/pulse oximeter if available."),
            )
        know_bp = st.checkbox(tr("I know my blood pressure numbers"), value=False)
        systolic_bp = 0
        diastolic_bp = 0
        if know_bp:
            systolic_bp = st.number_input(
                tr("Blood pressure top number"),
                min_value=0,
                max_value=260,
                value=120,
                help=tr("This is called systolic BP. It is the first/top number, like 120 in 120/80."),
            )
            diastolic_bp = st.number_input(
                tr("Blood pressure bottom number"),
                min_value=0,
                max_value=180,
                value=80,
                help=tr("This is called diastolic BP. It is the second/bottom number, like 80 in 120/80."),
            )
            st.caption(tr("If your BP machine shows 120/80, enter 120 as top number and 80 as bottom number."))
        know_oxygen = st.checkbox(tr("I know my oxygen level"), value=False)
        oxygen = 0
        if know_oxygen:
            oxygen = st.number_input(
                tr("Oxygen level from pulse oximeter"),
                min_value=0,
                max_value=100,
                value=98,
                help=tr("This is SpO2. It usually needs a pulse oximeter finger device. If you do not have one, leave this unchecked."),
            )
            st.caption(tr("Most people at home will only know this if they have a pulse oximeter."))

    st.markdown(f"**{tr('Existing conditions')}**")
    selected_conditions = st.multiselect(tr("Choose existing conditions from list"), CONDITION_OPTIONS, format_func=tr)
    typed_conditions = st.text_area(
        tr("Write any other existing conditions"),
        placeholder=tr("Example: thyroid problem, anemia, migraine"),
        help=tr("Use commas if adding more than one condition."),
    )
    conditions = unique_items(selected_conditions + split_free_text_items(typed_conditions))
    medications = st.text_area(tr("Current medicines or allergies"), placeholder=tr("Example: allergic to penicillin, taking asthma inhaler"))
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
    }


def render_result_panel(result: Any, advice: dict[str, Any]) -> None:
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
    st.subheader(tr(result.recommendation))
    st.info(tr(advice["risk_summary"]))
    st.write(tr(advice["simple_explanation"]))
    if result.model_prediction:
        st.caption(tr(f"ML model prediction: {result.model_prediction} | Confidence: {result.model_confidence}"))
    st.markdown(f"**{tr('Likely health pattern')}**")
    st.write(tr(advice["likely_pattern"]))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(f"**{tr('Why the app thinks this')}**")
        for signal in translate_items(result.signals, st.session_state.language):
            st.write(f"- {signal}")
        st.markdown(f"**{tr('What to do now')}**")
        for step in translate_items(advice["care_steps"], st.session_state.language):
            st.write(f"- {step}")
        st.markdown(f"**{tr('Home care support')}**")
        for step in translate_items(advice["home_care"], st.session_state.language):
            st.write(f"- {step}")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f"**{tr('Questions to ask a doctor')}**")
    for item in translate_items(advice["doctor_questions"], st.session_state.language):
        st.write(f"- {item}")
    st.markdown("</div>", unsafe_allow_html=True)
    st.warning(tr(advice["disclaimer"]))


def render_checker() -> None:
    render_command_bar()
    page_header(
        "Patient Health Checker",
        "Enter symptoms and the details you know. Heart rate, blood pressure, and oxygen are optional for home users.",
        "Prediction workspace",
    )
    form_col, result_col = st.columns([1.05, .95], gap="large")
    with form_col:
        st.markdown(f'<div class="section-label">{h("Patient intake")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        data = patient_form()
        save_to_dashboard = st.checkbox(tr("Save this case to Doctor Dashboard"), value=True)
        if st.button(tr("Analyze Health"), type="primary", width="stretch"):
            if not data["symptoms"]:
                st.error(tr("Please choose at least one symptom."))
            else:
                result = analyze_patient(data)
                advice = build_recommendations(result)
                st.session_state.checker_result = {
                    "result": result,
                    "advice": advice,
                    "saved": bool(save_to_dashboard),
                }
                st.session_state.checker_patient_data = data
                if save_to_dashboard:
                    save_case(data, result)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with result_col:
        st.markdown(f'<div class="section-label">{h("Live result")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        stored = st.session_state.get("checker_result")
        if stored:
            if stored.get("saved"):
                st.success(tr("Case saved to Doctor Dashboard."))
            render_result_panel(stored["result"], stored["advice"])
            patient_data = st.session_state.get("checker_patient_data") or {}
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
        st.markdown("</div>", unsafe_allow_html=True)
    st.write("")


def render_qa() -> None:
    render_command_bar()
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
        question = st.text_input(tr("Ask in simple words"), placeholder=tr("Example: What is ibuprofen used for?"))
        examples = st.columns(4)
        example_questions = [
            "What is paracetamol used for?",
            "Can I take antibiotics for fever?",
            "Side effects of ibuprofen",
            "What is Parkinson's?",
        ]
        for idx, example in enumerate(example_questions):
            if examples[idx].button(tr(example)):
                question = example
        if question:
            answer = translate_answer(answer_question(question), st.session_state.language)
            st.markdown('<div class="panel">', unsafe_allow_html=True)
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
            st.markdown("</div>", unsafe_allow_html=True)
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
    render_command_bar()
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
        st.markdown('<div class="panel">', unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)
    with result_area:
        st.markdown(f'<div class="section-label">{h("Safety result")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)


def render_dashboard() -> None:
    render_command_bar()
    page_header(
        "Doctor / Hospital Dashboard",
        "Review saved patient cases, sorted by urgency so serious cases are easier to notice first.",
        "Clinical queue",
    )
    cases = list_cases()
    if not cases:
        st.info(tr("No saved patient cases yet. Use the Health Checker and save a case."))
        return

    df = pd.DataFrame(cases)
    selected = st.selectbox(tr("Filter by risk"), ["All", "Self-Care", "Doctor Visit Recommended", "Urgent Care", "Emergency"], format_func=tr)
    if selected != "All":
        df = df[df["risk_level"] == selected]
    df["urgency_rank"] = df["risk_level"].map(RISK_ORDER)
    df = df.sort_values(["urgency_rank", "score"], ascending=[False, False])

    st.markdown(f'<div class="section-label">{h("Queue summary")}</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(tr("Total cases"), len(df))
    c2.metric(tr("Emergency"), int((df["risk_level"] == "Emergency").sum()))
    c3.metric(tr("Urgent"), int((df["risk_level"] == "Urgent Care").sum()))
    c4.metric(tr("Doctor visits"), int((df["risk_level"] == "Doctor Visit Recommended").sum()))

    st.markdown(f'<div class="section-label">{h("Patient cases")}</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.dataframe(
        df[["created_at", "patient_name", "age", "symptoms", "category", "risk_level", "recommendation", "score"]],
        width="stretch",
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown(f'<div class="section-label">{h("Risk levels")}</div>', unsafe_allow_html=True)
        st.bar_chart(df["risk_level"].value_counts())
    with chart_col2:
        st.markdown(f'<div class="section-label">{h("Categories")}</div>', unsafe_allow_html=True)
        st.bar_chart(df["category"].value_counts())


def render_challenge() -> None:
    render_command_bar()
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

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-label">{h("Current case")}</div>', unsafe_allow_html=True)
    st.subheader(tr("Patient Case"))
    st.write(tr(scenario["case"]))
    choice = st.radio(tr("What should this patient do?"), ["Self-Care", "Doctor Visit Recommended", "Urgent Care", "Emergency"], format_func=tr)
    if st.button(tr("Check My Answer")):
        result = fast_analyze_patient(scenario["data"])
        if choice == result.risk_level:
            st.session_state.score += 10
            st.success(tr(f"Correct. LifeLine AI also chose: {result.risk_level}"))
        else:
            st.warning(tr(f"LifeLine AI chose: {result.risk_level}"))
        st.write(tr(result.explanation))
        for signal in translate_items(result.signals, st.session_state.language):
            st.write(f"- {signal}")
    if st.button(tr("Next Scenario")):
        st.session_state.scenario_index = random.randint(0, len(SCENARIOS) - 1)
        st.rerun()
    st.metric(tr("Score"), st.session_state.score)
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    inject_css()
    init_state()
    sidebar()

    if st.session_state.page == "Home":
        render_home()
    elif st.session_state.page == "Patient Health Checker":
        render_checker()
    elif st.session_state.page == "Disease Q&A Assistant":
        render_qa()
    elif st.session_state.page == "Medication Safety Checker":
        render_medication_safety()
    elif st.session_state.page == "Doctor Dashboard":
        render_dashboard()
    elif st.session_state.page == "Scenario Challenge":
        render_challenge()
    render_sam()


if __name__ == "__main__":
    main()
