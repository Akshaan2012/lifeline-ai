from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from functools import lru_cache
import json
import os
from pathlib import Path
from threading import RLock
from typing import Any


TRANSLATION_CACHE_PATH = Path("data/translation_cache.json")
_TRANSLATION_MEMORY: dict[str, dict[str, str]] | None = None
_MEMORY_LOCK = RLock()
_PRELOAD_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="translation-preload")
_PRELOAD_TASKS: dict[str, Future[None]] = {}


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


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _offline_mode() -> bool:
    if _truthy(os.getenv("LIFELINE_OFFLINE_MODE", "")):
        return True
    try:
        import streamlit as st
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx(suppress_warning=True) is None:
            return False

        return bool(st.session_state.get("offline_mode")) or _truthy(
            str(st.secrets.get("LIFELINE_OFFLINE_MODE", ""))
        )
    except Exception:
        return False


def language_name(selected: str) -> str:
    return selected.split(" ", 1)[1] if " " in selected else selected


def _memory() -> dict[str, dict[str, str]]:
    global _TRANSLATION_MEMORY
    with _MEMORY_LOCK:
        if _TRANSLATION_MEMORY is None:
            try:
                _TRANSLATION_MEMORY = json.loads(TRANSLATION_CACHE_PATH.read_text(encoding="utf-8"))
            except Exception:
                _TRANSLATION_MEMORY = {}
        return _TRANSLATION_MEMORY


def _save_memory() -> None:
    if _TRANSLATION_MEMORY is None:
        return
    with _MEMORY_LOCK:
        try:
            TRANSLATION_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            TRANSLATION_CACHE_PATH.write_text(
                json.dumps(_TRANSLATION_MEMORY, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass


def _remember(selected_language: str, original: str, translated: str) -> None:
    if translated and translated != original:
        with _MEMORY_LOCK:
            _memory().setdefault(selected_language, {})[original] = translated


def _target_code(selected_language: str) -> str:
    language = language_name(selected_language)
    return LANGUAGE_CODES.get(language, "en")


def _should_skip_translation(text: str, target: str) -> bool:
    return target == "en" or not text.strip() or not any(char.isalpha() for char in text)


@lru_cache(maxsize=64)
def _translator(target: str) -> Any:
    from deep_translator import GoogleTranslator

    return GoogleTranslator(source="auto", target=target)


def _direct_google_batch(texts: list[str], target: str) -> list[str] | None:
    try:
        import requests

        params: list[tuple[str, str]] = [
            ("client", "gtx"),
            ("sl", "auto"),
            ("tl", target),
            ("dt", "t"),
        ]
        params.extend(("q", text) for text in texts)
        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params=params,
            timeout=4,
        )
        response.raise_for_status()
        data = response.json()
        rows = data[0] if isinstance(data, list) and data else []
        if len(rows) == len(texts):
            values = [str(row[0] or texts[index]) for index, row in enumerate(rows)]
            if values:
                return values
    except Exception:
        return None
    return None


@lru_cache(maxsize=1000)
def _translate_batch_cached(items: tuple[str, ...], selected_language: str) -> tuple[str, ...]:
    target = _target_code(selected_language)
    memory = _memory().get(selected_language, {})
    if _offline_mode():
        if target == "hi":
            return tuple(HINDI_FALLBACKS.get(item, item) for item in items)
        return items

    translated: list[str] = list(items)
    pending: list[str] = []
    pending_indexes: list[int] = []
    for index, item in enumerate(items):
        if _should_skip_translation(item, target):
            continue
        if item in memory:
            translated[index] = memory[item]
            continue
        if target == "hi" and item in HINDI_FALLBACKS:
            translated[index] = HINDI_FALLBACKS[item]
            _remember(selected_language, item, translated[index])
            continue
        pending.append(item)
        pending_indexes.append(index)

    if not pending:
        return tuple(translated)

    try:
        batch = _direct_google_batch(pending, target) or _translator(target).translate_batch(pending)
        for index, value in zip(pending_indexes, batch):
            translated[index] = value or items[index]
            _remember(selected_language, items[index], translated[index])
        _save_memory()
    except Exception:
        for index in pending_indexes:
            translated[index] = HINDI_FALLBACKS.get(items[index], items[index]) if target == "hi" else items[index]
    return tuple(translated)


@lru_cache(maxsize=3000)
def translate_text(text: str, selected_language: str) -> str:
    target = _target_code(selected_language)
    if target == "en" or not text.strip():
        return text
    memory = _memory().get(selected_language, {})
    if text in memory:
        return memory[text]
    if target == "hi" and text in HINDI_FALLBACKS:
        _remember(selected_language, text, HINDI_FALLBACKS[text])
        return HINDI_FALLBACKS[text]
    if _should_skip_translation(text, target):
        return text
    if _offline_mode():
        return HINDI_FALLBACKS.get(text, text) if target == "hi" else text
    try:
        translated = _translator(target).translate(text)
        _remember(selected_language, text, translated or text)
        _save_memory()
        return translated or text
    except Exception:
        if target == "hi":
            return HINDI_FALLBACKS.get(text, text)
        return text


def translate_text_cached(text: str, selected_language: str) -> str:
    target = _target_code(selected_language)
    if target == "en" or not text.strip() or _should_skip_translation(text, target):
        return text
    memory = _memory().get(selected_language, {})
    if text in memory:
        return memory[text]
    if target == "hi" and text in HINDI_FALLBACKS:
        return HINDI_FALLBACKS[text]
    if _offline_mode():
        return HINDI_FALLBACKS.get(text, text) if target == "hi" else text
    return text


def translate_items(items: list[str], selected_language: str) -> list[str]:
    return list(_translate_batch_cached(tuple(items), selected_language))


def translate_items_cached(items: list[str], selected_language: str) -> list[str]:
    return [translate_text_cached(item, selected_language) for item in items]


def preload_translations(items: list[str], selected_language: str) -> None:
    unique_items = list(dict.fromkeys(items))
    for index in range(0, len(unique_items), 25):
        translate_items(unique_items[index : index + 25], selected_language)


def preload_translations_async(items: list[str], selected_language: str) -> None:
    target = _target_code(selected_language)
    if target == "en" or _offline_mode():
        return

    task_key = f"{selected_language}:{len(items)}"
    existing = _PRELOAD_TASKS.get(task_key)
    if existing and not existing.done():
        return

    def run_preload() -> None:
        preload_translations(items, selected_language)

    _PRELOAD_TASKS[task_key] = _PRELOAD_EXECUTOR.submit(run_preload)


def translate_answer(answer: dict[str, Any], selected_language: str) -> dict[str, Any]:
    translated = dict(answer)
    string_keys = ["title", "meaning", "doctor", "source", "safety_note"]
    list_keys = ["symptoms", "precautions", "prevention", "emergency", "what_to_do_now", "avoid", "doctor_questions"]
    texts: list[str] = []
    locations: list[tuple[str, int | None]] = []

    for key in string_keys:
        if isinstance(translated.get(key), str):
            texts.append(translated[key])
            locations.append((key, None))
    for key in list_keys:
        if isinstance(translated.get(key), list):
            for index, value in enumerate(translated[key]):
                if isinstance(value, str):
                    texts.append(value)
                    locations.append((key, index))

    translated_texts = list(_translate_batch_cached(tuple(texts), selected_language)) if texts else []
    for location, value in zip(locations, translated_texts):
        key, index = location
        if index is None:
            translated[key] = value
        else:
            translated[key][index] = value
    return translated
