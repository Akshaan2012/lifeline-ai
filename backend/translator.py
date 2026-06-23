from __future__ import annotations

from functools import lru_cache
from typing import Any


LANGUAGE_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Russian": "ru",
    "German": "de",
    "French": "fr",
    "Spanish": "es",
    "Gaelic": "ga",
    "Sanskrit": "sa",
    "Marathi": "mr",
    "Kannada": "kn",
    "Tamil": "ta",
    "Malayalam": "ml",
    "Telugu": "te",
    "Gujarati": "gu",
    "Bhojpuri": "bho",
    "Mandarin": "zh-CN",
    "Thai": "th",
    "Japanese": "ja",
    "Norwegian": "no",
    "Swedish": "sv",
    "Finnish": "fi",
    "Portuguese": "pt",
    "Romanian": "ro",
    "Italian": "it",
    "Icelandic": "is",
    "Dutch": "nl",
    "Malay": "ms",
    "Swahili": "sw",
    "Afrikaans": "af",
    "Hebrew": "iw",
    "Arabic": "ar",
}

HINDI_FALLBACKS = {
    "LifeLine AI workspace is ready": "\u0932\u093e\u0907\u092b\u0932\u093e\u0907\u0928 \u090f\u0906\u0908 \u0924\u0948\u092f\u093e\u0930 \u0939\u0948",
    "Use Sam or the sidebar to move between tools": "\u091f\u0942\u0932 \u092c\u0926\u0932\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u0938\u0948\u092e \u092f\u093e \u0938\u093e\u0907\u0921\u092c\u093e\u0930 \u0915\u093e \u0909\u092a\u092f\u094b\u0917 \u0915\u0930\u0947\u0902",
    "Smart inside. Simple outside.": "\u0905\u0902\u0926\u0930 \u0938\u094d\u092e\u093e\u0930\u094d\u091f\u0964 \u092c\u093e\u0939\u0930 \u0938\u0930\u0932\u0964",
    "Language": "\u092d\u093e\u0937\u093e",
    "Navigation": "\u0928\u0947\u0935\u093f\u0917\u0947\u0936\u0928",
    "Home": "\u0939\u094b\u092e",
    "Patient Health Checker": "\u0930\u094b\u0917\u0940 \u0938\u094d\u0935\u093e\u0938\u094d\u0925\u094d\u092f \u091c\u093e\u0902\u091a",
    "Disease Q&A Assistant": "\u0930\u094b\u0917 \u092a\u094d\u0930\u0936\u094d\u0928\u094b\u0924\u094d\u0924\u0930 \u0938\u0939\u093e\u092f\u0915",
    "Health & Medicine Q&A": "\u0938\u094d\u0935\u093e\u0938\u094d\u0925\u094d\u092f \u0914\u0930 \u0926\u0935\u093e \u092a\u094d\u0930\u0936\u094d\u0928\u094b\u0924\u094d\u0924\u0930",
    "Doctor Dashboard": "\u0921\u0949\u0915\u094d\u091f\u0930 \u0921\u0948\u0936\u092c\u094b\u0930\u094d\u0921",
    "Scenario Challenge": "\u0938\u094d\u0925\u093f\u0924\u093f \u091a\u0941\u0928\u094c\u0924\u0940",
    "V1 prototype": "\u0935\u0940 1 \u092a\u094d\u0930\u094b\u091f\u094b\u091f\u093e\u0907\u092a",
    "Decision-support prototype. Not a replacement for doctors.": "\u092f\u0939 \u0928\u093f\u0930\u094d\u0923\u092f \u0938\u0939\u093e\u092f\u0924\u093e \u092a\u094d\u0930\u094b\u091f\u094b\u091f\u093e\u0907\u092a \u0939\u0948\u0964 \u092f\u0939 \u0921\u0949\u0915\u094d\u091f\u0930 \u0915\u093e \u0935\u093f\u0915\u0932\u094d\u092a \u0928\u0939\u0940\u0902 \u0939\u0948\u0964",
    "AI health guidance": "\u090f\u0906\u0908 \u0938\u094d\u0935\u093e\u0938\u094d\u0925\u094d\u092f \u092e\u093e\u0930\u094d\u0917\u0926\u0930\u094d\u0936\u0928",
    "A simple health risk and doctor-visit advisor. It helps users check symptoms, learn about diseases, get precautions, and understand when medical help is needed.": "\u090f\u0915 \u0938\u0930\u0932 \u0938\u094d\u0935\u093e\u0938\u094d\u0925\u094d\u092f \u091c\u094b\u0916\u093f\u092e \u0914\u0930 \u0921\u0949\u0915\u094d\u091f\u0930 \u0935\u093f\u091c\u093f\u091f \u0938\u0932\u093e\u0939\u0915\u093e\u0930\u0964 \u092f\u0939 \u0932\u0915\u094d\u0937\u0923 \u091c\u093e\u0902\u091a\u0928\u0947, \u0930\u094b\u0917 \u0938\u092e\u091d\u0928\u0947, \u0938\u093e\u0935\u0927\u093e\u0928\u0940 \u092a\u093e\u0928\u0947 \u0914\u0930 \u091a\u093f\u0915\u093f\u0924\u094d\u0938\u093e \u0938\u0939\u093e\u092f\u0924\u093e \u0915\u092c \u091a\u093e\u0939\u093f\u090f \u092f\u0939 \u0938\u092e\u091d\u0928\u0947 \u092e\u0947\u0902 \u092e\u0926\u0926 \u0915\u0930\u0924\u093e \u0939\u0948\u0964",
    "Prediction": "\u092d\u0935\u093f\u0937\u094d\u092f\u0935\u093e\u0923\u0940",
    "Recommendations": "\u0938\u093f\u092b\u093e\u0930\u093f\u0936\u0947\u0902",
    "Simple language": "\u0938\u0930\u0932 \u092d\u093e\u0937\u093e",
    "Sam bubble assistant": "\u0938\u0948\u092e \u092c\u092c\u0932 \u0938\u0939\u093e\u092f\u0915",
    "Risk Prediction": "\u091c\u094b\u0916\u093f\u092e \u092d\u0935\u093f\u0937\u094d\u092f\u0935\u093e\u0923\u0940",
    "Advanced Advice": "\u0909\u0928\u094d\u0928\u0924 \u0938\u0932\u093e\u0939",
    "Sam Assistant": "\u0938\u0948\u092e \u0938\u0939\u093e\u092f\u0915",
    "Sam assistant": "\u0938\u0948\u092e \u0938\u0939\u093e\u092f\u0915",
    "Self-care, doctor visit, urgent care, or emergency.": "\u0938\u094d\u0935\u092f\u0902 \u0926\u0947\u0916\u092d\u093e\u0932, \u0921\u0949\u0915\u094d\u091f\u0930 \u0935\u093f\u091c\u093f\u091f, \u0924\u0924\u094d\u0915\u093e\u0932 \u0926\u0947\u0916\u092d\u093e\u0932, \u092f\u093e \u0906\u092a\u093e\u0924\u0915\u093e\u0932\u0964",
    "Care steps, prevention, avoid-list, and red flags.": "\u0926\u0947\u0916\u092d\u093e\u0932 \u0915\u0947 \u0915\u0926\u092e, \u092c\u091a\u093e\u0935, \u0915\u093f\u0928 \u091a\u0940\u091c\u094b\u0902 \u0938\u0947 \u092c\u091a\u0928\u093e \u0939\u0948, \u0914\u0930 \u0916\u0924\u0930\u0947 \u0915\u0947 \u0938\u0902\u0915\u0947\u0924\u0964",
    "Click the bottom-right bubble to ask for help.": "\u092e\u0926\u0926 \u092e\u093e\u0902\u0917\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u0928\u0940\u091a\u0947 \u0926\u093e\u0908\u0902 \u0924\u0930\u092b \u0915\u0947 \u092c\u092c\u0932 \u092a\u0930 \u0915\u094d\u0932\u093f\u0915 \u0915\u0930\u0947\u0902\u0964",
    "LOW DANGER": "\u0915\u092e \u0916\u0924\u0930\u093e",
    "MODERATE DANGER": "\u092e\u0927\u094d\u092f\u092e \u0916\u0924\u0930\u093e",
    "HIGH DANGER": "\u0909\u091a\u094d\u091a \u0916\u0924\u0930\u093e",
    "Care Level": "\u0926\u0947\u0916\u092d\u093e\u0932 \u0938\u094d\u0924\u0930",
    "Risk Score": "\u091c\u094b\u0916\u093f\u092e \u0938\u094d\u0915\u094b\u0930",
    "Pattern": "\u092a\u0948\u091f\u0930\u094d\u0928",
    "Timeframe": "\u0938\u092e\u092f \u0938\u0940\u092e\u093e",
    "Self-Care": "\u0938\u094d\u0935\u092f\u0902 \u0926\u0947\u0916\u092d\u093e\u0932",
    "Doctor Visit Recommended": "\u0921\u0949\u0915\u094d\u091f\u0930 \u0938\u0947 \u092e\u093f\u0932\u0928\u093e \u0938\u0941\u091d\u093e\u092f\u093e \u0917\u092f\u093e",
    "Urgent Care": "\u0924\u0924\u094d\u0915\u093e\u0932 \u0926\u0947\u0916\u092d\u093e\u0932",
    "Emergency": "\u0906\u092a\u093e\u0924\u0915\u093e\u0932",
    "Likely health pattern": "\u0938\u0902\u092d\u093e\u0935\u093f\u0924 \u0938\u094d\u0935\u093e\u0938\u094d\u0925\u094d\u092f \u092a\u0948\u091f\u0930\u094d\u0928",
    "Why the app thinks this": "\u090f\u092a \u090f\u0938\u093e \u0915\u094d\u092f\u094b\u0902 \u0938\u094b\u091a\u0924\u093e \u0939\u0948",
    "What to do now": "\u0905\u092d\u0940 \u0915\u094d\u092f\u093e \u0915\u0930\u0947\u0902",
    "Home care support": "\u0918\u0930 \u092a\u0930 \u0926\u0947\u0916\u092d\u093e\u0932",
    "Precautions": "\u0938\u093e\u0935\u0927\u093e\u0928\u093f\u092f\u093e\u0902",
    "What to avoid": "\u0915\u093f\u0928 \u091a\u0940\u091c\u094b\u0902 \u0938\u0947 \u092c\u091a\u0947\u0902",
    "Prevention tips": "\u092c\u091a\u093e\u0935 \u0915\u0947 \u0909\u092a\u093e\u092f",
    "Red Flags": "\u0916\u0924\u0930\u0947 \u0915\u0947 \u0938\u0902\u0915\u0947\u0924",
    "Questions to ask a doctor": "\u0921\u0949\u0915\u094d\u091f\u0930 \u0938\u0947 \u092a\u0942\u091b\u0928\u0947 \u0935\u093e\u0932\u0947 \u0938\u0935\u093e\u0932",
}


def language_name(selected: str) -> str:
    return selected.split(" ", 1)[1] if " " in selected else selected


@lru_cache(maxsize=2000)
def translate_text(text: str, selected_language: str) -> str:
    language = language_name(selected_language)
    target = LANGUAGE_CODES.get(language, "en")
    if target == "en" or not text.strip():
        return text
    if target == "hi" and text in HINDI_FALLBACKS:
        return HINDI_FALLBACKS[text]
    try:
        from deep_translator import GoogleTranslator

        translated = GoogleTranslator(source="auto", target=target).translate(text)
        return translated or text
    except Exception:
        if target == "hi":
            return HINDI_FALLBACKS.get(text, text)
        return text


def translate_items(items: list[str], selected_language: str) -> list[str]:
    return [translate_text(item, selected_language) for item in items]


def translate_answer(answer: dict[str, Any], selected_language: str) -> dict[str, Any]:
    translated = dict(answer)
    for key in ["title", "meaning", "doctor", "source"]:
        if isinstance(translated.get(key), str):
            translated[key] = translate_text(translated[key], selected_language)
    for key in ["symptoms", "precautions", "prevention", "emergency", "what_to_do_now", "avoid", "doctor_questions"]:
        if isinstance(translated.get(key), list):
            translated[key] = translate_items(translated[key], selected_language)
    return translated
