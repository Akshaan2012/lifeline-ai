from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


MODEL_PATH = Path("models/triage_model.joblib")
MODEL_VERSION = 3
LABELS = ["Self-Care", "Doctor Visit Recommended", "Urgent Care", "Emergency"]
SYMPTOM_FEATURES = [
    "fever",
    "high fever",
    "cough",
    "shortness of breath",
    "severe breathing difficulty",
    "chest pain",
    "sweating",
    "severe headache",
    "confusion",
    "stroke signs",
    "severe stomach pain",
    "persistent vomiting",
    "frequent urination",
    "excessive thirst",
    "rash",
    "severe allergic reaction",
]


def _selected_symptoms(data: dict[str, Any]) -> set[str]:
    return {str(item).strip().lower() for item in data.get("symptoms", [])}


def patient_to_features(data: dict[str, Any]) -> list[float]:
    symptoms = _selected_symptoms(data)
    values: list[float] = [
        float(data.get("age") or 0),
        float(data.get("duration_days") or 0),
        float(data.get("pain_level") or 0),
        float(data.get("temperature") or 37.0),
        float(data.get("heart_rate") or 80),
        float(data.get("systolic_bp") or 120),
        float(data.get("diastolic_bp") or 80),
        float(data.get("oxygen") or 98),
        float(len(data.get("conditions", []))),
    ]
    values.extend(1.0 if symptom in symptoms else 0.0 for symptom in SYMPTOM_FEATURES)
    return values


def _label_from_score(score: int) -> str:
    if score >= 70:
        return "Emergency"
    if score >= 45:
        return "Urgent Care"
    if score >= 22:
        return "Doctor Visit Recommended"
    return "Self-Care"


def _synthetic_score(data: dict[str, Any]) -> int:
    symptoms = _selected_symptoms(data)
    score = 0
    score += 60 if {"chest pain", "severe breathing difficulty", "stroke signs", "confusion", "severe allergic reaction"}.intersection(symptoms) else 0
    score += 25 if {"shortness of breath", "high fever", "severe headache", "persistent vomiting", "severe stomach pain"}.intersection(symptoms) else 0
    score += 10 if data["age"] >= 65 else 0
    score += 10 if data["duration_days"] >= 7 else 0
    score += 18 if data["pain_level"] >= 8 else 8 if data["pain_level"] >= 5 else 0
    score += 22 if data["temperature"] >= 39.4 else 8 if data["temperature"] >= 38 else 0
    score += 45 if data["oxygen"] < 90 else 25 if data["oxygen"] < 94 else 0
    score += 14 if data["heart_rate"] < 50 or data["heart_rate"] > 120 else 0
    score += 35 if data["systolic_bp"] >= 180 or data["diastolic_bp"] >= 120 else 8 if data["systolic_bp"] >= 140 or data["diastolic_bp"] >= 90 else 0
    score += 10 if data.get("conditions") else 0
    score += 22 if len({"frequent urination", "excessive thirst", "blurred vision", "fatigue"}.intersection(symptoms)) >= 3 else 0
    return min(score, 100)


def _generate_training_data(rows: int = 900) -> tuple[np.ndarray, np.ndarray]:
    random.seed(42)
    x_rows: list[list[float]] = []
    y_rows: list[str] = []
    for _ in range(rows):
        symptom_count = random.randint(1, 6)
        symptoms = random.sample(SYMPTOM_FEATURES, symptom_count)
        data = {
            "age": random.randint(1, 90),
            "duration_days": random.randint(0, 14),
            "pain_level": random.randint(0, 10),
            "temperature": round(random.uniform(36.1, 40.3), 1),
            "heart_rate": random.randint(48, 135),
            "systolic_bp": random.randint(90, 190),
            "diastolic_bp": random.randint(55, 125),
            "oxygen": random.randint(88, 100),
            "conditions": ["condition"] * random.randint(0, 2),
            "symptoms": symptoms,
        }
        x_rows.append(patient_to_features(data))
        y_rows.append(_label_from_score(_synthetic_score(data)))
    return np.array(x_rows), np.array(y_rows)


def train_or_load_model() -> Pipeline:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists():
        artifact = joblib.load(MODEL_PATH)
        if isinstance(artifact, dict) and artifact.get("version") == MODEL_VERSION:
            return artifact["model"]
    x_train, y_train = _generate_training_data()
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("forest", RandomForestClassifier(n_estimators=120, random_state=42, class_weight="balanced")),
        ]
    )
    model.fit(x_train, y_train)
    joblib.dump({"version": MODEL_VERSION, "model": model}, MODEL_PATH)
    return model


def predict_with_model(data: dict[str, Any]) -> dict[str, Any]:
    model = train_or_load_model()
    features = np.array([patient_to_features(data)])
    prediction = str(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0]
    classes = list(model.classes_)
    confidence = float(max(probabilities))
    return {
        "prediction": prediction,
        "confidence": round(confidence, 2),
        "probabilities": {classes[index]: round(float(value), 2) for index, value in enumerate(probabilities)},
    }
