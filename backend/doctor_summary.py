from __future__ import annotations

from typing import Any


def _list_text(items: list[str]) -> str:
    clean = [str(item).strip() for item in items if str(item).strip()]
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


def build_doctor_summary(patient_data: dict[str, Any], result: Any, advice: dict[str, Any]) -> str:
    name = patient_data.get("patient_name") or "Anonymous patient"
    age = patient_data.get("age") or "age not provided"
    gender = patient_data.get("gender") or "gender not provided"
    duration = patient_data.get("duration_days") or "not provided"
    pain = patient_data.get("pain_level")
    pain_text = f"{pain}/10" if pain is not None else "not provided"

    return (
        f"{name}, {age} years old, {gender}, reports symptoms for {duration} day(s): "
        f"{_list_text(patient_data.get('symptoms', []))}. Pain level: {pain_text}. "
        f"Home measurements: {_vitals_text(patient_data)}. Existing conditions: "
        f"{_list_text(patient_data.get('conditions', []))}. Current medicines/allergies: "
        f"{patient_data.get('medications') or 'not provided'}. LifeLine AI risk level: "
        f"{result.risk_level} ({result.score}/100), likely pattern: {result.possible_category}. "
        f"Recommended timeframe: {_clean_sentence(advice['timeframe'])}. "
        f"Main advice: {_clean_sentence(result.recommendation)}."
    )
