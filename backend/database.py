from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


DB_PATH = Path("data/lifeline_cases.db")


def _setting(name: str) -> str:
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
    if _offline_mode():
        return None
    url = _setting("SUPABASE_URL")
    key = _setting("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception:
        return None


def database_backend() -> str:
    if _offline_mode():
        return "SQLite offline mode"
    return "Supabase" if _supabase_client() else "SQLite local fallback"


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
                raw_data TEXT NOT NULL
            )
            """
        )


def save_case(patient_data: dict[str, Any], triage_result: Any) -> None:
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
    }
    if supabase:
        supabase.table("patient_cases").insert(row).execute()
        return

    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO patient_cases (
                created_at, patient_name, age, symptoms, category, risk_level,
                recommendation, score, raw_data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            ),
        )


def list_cases() -> list[dict[str, Any]]:
    supabase = _supabase_client()
    if supabase:
        response = (
            supabase.table("patient_cases")
            .select("*")
            .order("score", desc=True)
            .order("created_at", desc=True)
            .execute()
        )
        return list(response.data or [])

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
        supabase.table("patient_cases").delete().neq("id", 0).execute()
        return

    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM patient_cases")
