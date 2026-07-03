from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any
from uuid import uuid4


ACTIVE_INGREDIENT_GROUPS = {
    "paracetamol": {"paracetamol", "acetaminophen", "crocin", "calpol", "tylenol"},
    "ibuprofen": {"ibuprofen", "brufen", "advil", "motrin"},
    "aspirin": {"aspirin", "ecosprin"},
    "cetirizine": {"cetirizine", "zyrtec"},
}

INTERACTION_RULES = [
    ({"ibuprofen", "aspirin"}, "Ibuprofen and aspirin together can increase stomach irritation and bleeding risk."),
    ({"ibuprofen", "warfarin"}, "Ibuprofen with warfarin can increase bleeding risk."),
    ({"aspirin", "warfarin"}, "Aspirin with warfarin can increase bleeding risk."),
    ({"cetirizine", "diphenhydramine"}, "Two sedating allergy medicines can cause extra sleepiness."),
    ({"metformin", "heavy alcohol use"}, "Metformin and heavy alcohol use need professional review."),
]


def split_medications(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = re.split(r"[,;\n]+", value or "")
    return [str(item).strip() for item in raw if str(item).strip()]


def canonical_ingredient(medicine: str) -> str:
    normalized = medicine.lower()
    for ingredient, aliases in ACTIVE_INGREDIENT_GROUPS.items():
        if any(alias in normalized for alias in aliases):
            return ingredient
    return normalized.split()[0] if normalized.split() else ""


def reconcile_medications(medicines: str | list[str], allergies: str = "") -> dict[str, list[str]]:
    items = split_medications(medicines)
    canonical = [canonical_ingredient(item) for item in items]
    duplicates = sorted({item for item in canonical if item and canonical.count(item) > 1})
    duplicate_flags = [
        f"Possible duplicate active ingredient: {item.title()}. Check every label before taking either product."
        for item in duplicates
    ]

    present = set(canonical)
    interaction_flags = [message for pair, message in INTERACTION_RULES if pair.issubset(present)]
    allergy_flags: list[str] = []
    allergy_text = allergies.lower()
    for item, ingredient in zip(items, canonical):
        if ingredient and ingredient in allergy_text:
            allergy_flags.append(f"Possible allergy match: {item}. Do not take it until a clinician or pharmacist checks this.")

    return {
        "medicines": items,
        "duplicate_flags": duplicate_flags,
        "interaction_flags": interaction_flags,
        "allergy_flags": allergy_flags,
    }


def clinician_evidence(patient_data: dict[str, Any], result: Any) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for symptom in patient_data.get("symptoms", []):
        evidence.append({"input": str(symptom), "effect": "Included in symptom and red-flag matching."})
    measurements = {
        "Temperature": patient_data.get("temperature"),
        "Oxygen": patient_data.get("oxygen"),
        "Pulse": patient_data.get("heart_rate"),
        "Systolic BP": patient_data.get("systolic_bp"),
        "Diastolic BP": patient_data.get("diastolic_bp"),
        "Pain": patient_data.get("pain_level"),
    }
    for label, value in measurements.items():
        if value not in (None, "", 0, 0.0):
            evidence.append({"input": f"{label}: {value}", "effect": "Included in the rule-based risk score."})
    for signal in getattr(result, "signals", []):
        evidence.append({"input": "Rule outcome", "effect": str(signal)})
    return evidence


def emergency_action_plan(patient_data: dict[str, Any]) -> list[str]:
    return [
        "Call 112 or the local emergency number now.",
        "Do not drive yourself; ask someone to stay with the patient.",
        "Note when the symptoms began and whether they changed suddenly.",
        "Keep the medicine list, allergies, emergency contact, and recent measurements ready.",
        "Do not give food, drink, or medicine to an unconscious or confused person.",
    ]


def reminder_status(reminder: dict[str, Any], today: date | None = None) -> str:
    today = today or date.today()
    try:
        due = date.fromisoformat(str(reminder.get("due_date")))
    except (TypeError, ValueError):
        return "Unscheduled"
    if reminder.get("completed"):
        return "Completed"
    if due < today:
        return "Overdue"
    if due == today:
        return "Due today"
    return "Upcoming"


def build_fhir_bundle(profile: dict[str, Any], result: Any | None = None) -> dict[str, Any]:
    patient_id = str(profile.get("patient_id") or profile.get("patient_name") or uuid4().hex[:12])
    resources: list[dict[str, Any]] = [
        {
            "fullUrl": f"urn:uuid:{patient_id}",
            "resource": {
                "resourceType": "Patient",
                "id": patient_id,
                "name": [{"text": profile.get("patient_name") or "Anonymous"}],
                "gender": str(profile.get("gender") or "unknown").lower().replace("prefer not to say", "unknown"),
                "extension": [
                    {"url": "https://lifeline-ai.local/emergency-contact", "valueString": profile.get("emergency_contact", "")},
                    {"url": "https://lifeline-ai.local/blood-group", "valueString": profile.get("blood_group", "")},
                ],
            },
        }
    ]
    for condition in profile.get("conditions", []):
        resources.append({"resource": {"resourceType": "Condition", "subject": {"reference": f"Patient/{patient_id}"}, "code": {"text": condition}}})
    for medication in split_medications(profile.get("medications", "")):
        resources.append({"resource": {"resourceType": "MedicationStatement", "status": "recorded", "subject": {"reference": f"Patient/{patient_id}"}, "medicationCodeableConcept": {"text": medication}}})
    if result is not None:
        resources.append({
            "resource": {
                "resourceType": "RiskAssessment",
                "status": "final",
                "subject": {"reference": f"Patient/{patient_id}"},
                "occurrenceDateTime": datetime.now().isoformat(timespec="seconds"),
                "prediction": [{"qualitativeRisk": {"text": result.risk_level}, "rationale": result.explanation}],
                "note": [{"text": "Educational decision support; not a diagnosis or prescription."}],
            }
        })
    return {"resourceType": "Bundle", "type": "collection", "timestamp": datetime.now().isoformat(timespec="seconds"), "entry": resources}
