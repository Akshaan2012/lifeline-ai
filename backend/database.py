from __future__ import annotations

import json
import os
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


DB_PATH = Path("data/lifeline_cases.db")
LAST_DATABASE_ERROR = ""
_SUPABASE_CLIENT: Any | None = None
_SUPABASE_CLIENT_READY = False
_DOTENV_LOADED = False


def _set_database_error(message: str) -> None:
    global LAST_DATABASE_ERROR
    LAST_DATABASE_ERROR = message


def database_error_message() -> str:
    return LAST_DATABASE_ERROR


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
    except Exception as exc:
        _set_database_error(f"Could not read .env: {exc}")


def _setting(name: str) -> str:
    _load_dotenv()
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st

        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _offline_mode() -> bool:
    if _truthy(os.getenv("LIFELINE_OFFLINE_MODE", "")):
        return True
    try:
        import streamlit as st

        return bool(st.session_state.get("offline_mode")) or _truthy(
            str(st.secrets.get("LIFELINE_OFFLINE_MODE", ""))
        )
    except Exception:
        return False


def _supabase_client() -> Any | None:
    global _SUPABASE_CLIENT, _SUPABASE_CLIENT_READY
    if _offline_mode():
        return None
    if _SUPABASE_CLIENT_READY:
        return _SUPABASE_CLIENT
    url = _setting("SUPABASE_URL")
    key = _setting("SUPABASE_ANON_KEY")
    if not url or not key:
        _set_database_error("Supabase is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY to Streamlit secrets or a local .env file.")
        _SUPABASE_CLIENT_READY = True
        return None
    try:
        from supabase import create_client

        _SUPABASE_CLIENT = create_client(url, key)
        _SUPABASE_CLIENT_READY = True
        return _SUPABASE_CLIENT
    except Exception as exc:
        _set_database_error(f"Could not connect to Supabase: {exc}")
        _SUPABASE_CLIENT_READY = True
        return None


def _supabase_configured() -> bool:
    return bool(_setting("SUPABASE_URL") and _setting("SUPABASE_ANON_KEY"))


def database_backend() -> str:
    if _offline_mode():
        return "SQLite offline mode"
    return "Supabase" if _supabase_client() else "SQLite local fallback"


def supabase_is_configured() -> bool:
    """Return whether this deployment can authenticate clinic staff."""
    return _supabase_configured()


def sign_in_staff(email: str, password: str) -> tuple[bool, str]:
    """Sign in and accept only a server-assigned staff role."""
    client = _supabase_client()
    if client is None:
        return False, "Clinic sign-in is not configured on this deployment."
    try:
        response = client.auth.sign_in_with_password(
            {"email": email.strip(), "password": password}
        )
        user = getattr(response, "user", None)
        metadata = getattr(user, "app_metadata", {}) or {}
        if metadata.get("role") != "staff":
            client.auth.sign_out()
            return False, "This account does not have clinic staff access."
        return True, "Signed in."
    except Exception:
        return False, "Sign-in failed. Check the email and password."


def current_staff_user() -> dict[str, str] | None:
    """Return a minimal staff identity without exposing session tokens."""
    client = _supabase_client()
    if client is None:
        return None
    try:
        session = client.auth.get_session()
        user = getattr(session, "user", None)
        metadata = getattr(user, "app_metadata", {}) or {}
        if user is None or metadata.get("role") != "staff":
            return None
        return {
            "id": str(getattr(user, "id", "")),
            "email": str(getattr(user, "email", "")),
        }
    except Exception:
        return None


def sign_out_staff() -> None:
    client = _supabase_client()
    if client is not None:
        try:
            client.auth.sign_out()
        except Exception:
            pass


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS patient_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                patient_name TEXT,
                age INTEGER,
                symptoms TEXT NOT NULL,
                category TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                score INTEGER NOT NULL,
                raw_data TEXT NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'New',
                doctor_notes TEXT NOT NULL DEFAULT ''
                ,share_code TEXT
                ,patient_consent INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        existing_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(patient_cases)").fetchall()
        }
        if "review_status" not in existing_columns:
            conn.execute(
                "ALTER TABLE patient_cases ADD COLUMN review_status TEXT NOT NULL DEFAULT 'New'"
            )
        if "doctor_notes" not in existing_columns:
            conn.execute(
                "ALTER TABLE patient_cases ADD COLUMN doctor_notes TEXT NOT NULL DEFAULT ''"
            )
        if "share_code" not in existing_columns:
            conn.execute("ALTER TABLE patient_cases ADD COLUMN share_code TEXT")
        if "patient_consent" not in existing_columns:
            conn.execute(
                "ALTER TABLE patient_cases ADD COLUMN patient_consent INTEGER NOT NULL DEFAULT 0"
            )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS patient_cases_share_code_idx ON patient_cases (share_code)"
        )


def _new_share_code() -> str:
    return f"LL-{secrets.token_hex(6).upper()}"


def save_case(patient_data: dict[str, Any], triage_result: Any) -> str:
    share_code = _new_share_code()
    supabase = _supabase_client()
    row = {
        "created_at": datetime.now().isoformat(timespec="minutes"),
        "patient_name": patient_data.get("patient_name") or "Anonymous",
        "age": int(patient_data.get("age") or 0),
        "symptoms": ", ".join(patient_data.get("symptoms", [])),
        "category": triage_result.possible_category,
        "risk_level": triage_result.risk_level,
        "recommendation": triage_result.recommendation,
        "score": int(triage_result.score),
        "raw_data": patient_data,
        "review_status": "New",
        "doctor_notes": "",
        "share_code": share_code,
        "patient_consent": True,
    }
    if supabase:
        try:
            supabase.table("patient_cases").insert(row).execute()
            _set_database_error("")
            return share_code
        except Exception:
            legacy_row = {
                key: value
                for key, value in row.items()
                if key not in {"review_status", "doctor_notes", "share_code", "patient_consent"}
            }
            try:
                supabase.table("patient_cases").insert(legacy_row).execute()
                _set_database_error("")
                return ""
            except Exception as exc:
                _set_database_error(str(exc))
                if _supabase_configured():
                    return ""

    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO patient_cases (
                created_at, patient_name, age, symptoms, category, risk_level,
                recommendation, score, raw_data, review_status, doctor_notes,
                share_code, patient_consent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["created_at"],
                row["patient_name"],
                row["age"],
                row["symptoms"],
                row["category"],
                row["risk_level"],
                row["recommendation"],
                row["score"],
                json.dumps(row["raw_data"]),
                row["review_status"],
                row["doctor_notes"],
                row["share_code"],
                1,
            ),
        )
    return share_code


def get_case_by_share_code(share_code: str) -> dict[str, Any] | None:
    code = share_code.strip().upper()
    if not code:
        return None
    supabase = _supabase_client()
    if supabase:
        try:
            # Use a narrowly-scoped RPC instead of granting anonymous SELECT
            # access to the entire patient table.
            response = supabase.rpc(
                "get_patient_case_by_share_code", {"input_code": code}
            ).execute()
            return dict(response.data[0]) if response.data else None
        except Exception as exc:
            _set_database_error(str(exc))
            if _supabase_configured():
                return None
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT created_at, patient_name, risk_level, review_status,
                   doctor_notes, share_code
            FROM patient_cases WHERE share_code = ? AND patient_consent = 1
            """,
            (code,),
        ).fetchone()
    return dict(row) if row else None


def list_cases() -> list[dict[str, Any]]:
    supabase = _supabase_client()
    if supabase:
        try:
            response = (
                supabase.table("patient_cases")
                .select("*")
                .order("score", desc=True)
                .order("created_at", desc=True)
                .execute()
            )
            _set_database_error("")
            return list(response.data or [])
        except Exception as exc:
            _set_database_error(str(exc))
            if _supabase_configured():
                return []

    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM patient_cases ORDER BY score DESC, created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def clear_cases() -> None:
    supabase = _supabase_client()
    if supabase:
        try:
            supabase.table("patient_cases").delete().neq("id", 0).execute()
            _set_database_error("")
            return
        except Exception as exc:
            _set_database_error(str(exc))
            if _supabase_configured():
                return

    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM patient_cases")


def delete_patient_cases(patient_name: str) -> None:
    name = patient_name or "Anonymous"
    supabase = _supabase_client()
    if supabase:
        try:
            supabase.table("patient_cases").delete().eq("patient_name", name).execute()
            _set_database_error("")
            return
        except Exception as exc:
            _set_database_error(str(exc))
            if _supabase_configured():
                return

    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM patient_cases WHERE patient_name = ?", (name,))


def update_case_review(case_id: int | str, review_status: str, doctor_notes: str) -> bool:
    supabase = _supabase_client()
    if supabase:
        try:
            supabase.table("patient_cases").update(
                {"review_status": review_status, "doctor_notes": doctor_notes}
            ).eq("id", case_id).execute()
            return True
        except Exception:
            if _supabase_configured():
                _set_database_error("Supabase case review update failed. Check the patient_cases table schema and RLS policies.")
                return False
            return False

    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE patient_cases
            SET review_status = ?, doctor_notes = ?
            WHERE id = ?
            """,
            (review_status, doctor_notes, case_id),
        )
    return True
