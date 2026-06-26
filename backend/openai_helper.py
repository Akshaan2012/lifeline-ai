from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=64)
def setting(name: str, default: str = "") -> str:
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
    return bool(setting("OPENAI_API_KEY")) and not offline_mode()


def openai_text(
    system: str,
    user: str,
    *,
    max_output_tokens: int | None = None,
    timeout_seconds: float | None = None,
) -> str | None:
    if not openai_enabled():
        return None
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=setting("OPENAI_API_KEY"),
            timeout=timeout_seconds or float(setting("OPENAI_TIMEOUT_SECONDS", "6")),
        )
        response = client.responses.create(
            model=setting("OPENAI_MODEL", "gpt-5.4-nano"),
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_output_tokens=max_output_tokens
            or int(setting("OPENAI_MAX_OUTPUT_TOKENS", "220")),
        )
        return (response.output_text or "").strip() or None
    except Exception:
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
