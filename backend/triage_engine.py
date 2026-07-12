from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


RISK_ORDER = {
    "Self-Care": 1,
    "Doctor Visit Recommended": 2,
    "Urgent Care": 3,
    "Emergency": 4,
}

EMERGENCY_SYMPTOMS = {
    "heart attack warning signs",
    "severe breathing difficulty",
    "fainting",
    "confusion",
    "stroke signs",
    "seizure",
    "severe allergic reaction",
    "blue lips",
}

# These descriptions are broad enough that ordinary users may select them for
# both dangerous and non-dangerous problems. They must never become self-care,
# but the follow-up answers decide whether they need emergency escalation.
AMBIGUOUS_HIGH_RISK_SYMPTOMS = {
    "chest pain",
}

URGENT_SYMPTOMS = {
    "chest pain",
    "shortness of breath",
    "high fever",
    "severe headache",
    "severe stomach pain",
    "persistent vomiting",
    "dehydration",
    "blood in stool",
    "black stool",
    "heavy bleeding",
    "pregnancy bleeding",
    "severe weakness",
    "very high sugar symptoms",
}

SYMPTOM_ALIASES = {
    "chest pain": (
        "chest hurts", "chest hurt", "pain in my chest", "pain in the chest",
        "chest discomfort", "chest tightness", "tight chest", "chest pressure",
    ),
    "shortness of breath": (
        "short of breath", "breathless", "trouble breathing", "hard to breathe",
        "difficulty breathing", "bad breathing", "breathing bad", "breathing is bad",
        "breathing worse",
    ),
    "severe breathing difficulty": (
        "cannot breathe", "can't breathe", "cant breathe", "gasping for air",
    ),
    "confusion": ("confused", "disoriented", "not making sense"),
    "fainting": ("fainted", "passed out", "blacked out", "lost consciousness"),
    "stroke signs": ("face drooping", "face droop", "slurred speech", "speech is slurred", "arm weakness"),
    "seizure": ("convulsion", "convulsions", "having a fit"),
    "severe allergic reaction": ("anaphylaxis", "throat swelling", "throat is swelling", "tongue swelling"),
    "blue lips": ("lips are blue", "bluish lips"),
    "severe headache": ("worst headache", "extreme headache"),
    "persistent vomiting": ("cannot stop vomiting", "keeps vomiting", "repeated vomiting"),
    "blood in stool": ("bloody stool", "blood in poo", "blood in poop"),
    "black stool": ("black stools", "tarry stool", "tarry stools"),
    "heavy bleeding": ("bleeding heavily", "a lot of bleeding", "won't stop bleeding", "wont stop bleeding"),
    "pregnancy bleeding": ("bleeding while pregnant", "pregnant and bleeding"),
}

SYMPTOM_CATEGORIES = {
    "Respiratory": {"cough", "sore throat", "shortness of breath", "severe breathing difficulty", "wheezing"},
    "Heart Warning": {"chest pain", "sweating", "fainting", "palpitations"},
    "Infection/Fever": {"fever", "high fever", "chills", "body pain", "fatigue"},
    "Digestive": {"stomach pain", "severe stomach pain", "diarrhea", "persistent vomiting", "nausea", "blood in stool", "black stool"},
    "Bleeding/Pregnancy Warning": {"heavy bleeding", "pregnancy bleeding"},
    "Diabetes Warning": {"very high sugar symptoms", "frequent urination", "excessive thirst", "blurred vision"},
    "Neurological": {"severe headache", "confusion", "stroke signs", "seizure", "dizziness"},
    "Skin/Allergy": {"rash", "itching", "swelling", "severe allergic reaction"},
}

KNOWN_SYMPTOMS = set().union(
    EMERGENCY_SYMPTOMS,
    AMBIGUOUS_HIGH_RISK_SYMPTOMS,
    URGENT_SYMPTOMS,
    *SYMPTOM_CATEGORIES.values(),
)

SYMPTOM_PRIORITY = {
    **{symptom: 4 for symptom in EMERGENCY_SYMPTOMS},
    **{symptom: 3 for symptom in URGENT_SYMPTOMS | AMBIGUOUS_HIGH_RISK_SYMPTOMS},
}


@dataclass(frozen=True)
class TriageResult:
    risk_level: str
    score: int
    possible_category: str
    recommendation: str
    explanation: str
    signals: list[str]
    model_prediction: str | None = None
    model_confidence: float | None = None


def canonicalize_symptom(value: Any) -> str:
    matches = extract_symptoms(value)
    if matches:
        return sorted(matches, key=lambda item: (SYMPTOM_PRIORITY.get(item, 1), len(item)), reverse=True)[0]
    text = " ".join(str(value).strip().lower().split())
    return text


def _contains_phrase(text: str, phrase: str) -> bool:
    if not phrase:
        return False
    if " " in phrase:
        return phrase in text
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def extract_symptoms(value: Any) -> set[str]:
    text = " ".join(str(value).strip().lower().split())
    if not text:
        return set()
    matches: set[str] = set()
    for known in KNOWN_SYMPTOMS:
        if _contains_phrase(text, known):
            matches.add(known)
    for canonical, aliases in SYMPTOM_ALIASES.items():
        if _contains_phrase(text, canonical) or any(_contains_phrase(text, alias) for alias in aliases):
            matches.add(canonical)
    return matches


def _selected_symptoms(data: dict[str, Any]) -> set[str]:
    selected: set[str] = set()
    for item in data.get("symptoms", []):
        matches = extract_symptoms(item)
        if matches:
            selected.update(matches)
        else:
            canonical = canonicalize_symptom(item)
            if canonical:
                selected.add(canonical)
    return selected


def _safe_float(value: Any, default: float = 0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    return int(_safe_float(value, default))


def classify_category(symptoms: set[str]) -> str:
    matches: list[tuple[str, int]] = []
    for category, category_symptoms in SYMPTOM_CATEGORIES.items():
        count = len(symptoms.intersection(category_symptoms))
        if count:
            matches.append((category, count))
    if not matches:
        return "General Health"
    matches.sort(key=lambda item: item[1], reverse=True)
    return matches[0][0]


def analyze_patient(data: dict[str, Any], use_ml: bool = True) -> TriageResult:
    symptoms = _selected_symptoms(data)
    age = _safe_int(data.get("age"))
    duration = _safe_int(data.get("duration_days"))
    pain = _safe_int(data.get("pain_level"))
    temperature = _safe_float(data.get("temperature"))
    heart_rate = _safe_int(data.get("heart_rate"))
    systolic = _safe_int(data.get("systolic_bp"))
    diastolic = _safe_int(data.get("diastolic_bp"))
    oxygen = _safe_int(data.get("oxygen"))
    conditions = {str(item).strip().lower() for item in data.get("conditions", [])}

    score = 0
    signals: list[str] = []

    emergency_hits = symptoms.intersection(EMERGENCY_SYMPTOMS)
    ambiguous_high_risk_hits = symptoms.intersection(AMBIGUOUS_HIGH_RISK_SYMPTOMS)
    urgent_hits = symptoms.intersection(URGENT_SYMPTOMS)

    if emergency_hits:
        score += 70
        signals.append("One or more emergency warning symptoms are present.")
    if ambiguous_high_risk_hits:
        signals.append("A potentially serious symptom needs careful follow-up answers.")
    if urgent_hits:
        score += 28
        signals.append("Some symptoms can become serious and need faster attention.")
    if age >= 65:
        score += 10
        signals.append("Older age can increase health risk.")
    elif age <= 5 and age > 0:
        score += 8
        signals.append("Very young patients need extra caution.")
    if duration >= 7:
        score += 10
        signals.append("Symptoms lasting a week or more should be checked.")
    elif duration >= 3:
        score += 5
        signals.append("Symptoms have lasted multiple days.")
    if pain >= 8:
        score += 18
        signals.append("Pain level is high.")
    elif pain >= 5:
        score += 8
        signals.append("Pain level is moderate.")
    if temperature >= 39.4:
        score += 22
        signals.append("Fever is very high.")
    elif temperature >= 38:
        score += 8
        signals.append("Fever is present.")
    if oxygen and oxygen < 90:
        score += 45
        signals.append("Oxygen level is dangerously low.")
    elif oxygen and oxygen < 94:
        score += 25
        signals.append("Oxygen level is lower than expected.")
    if heart_rate and (heart_rate < 50 or heart_rate > 120):
        score += 14
        signals.append("Heart rate is outside the usual resting range.")
    if systolic and diastolic and (systolic >= 180 or diastolic >= 120):
        score += 35
        signals.append("Blood pressure is in a danger range.")
    elif systolic and diastolic and (systolic >= 140 or diastolic >= 90):
        score += 8
        signals.append("Blood pressure is high.")
    if {"diabetes", "heart disease", "asthma", "copd", "kidney disease"}.intersection(conditions):
        score += 10
        signals.append("Existing health conditions can increase risk.")
    if len(symptoms) >= 5:
        score += 5
        signals.append("Several symptoms are happening together.")
    if len({"frequent urination", "excessive thirst", "blurred vision", "fatigue"}.intersection(symptoms)) >= 3:
        score += 22
        signals.append("This combination can be a diabetes warning pattern.")

    if ambiguous_high_risk_hits:
        # A broad high-risk description may be clarified down from Emergency,
        # but never below same-day urgent assessment.
        score = max(score, 45)
    if urgent_hits:
        # Symptoms defined as urgent must never fall through to a routine
        # doctor visit merely because few other score inputs were supplied.
        score = max(score, 45)

    if emergency_hits:
        # Explicit red flags override numeric scoring. A model or a low total
        # must never downgrade an emergency warning.
        score = max(score, 70)
        risk = "Emergency"
        recommendation = "Get medical help immediately."
    elif score >= 70:
        risk = "Emergency"
        recommendation = "Get medical help immediately."
    elif score >= 45:
        risk = "Urgent Care"
        recommendation = "Visit a clinic or hospital as soon as possible."
    elif score >= 22:
        risk = "Doctor Visit Recommended"
        recommendation = "Book a doctor visit, especially if symptoms continue or get worse."
    else:
        risk = "Self-Care"
        recommendation = "Home care may be enough for now, but keep watching your symptoms."

    category = classify_category(symptoms)
    if not signals:
        signals.append("No major danger signs were found from the details entered.")

    model_prediction = None
    model_confidence = None
    if use_ml:
        try:
            from backend.ml_model import predict_with_model

            model_result = predict_with_model(data)
            model_prediction = str(model_result["prediction"])
            model_confidence = float(model_result["confidence"])
            if RISK_ORDER[model_prediction] > RISK_ORDER[risk] and model_confidence >= 0.62:
                risk = model_prediction
                signals.append("The ML model saw a higher risk pattern in similar training cases.")
        except Exception:
            signals.append("ML model was unavailable, so the rule engine completed the prediction.")

    explanation = (
        f"The app looked at symptoms, age, duration, pain, vital signs, and health history. "
        f"Based on these details, this looks like a {risk.lower()} case."
    )

    return TriageResult(
        risk_level=risk,
        score=min(score, 100),
        possible_category=category,
        recommendation=recommendation,
        explanation=explanation,
        signals=signals,
        model_prediction=model_prediction,
        model_confidence=model_confidence,
    )
