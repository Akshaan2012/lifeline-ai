from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MedicationSafetyResult:
    level: str
    summary: str
    key_points: list[str]
    caution_flags: list[str]
    what_to_do: list[str]
    emergency_signs: list[str]
    questions: list[str]


MEDICINE_RULES = {
    "paracetamol": {
        "names": ["paracetamol", "acetaminophen", "crocin", "tylenol"],
        "summary": "Paracetamol can help fever and mild pain. The main safety risk is taking too much or mixing it with other medicines that also contain paracetamol.",
        "cautions": ["liver disease", "heavy alcohol use"],
    },
    "ibuprofen": {
        "names": ["ibuprofen", "advil", "brufen", "motrin"],
        "summary": "Ibuprofen can help pain, fever, swelling, and cramps. It is not safe for everyone because it can affect the stomach, kidneys, bleeding risk, and some heart conditions.",
        "cautions": ["kidney disease", "stomach ulcer", "blood thinner", "heart disease", "pregnancy", "high blood pressure"],
    },
    "aspirin": {
        "names": ["aspirin"],
        "summary": "Aspirin can help pain or fever and may be used as a blood thinner under medical advice. It can increase bleeding risk.",
        "cautions": ["child", "teen", "blood thinner", "stomach ulcer", "bleeding", "asthma"],
    },
    "antibiotics": {
        "names": ["antibiotic", "antibiotics", "amoxicillin", "azithromycin"],
        "summary": "Antibiotics treat some bacterial infections. They do not treat most viral colds, flu, or dengue-like fevers.",
        "cautions": ["allergy", "pregnancy", "kidney disease", "liver disease"],
    },
    "cetirizine": {
        "names": ["cetirizine", "zyrtec", "allergy tablet"],
        "summary": "Cetirizine can help allergy symptoms like sneezing, itching, runny nose, or hives. It can make some people sleepy.",
        "cautions": ["kidney disease", "pregnancy", "child"],
    },
    "metformin": {
        "names": ["metformin"],
        "summary": "Metformin is a prescription diabetes medicine. It should be used only with medical guidance.",
        "cautions": ["kidney disease", "liver disease", "heavy alcohol use", "vomiting", "dehydration"],
    },
    "insulin": {
        "names": ["insulin"],
        "summary": "Insulin is a prescription diabetes medicine. Wrong dose or missed meals can cause low blood sugar.",
        "cautions": ["low sugar", "skipping meals", "vomiting", "dehydration"],
    },
    "salbutamol": {
        "names": ["salbutamol", "albuterol", "inhaler"],
        "summary": "Salbutamol or albuterol is a rescue inhaler for wheezing or asthma-like breathing symptoms.",
        "cautions": ["chest pain", "fast heartbeat", "heart disease"],
    },
}


def _text_blob(items: list[str]) -> str:
    return " ".join(items).lower()


def _match_medicine(name: str) -> dict[str, object] | None:
    normalized = name.lower()
    for rule in MEDICINE_RULES.values():
        if any(alias in normalized for alias in rule["names"]):
            return rule
    return None


def analyze_medication_safety(
    medicine_name: str,
    age: int,
    allergies: str,
    conditions: list[str],
    current_medicines: str,
    pregnant: bool,
) -> MedicationSafetyResult:
    rule = _match_medicine(medicine_name)
    context = _text_blob([allergies, current_medicines, *conditions])
    caution_flags: list[str] = []

    if age < 12:
        caution_flags.append("Child: medicine safety and dose can be very different for children.")
    if age >= 65:
        caution_flags.append("Older adult: side effects and interactions can be more likely.")
    if pregnant:
        caution_flags.append("Pregnancy: ask a doctor before using medicines.")
    if allergies.strip():
        caution_flags.append("Allergy history: check ingredients carefully and ask a pharmacist.")

    if rule:
        for caution in rule["cautions"]:
            if caution in context or (caution == "pregnancy" and pregnant) or (caution in ["child", "teen"] and age < 18):
                caution_flags.append(f"Extra caution: {caution}.")
        summary = str(rule["summary"])
        medicine_known = True
    else:
        summary = "I do not have a detailed safety card for this medicine yet. Use the label and ask a pharmacist or doctor before taking it."
        medicine_known = False

    if any(word in context for word in ["blood thinner", "warfarin", "aspirin", "clopidogrel"]):
        caution_flags.append("Possible bleeding-risk medicine: ask before mixing with painkillers or aspirin.")
    if any(word in context for word in ["kidney", "liver", "heart"]):
        caution_flags.append("Long-term condition mentioned: medicine choice may need professional review.")

    level = "Low caution"
    if caution_flags:
        level = "Use with caution"
    if not medicine_known or len(caution_flags) >= 4:
        level = "Ask a doctor/pharmacist first"

    return MedicationSafetyResult(
        level=level,
        summary=summary,
        key_points=[
            "This checker gives safety education, not a prescription.",
            "Correct dose depends on age, weight, diagnosis, other medicines, pregnancy, allergies, and kidney/liver health.",
            "Read the active ingredient on the label before taking anything.",
        ],
        caution_flags=caution_flags or ["No major caution was detected from what you entered, but still follow the label or medical advice."],
        what_to_do=[
            "Use the medicine only for the reason it is meant for.",
            "Ask a pharmacist before mixing it with other medicines.",
            "Keep a list of medicines and allergies to show a doctor.",
        ],
        emergency_signs=[
            "Breathing trouble.",
            "Swelling of lips, tongue, face, or throat.",
            "Fainting, severe dizziness, confusion, or seizure.",
            "Accidental overdose or taking much more than advised.",
        ],
        questions=[
            "Is this medicine safe for my age and health conditions?",
            "Can I take it with my current medicines?",
            "What side effects should make me stop and get help?",
        ],
    )
