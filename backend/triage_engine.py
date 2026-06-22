from __future__ import annotations

from dataclasses import dataclass
from typing import Any


RISK_ORDER = {
    "Self-Care": 1,
    "Doctor Visit Recommended": 2,
    "Urgent Care": 3,
    "Emergency": 4,
}

EMERGENCY_SYMPTOMS = {
    "chest pain",
    "severe breathing difficulty",
    "fainting",
    "confusion",
    "stroke signs",
    "seizure",
    "severe allergic reaction",
    "blue lips",
}

URGENT_SYMPTOMS = {
    "shortness of breath",
    "high fever",
    "severe headache",
    "severe stomach pain",
    "persistent vomiting",
    "dehydration",
    "blood in stool",
    "very high sugar symptoms",
}

SYMPTOM_CATEGORIES = {
    "Respiratory": {"cough", "sore throat", "shortness of breath", "severe breathing difficulty", "wheezing"},
    "Heart Warning": {"chest pain", "sweating", "fainting", "palpitations"},
    "Infection/Fever": {"fever", "high fever", "chills", "body pain", "fatigue"},
    "Digestive": {"stomach pain", "severe stomach pain", "diarrhea", "persistent vomiting", "nausea"},
    "Diabetes Warning": {"very high sugar symptoms", "frequent urination", "excessive thirst", "blurred vision"},
    "Neurological": {"severe headache", "confusion", "stroke signs", "seizure", "dizziness"},
    "Skin/Allergy": {"rash", "itching", "swelling", "severe allergic reaction"},
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


def _selected_symptoms(data: dict[str, Any]) -> set[str]:
    return {str(item).strip().lower() for item in data.get("symptoms", []) if str(item).strip()}


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
    urgent_hits = symptoms.intersection(URGENT_SYMPTOMS)

    if emergency_hits:
        score += 60
        signals.append("One or more emergency warning symptoms are present.")
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

    if score >= 70:
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
