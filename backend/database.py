from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


DB_PATH = Path("data/lifeline_cases.db")


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
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                patient_data.get("patient_name") or "Anonymous",
                int(patient_data.get("age") or 0),
                ", ".join(patient_data.get("symptoms", [])),
                triage_result.possible_category,
                triage_result.risk_level,
                triage_result.recommendation,
                triage_result.score,
                json.dumps(patient_data),
            ),
        )


def list_cases() -> list[dict[str, Any]]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM patient_cases ORDER BY score DESC, created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]
