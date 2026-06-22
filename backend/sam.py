from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class SamCommand:
    intent: str
    target_page: str | None
    confidence: float
    reason: str
    message: str

    def to_json(self) -> dict[str, object]:
        return asdict(self)


def route_message(message: str) -> SamCommand:
    text = message.lower().strip()

    if any(word in text for word in ["medicine safety", "safe to take", "mix", "interaction", "allergy", "allergic", "dose", "dosage"]):
        return SamCommand(
            intent="navigate",
            target_page="Medication Safety Checker",
            confidence=0.92,
            reason="The user is asking about medicine safety, interactions, allergies, or dosage.",
            message="Use Medication Safety Checker. It can flag simple safety concerns and questions to ask a pharmacist or doctor.",
        )

    medicine_words = [
        "medicine",
        "medication",
        "tablet",
        "pill",
        "dose",
        "dosage",
        "side effect",
        "antibiotic",
        "painkiller",
        "paracetamol",
        "acetaminophen",
        "ibuprofen",
        "aspirin",
        "amoxicillin",
        "cetirizine",
        "metformin",
        "insulin",
        "salbutamol",
        "albuterol",
        "ors",
    ]
    disease_words = ["alzheimer", "parkinson", "diabetes", "asthma", "disease", "what is"]
    if any(word in text for word in medicine_words + disease_words):
        return SamCommand(
            intent="navigate",
            target_page="Disease Q&A Assistant",
            confidence=0.9,
            reason="The user asked for disease or medicine information.",
            message="Use Health & Medicine Q&A. It explains diseases and medicines in simple language with precautions and warning signs.",
        )
    if any(word in text for word in ["fever", "cough", "pain", "symptom", "sick", "breathing", "headache"]):
        return SamCommand(
            intent="navigate",
            target_page="Patient Health Checker",
            confidence=0.92,
            reason="The user mentioned symptoms and may need risk checking.",
            message="Use the Health Checker. It can suggest self-care, doctor visit, urgent care, or emergency help.",
        )
    if any(word in text for word in ["doctor", "hospital", "dashboard", "cases", "patients"]):
        return SamCommand(
            intent="navigate",
            target_page="Doctor Dashboard",
            confidence=0.86,
            reason="The user wants patient case review or hospital workflow.",
            message="Open the Doctor Dashboard to see saved cases sorted by risk.",
        )
    if any(word in text for word in ["game", "challenge", "scenario", "quiz"]):
        return SamCommand(
            intent="navigate",
            target_page="Scenario Challenge",
            confidence=0.88,
            reason="The user wants the interactive health challenge.",
            message="Try Scenario Challenge to practice choosing the right care level.",
        )
    if any(word in text for word in ["help", "what can you do", "lifeline"]):
        return SamCommand(
            intent="explain_app",
            target_page="Home",
            confidence=0.82,
            reason="The user asked what the app does.",
            message="LifeLine AI helps people check symptoms, learn about diseases, and decide when to visit a doctor.",
        )

    return SamCommand(
        intent="recommend_feature",
        target_page="Patient Health Checker",
        confidence=0.65,
        reason="The request is unclear, so the safest useful page is the Health Checker.",
        message="I can help you choose a page. If you feel unwell, start with the Health Checker.",
    )
