from __future__ import annotations

from typing import Any

from backend.care_features import result_value, split_list_items


def _list_text(items: Any) -> str:
    clean = split_list_items(items)
    return ", ".join(clean) if clean else "not provided"


def _vitals_text(patient_data: dict[str, Any]) -> str:
    vitals: list[str] = []
    temperature = patient_data.get("temperature")
    heart_rate = patient_data.get("heart_rate")
    systolic = patient_data.get("systolic_bp")
    diastolic = patient_data.get("diastolic_bp")
    oxygen = patient_data.get("oxygen")
    if temperature:
        vitals.append(f"temperature {temperature} C")
    if heart_rate:
        vitals.append(f"pulse {heart_rate}/min")
    if systolic and diastolic:
        vitals.append(f"BP {systolic}/{diastolic}")
    if oxygen:
        vitals.append(f"oxygen {oxygen}%")
    return ", ".join(vitals) if vitals else "no home measurements provided"


def _clean_sentence(text: Any) -> str:
    return str(text or "not provided").strip().rstrip(".")


def _present_text(value: Any, fallback: str = "not provided") -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else fallback


def _score_text(value: Any) -> str:
    try:
        score = max(0, min(100, int(float(value or 0))))
    except (TypeError, ValueError):
        score = 0
    return f"{score}/100"


def build_doctor_summary(patient_data: dict[str, Any], result: Any, advice: dict[str, Any]) -> str:
    name = _present_text(patient_data.get("patient_name"), "Anonymous patient")
    age = _present_text(patient_data.get("age"), "age not provided")
    gender = _present_text(patient_data.get("gender"), "gender not provided")
    duration = _present_text(patient_data.get("duration_days"))
    pain = patient_data.get("pain_level")
    pain_text = f"{pain}/10" if pain is not None else "not provided"

    return (
        f"{name}, {age} years old, {gender}, reports symptoms for {duration} day(s): "
        f"{_list_text(patient_data.get('symptoms', []))}. Pain level: {pain_text}. "
        f"Home measurements: {_vitals_text(patient_data)}. Existing conditions: "
        f"{_list_text(patient_data.get('conditions', []))}. Current medicines: "
        f"{_present_text(patient_data.get('medications'))}. Allergies: "
        f"{_present_text(patient_data.get('allergies'))}. LifeLine AI decision-support risk level: "
        f"{_present_text(result_value(result, 'risk_level'), 'Doctor Visit Recommended')} ({_score_text(result_value(result, 'score', 0))}), "
        f"possible symptom pattern: {_present_text(result_value(result, 'possible_category'), 'General Health')}. "
        f"Recommended timeframe: {_clean_sentence(advice.get('timeframe'))}. "
        f"Main advice: {_clean_sentence(result_value(result, 'recommendation', 'Review with a medical professional if symptoms continue or worsen.'))}. "
        "This summary is not a diagnosis or prescription."
    )
