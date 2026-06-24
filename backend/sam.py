from __future__ import annotations

from dataclasses import dataclass, asdict
from functools import lru_cache
import os


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

    if any(word in text for word in ["timeline", "history", "past checks", "patient profile"]):
        return SamCommand(
            intent="navigate",
            target_page="Health Timeline",
            confidence=0.94,
            reason="The user asked for patient history, timeline, or profile.",
            message="Open Health Timeline to see saved checks and patient history over time.",
        )
    if any(word in text for word in ["disease q&a", "q&a", "qa", "health question", "medicine question"]):
        return SamCommand(
            intent="navigate",
            target_page="Disease Q&A Assistant",
            confidence=0.94,
            reason="The user asked for the disease or medicine Q&A page.",
            message="Open Health & Medicine Q&A to ask about diseases, symptoms, or medicines.",
        )
    if any(word in text for word in ["safety video", "safety videos", "public health video", "prevention video"]):
        return SamCommand(
            intent="navigate",
            target_page="Safety Videos",
            confidence=0.94,
            reason="The user asked for safety videos or prevention education.",
            message="Open Safety Videos to learn about prevention, precautions, medicine safety, and disease safety.",
        )
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


@lru_cache(maxsize=64)
def _setting(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st

        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return default


def _ai_reply(message: str) -> str | None:
    api_key = _setting("OPENAI_API_KEY")
    if not api_key:
        return None
    model = _setting("OPENAI_MODEL", "gpt-5.4-nano")
    system = (
        "You are Sam, the friendly AI assistant inside LifeLine AI. "
        "Answer any normal question clearly in 2 to 5 short sentences. For health questions, use simple patient-friendly language, "
        "give safe general education, mention red flags when relevant, and never claim to diagnose, prescribe, or replace a doctor. "
        "If emergency symptoms are mentioned, advise urgent local medical help. "
        "You can also guide users to these app pages: Patient Health Checker, Health Timeline, Disease Q&A Assistant, "
        "Medication Safety Checker, Doctor Dashboard, Scenario Challenge, Safety Videos."
    )
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=float(_setting("OPENAI_TIMEOUT_SECONDS", "3.5")))
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": message},
            ],
            max_output_tokens=int(_setting("OPENAI_MAX_OUTPUT_TOKENS", "90")),
        )
        return (response.output_text or "").strip() or None
    except Exception:
        return None


def _wants_navigation(message: str) -> bool:
    text = message.lower()
    return any(word in text for word in ["open", "go to", "take me", "show me", "switch", "page", "button"])


def _wants_explanation(message: str) -> bool:
    text = message.lower().strip()
    question_starts = ("what", "why", "how", "when", "where", "explain", "tell me", "define")
    return text.startswith(question_starts) or "?" in text


def _is_clear_app_request(message: str, command: SamCommand) -> bool:
    if _wants_explanation(message) and command.intent != "explain_app":
        return False
    return command.confidence >= 0.86 and command.intent in {
        "navigate",
        "explain_app",
        "recommend_feature",
    }


@lru_cache(maxsize=256)
def _cached_ai_reply(message: str) -> str | None:
    return _ai_reply(message)


def answer_message(message: str) -> SamCommand:
    clean_message = " ".join(message.strip().split())
    routed = route_message(clean_message)
    if _wants_navigation(clean_message) and routed.target_page:
        return routed
    if _is_clear_app_request(clean_message, routed):
        return routed
    reply = _cached_ai_reply(clean_message.lower())
    if not reply:
        return routed
    return SamCommand(
        intent="ai_answer",
        target_page=routed.target_page,
        confidence=max(routed.confidence, 0.9),
        reason="Sam answered with the configured OpenAI model and kept the best app route as an optional next step.",
        message=reply,
    )
