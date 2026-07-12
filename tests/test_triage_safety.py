from __future__ import annotations

import unittest

from backend.triage_engine import analyze_patient, canonicalize_symptom


class TriageSafetyTests(unittest.TestCase):
    def test_explicit_emergency_signs_cannot_be_downgraded(self) -> None:
        for symptom in (
            "Confusion",
            "Fainting",
            "Stroke signs",
            "Seizure",
            "Severe breathing difficulty",
            "Severe allergic reaction",
            "Blue lips",
        ):
            with self.subTest(symptom=symptom):
                result = analyze_patient({"symptoms": [symptom]}, use_ml=False)
                self.assertEqual(result.risk_level, "Emergency")
                self.assertGreaterEqual(result.score, 70)

    def test_plain_language_danger_phrases_are_understood(self) -> None:
        expectations = {
            "my chest hurts": "chest pain",
            "I can't breathe": "severe breathing difficulty",
            "she passed out": "fainting",
            "his speech is slurred": "stroke signs",
            "her throat is swelling": "severe allergic reaction",
        }
        for phrase, expected in expectations.items():
            with self.subTest(phrase=phrase):
                self.assertEqual(canonicalize_symptom(phrase), expected)

    def test_ambiguous_chest_pain_is_never_self_care(self) -> None:
        result = analyze_patient({"symptoms": ["Chest pain"]}, use_ml=False)
        self.assertEqual(result.risk_level, "Urgent Care")

    def test_plain_sentence_with_high_risk_words_is_not_missed(self) -> None:
        expectations = {
            "is chest pain normal": "Urgent Care",
            "my chest pain is normal right": "Urgent Care",
            "chest pain and confusion is normal": "Emergency",
            "confused and chest hurts": "Emergency",
            "breathing bad": "Urgent Care",
        }
        for phrase, expected_risk in expectations.items():
            with self.subTest(phrase=phrase):
                result = analyze_patient({"symptoms": [phrase]}, use_ml=False)
                self.assertEqual(result.risk_level, expected_risk)

    def test_chest_pain_with_danger_signal_is_emergency(self) -> None:
        result = analyze_patient(
            {"symptoms": ["Chest pain", "Sweating"]}, use_ml=False
        )
        self.assertNotEqual(result.risk_level, "Self-Care")
        warning = analyze_patient(
            {"symptoms": ["Chest pain", "Heart attack warning signs"]}, use_ml=False
        )
        self.assertEqual(warning.risk_level, "Emergency")
        escalated = analyze_patient(
            {"symptoms": ["Chest pain", "Fainting"]}, use_ml=False
        )
        self.assertEqual(escalated.risk_level, "Emergency")

    def test_natural_heart_and_neuro_emergency_phrases_are_caught(self) -> None:
        expectations = {
            "chest pain spreading to my arm": "Heart Warning",
            "chest pain going to jaw": "Heart Warning",
            "crushing chest pressure": "Heart Warning",
            "severe chest pain with sweating": "Heart Warning",
            "chest pain and I feel faint": "Heart Warning",
            "i think i am having a heart attack": "Heart Warning",
            "severe chest pain": "Heart Warning",
            "pressure in chest and sweating": "Heart Warning",
            "lips turning blue": "Respiratory",
            "worst headache of my life": "Neurological",
            "sudden worst headache": "Neurological",
            "weak on one side": "Neurological",
            "one side weakness": "Neurological",
            "cannot speak properly": "Neurological",
            "swollen tongue": "Skin/Allergy",
            "swollen lips and rash": "Skin/Allergy",
            "medicine overdose": "Medication Emergency",
            "took too many pills": "Medication Emergency",
        }
        for phrase, category in expectations.items():
            with self.subTest(phrase=phrase):
                result = analyze_patient({"symptoms": [phrase]}, use_ml=False)
                self.assertEqual(result.risk_level, "Emergency")
                self.assertEqual(result.possible_category, category)

    def test_new_bleeding_phrases_require_same_day_care(self) -> None:
        for phrase in ("black stools", "pregnant and bleeding", "won't stop bleeding"):
            with self.subTest(phrase=phrase):
                result = analyze_patient({"symptoms": [phrase]}, use_ml=False)
                self.assertIn(result.risk_level, {"Urgent Care", "Emergency"})


if __name__ == "__main__":
    unittest.main()
