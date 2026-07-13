from __future__ import annotations

import json
import logging
import os
import re
import time
from collections import deque
from functools import lru_cache
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger(__name__)
_DOTENV_LOADED = False
_LAST_OPENAI_ERROR = ""
_OPENAI_CALL_TIMES: deque[float] = deque()


ENVIRONMENT_KEY_NAMES = {
    "development": "OPENAI_API_KEY_DEV",
    "dev": "OPENAI_API_KEY_DEV",
    "testing": "OPENAI_API_KEY_TEST",
    "test": "OPENAI_API_KEY_TEST",
    "production": "OPENAI_API_KEY_PROD",
    "prod": "OPENAI_API_KEY_PROD",
}

IDENTIFIER_PATTERNS = [
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[email removed]"),
    (re.compile(r"\b(?:\+?\d[\d\s().-]{7,}\d)\b"), "[phone or id removed]"),
    (re.compile(r"(?im)\b(patient\s*(?:name|id)|mrn|medical record number|address|contact)\s*[:=]\s*[^,\n;]+"), r"\1: [removed]"),
    (re.compile(r"(?im)\b(?:dob|date of birth)\s*[:=]\s*[^,\n;]+"), "date of birth: [removed]"),
]


def _load_dotenv() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    _DOTENV_LOADED = True
    env_path = Path(".env")
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            clean = line.strip()
            if not clean or clean.startswith("#") or "=" not in clean:
                continue
            key, value = clean.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError as exc:
        LOGGER.warning("Could not read local .env settings: %s", exc)


@lru_cache(maxsize=64)
def setting(name: str, default: str = "") -> str:
    _load_dotenv()
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st

        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return default


def truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def offline_mode() -> bool:
    if truthy(os.getenv("LIFELINE_OFFLINE_MODE", "")):
        return True
    try:
        import streamlit as st

        return bool(st.session_state.get("offline_mode")) or truthy(
            str(st.secrets.get("LIFELINE_OFFLINE_MODE", ""))
        )
    except Exception:
        return False


def openai_enabled() -> bool:
    return bool(provider_api_key()) and not offline_mode()


def last_openai_error() -> str:
    return _LAST_OPENAI_ERROR


def app_environment() -> str:
    return (setting("LIFELINE_ENV", "development") or "development").strip().lower()


def provider_api_key() -> str:
    key_name = ENVIRONMENT_KEY_NAMES.get(app_environment(), "OPENAI_API_KEY_DEV")
    return setting(key_name) or setting("OPENAI_API_KEY")


def provider_model() -> str:
    env = app_environment().upper()
    specific = setting(f"OPENAI_MODEL_{env}")
    return specific or setting("OPENAI_MODEL", "gpt-5.4-nano")


def minimize_patient_identifiers(text: str) -> str:
    minimized = str(text)
    for pattern, replacement in IDENTIFIER_PATTERNS:
        minimized = pattern.sub(replacement, minimized)
    return minimized


def _rate_limit_allows_call() -> bool:
    limit = int(setting("OPENAI_RATE_LIMIT_PER_MINUTE", "30") or "30")
    if limit <= 0:
        return True
    now = time.monotonic()
    while _OPENAI_CALL_TIMES and now - _OPENAI_CALL_TIMES[0] > 60:
        _OPENAI_CALL_TIMES.popleft()
    if len(_OPENAI_CALL_TIMES) >= limit:
        return False
    _OPENAI_CALL_TIMES.append(now)
    return True


def _audit_openai_event(event: str, *, model: str, user_text: str) -> None:
    LOGGER.info(
        "OpenAI event=%s env=%s model=%s prompt_chars=%s",
        event,
        app_environment(),
        model,
        len(user_text),
    )


def openai_text(
    system: str,
    user: str,
    *,
    max_output_tokens: int | None = None,
    timeout_seconds: float | None = None,
) -> str | None:
    global _LAST_OPENAI_ERROR
    if not openai_enabled():
        _LAST_OPENAI_ERROR = "OpenAI is disabled or OPENAI_API_KEY is not configured."
        return None
    if not _rate_limit_allows_call():
        _LAST_OPENAI_ERROR = "OpenAI rate limit reached for this app instance."
        _audit_openai_event("rate_limited", model=provider_model(), user_text=user)
        return None
    try:
        from openai import OpenAI

        model = provider_model()
        safe_user = minimize_patient_identifiers(user)
        client = OpenAI(
            api_key=provider_api_key(),
            timeout=timeout_seconds or float(setting("OPENAI_TIMEOUT_SECONDS", "6")),
        )
        _audit_openai_event("request_started", model=model, user_text=safe_user)
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": safe_user},
            ],
            max_output_tokens=max_output_tokens
            or int(setting("OPENAI_MAX_OUTPUT_TOKENS", "220")),
            store=False,
        )
        output = (response.output_text or "").strip() or None
        _LAST_OPENAI_ERROR = "" if output else "OpenAI returned an empty response."
        return output
    except Exception as exc:
        error_code = getattr(exc, "code", None) or type(exc).__name__
        status_code = getattr(exc, "status_code", None)
        _LAST_OPENAI_ERROR = f"{error_code} ({status_code})" if status_code else str(error_code)
        LOGGER.warning("OpenAI enhancement unavailable: %s", _LAST_OPENAI_ERROR)
        return None


def openai_json(
    system: str,
    user: str,
    *,
    max_output_tokens: int | None = None,
) -> dict[str, Any] | None:
    text = openai_text(system, user, max_output_tokens=max_output_tokens)
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None
