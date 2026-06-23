from __future__ import annotations

from typing import Any

from backend.triage_engine import RISK_ORDER


DANGER_WORDS = {
    "breathing",
    "breathless",
    "chest pain",
    "confusion",
    "faint",
    "fainting",
    "seizure",
    "stroke",
    "blue lips",
    "blood",
    "severe",
    "worst headache",
}


def evaluate_follow_up(
    original_result: Any,
    status: str,
    new_notes: str,
    hours_since_check: int,
) -> dict[str, Any]:
    notes = new_notes.lower()
    danger_found = any(word in notes for word in DANGER_WORDS)
    risk_rank = RISK_ORDER.get(original_result.risk_level, 1)

    if danger_found or status == "Worse" or risk_rank >= RISK_ORDER["Urgent Care"]:
        level = "Needs faster care"
        message = "Because symptoms are worse, serious, or high-risk, medical care should not be delayed."
        next_steps = [
            "Seek urgent care today, or emergency help now if symptoms are severe.",
            "Do not wait at home if breathing, chest pain, confusion, fainting, seizure, or stroke-like signs are present.",
            "Bring the doctor summary, medicines, allergy details, and any home measurements.",
        ]
    elif status == "Same" and hours_since_check >= 24:
        level = "Doctor review is safer"
        message = "Symptoms have not improved after a day, so a doctor review is a safer next step."
        next_steps = [
            "Book a doctor visit within 1 to 2 days.",
            "Keep tracking temperature, pain, breathing, food intake, and any new symptoms.",
            "Use the doctor summary so the visit is faster and clearer.",
        ]
    elif status == "Better":
        level = "Improving"
        message = "The symptoms sound better than before. Keep watching for any return or worsening."
        next_steps = [
            "Continue rest, fluids, and the safe care steps already shown.",
            "Avoid heavy activity until you are clearly better.",
            "Get medical help if symptoms return, worsen, or new danger signs appear.",
        ]
    else:
        level = "Keep monitoring"
        message = "There is no clear worsening from this follow-up, but symptoms still need watching."
        next_steps = [
            "Check again in 12 to 24 hours.",
            "Write down any new symptoms, temperature, pain level, and medicines taken.",
            "Move to urgent care if symptoms become worse or danger signs appear.",
        ]

    return {
        "level": level,
        "message": message,
        "next_steps": next_steps,
        "safety_note": "This follow-up is decision support only. It does not replace a doctor or emergency service.",
    }
