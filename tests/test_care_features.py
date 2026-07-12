from __future__ import annotations

import unittest
from datetime import date
from types import SimpleNamespace

from backend.care_features import build_fhir_bundle, reconcile_medications, reminder_status
from backend.followup import evaluate_follow_up
from backend.medication_safety import analyze_medication_safety


class CareFeatureTests(unittest.TestCase):
    def test_duplicate_active_ingredient_is_detected(self) -> None:
        result = reconcile_medications("Crocin, paracetamol")
        self.assertTrue(any("duplicate" in item.lower() for item in result["duplicate_flags"]))

    def test_known_interaction_is_detected(self) -> None:
        result = reconcile_medications("ibuprofen, aspirin")
        self.assertTrue(any("bleeding" in item.lower() for item in result["interaction_flags"]))

    def test_allergy_match_is_detected(self) -> None:
        result = reconcile_medications("aspirin", "aspirin allergy")
        self.assertTrue(result["allergy_flags"])

    def test_common_blood_thinner_brand_interactions_are_detected(self) -> None:
        for medicine_list in ("ibuprofen, Eliquis", "aspirin, Xarelto", "ibuprofen, Plavix"):
            with self.subTest(medicine_list=medicine_list):
                result = reconcile_medications(medicine_list)
                self.assertTrue(any("bleeding" in item.lower() for item in result["interaction_flags"]))

    def test_penicillin_family_allergy_is_detected_for_amoxicillin(self) -> None:
        result = reconcile_medications("amoxicillin", "penicillin allergy")
        self.assertTrue(any("penicillin" in item.lower() for item in result["allergy_flags"]))

    def test_medication_safety_flags_blood_thinner_aliases(self) -> None:
        result = analyze_medication_safety(
            "ibuprofen",
            age=45,
            allergies="",
            conditions=[],
            current_medicines="Eliquis",
            pregnant=False,
        )
        self.assertNotEqual(result.level, "Low caution")
        self.assertTrue(any("blood thinner" in item.lower() or "bleeding" in item.lower() for item in result.caution_flags))

    def test_medication_safety_escalates_possible_overdose_wording(self) -> None:
        result = analyze_medication_safety(
            "paracetamol",
            age=40,
            allergies="",
            conditions=[],
            current_medicines="I took too many pills",
            pregnant=False,
        )
        self.assertEqual(result.level, "Get urgent help now")
        self.assertTrue(any("overdose" in item.lower() or "urgent" in item.lower() for item in result.caution_flags))

    def test_reminder_status(self) -> None:
        self.assertEqual(reminder_status({"due_date": "2026-07-03"}, date(2026, 7, 3)), "Due today")
        self.assertEqual(reminder_status({"due_date": "2026-07-02"}, date(2026, 7, 3)), "Overdue")

    def test_structured_bundle_contains_patient_and_risk(self) -> None:
        result = SimpleNamespace(risk_level="Urgent Care", explanation="Rule explanation")
        bundle = build_fhir_bundle(
            {"patient_name": "Patient 1", "conditions": ["Asthma"], "medications": "salbutamol"},
            result,
        )
        resource_types = [entry["resource"]["resourceType"] for entry in bundle["entry"]]
        self.assertIn("Patient", resource_types)
        self.assertIn("RiskAssessment", resource_types)
        self.assertIn("MedicationStatement", resource_types)

    def test_followup_catches_new_danger_words_after_low_risk_check(self) -> None:
        original = SimpleNamespace(risk_level="Self-Care")
        for note in (
            "swollen tongue now",
            "took too many pills",
            "lips turning blue",
            "one side weakness",
            "cannot speak properly",
        ):
            with self.subTest(note=note):
                result = evaluate_follow_up(original, "Same", note, 1)
                self.assertEqual(result["level"], "Needs faster care")


if __name__ == "__main__":
    unittest.main()
