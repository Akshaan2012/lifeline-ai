from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger(__name__)
_DOTENV_LOADED = False
_LAST_OPENAI_ERROR = ""


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
    return bool(setting("OPENAI_API_KEY")) and not offline_mode()


def last_openai_error() -> str:
    return _LAST_OPENAI_ERROR


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
            # gpt-5.4-nano is a reasoning model: keep effort low so the token
            # budget goes to the actual answer instead of hidden reasoning
            # (a low budget here was silently returning empty text before).
            reasoning={"effort": setting("OPENAI_REASONING_EFFORT", "low")},
            # Keep answers tight so structured JSON does not get truncated.
            text={"verbosity": setting("OPENAI_VERBOSITY", "low")},
            max_output_tokens=max_output_tokens
            or int(setting("OPENAI_MAX_OUTPUT_TOKENS", "700")),
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
