from __future__ import annotations

import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from backend.care_features import build_fhir_bundle, reconcile_medications, reminder_status, safe_fhir_id, split_list_items
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

    def test_medication_safety_accepts_text_conditions_and_age(self) -> None:
        result = analyze_medication_safety(
            "ibuprofen",
            age="not entered",
            allergies="",
            conditions="kidney disease, high blood pressure",
            current_medicines="",
            pregnant=False,
        )

        self.assertNotEqual(result.level, "Low caution")
        self.assertTrue(any("kidney" in item.lower() or "blood pressure" in item.lower() for item in result.caution_flags))

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

    def test_medication_safety_escalates_overdose_wording_in_medicine_name(self) -> None:
        for medicine_name in ("too much paracetamol", "ibuprofen extra dose"):
            with self.subTest(medicine_name=medicine_name):
                result = analyze_medication_safety(
                    medicine_name,
                    age=40,
                    allergies="",
                    conditions=[],
                    current_medicines="",
                    pregnant=False,
                )

                self.assertEqual(result.level, "Get urgent help now")
                self.assertTrue(any("overdose" in item.lower() or "urgent" in item.lower() for item in result.caution_flags))

    def test_medication_ai_enhancement_preserves_local_safety_flags(self) -> None:
        ai_payload = {
            "summary": "Polished summary.",
            "key_points": "read the label, ask a pharmacist",
            "caution_flags": ["General caution only."],
            "what_to_do": "call poison control, keep the bottle nearby",
            "emergency_signs": ["Feeling very unwell."],
            "questions": "What should I watch for?",
        }

        with patch("backend.medication_safety.ai_json", return_value=ai_payload):
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
        self.assertTrue(any("accidental overdose" in item.lower() for item in result.emergency_signs))
        self.assertIn("read the label", result.key_points)

    def test_reminder_status(self) -> None:
        self.assertEqual(reminder_status({"due_date": "2026-07-03"}, date(2026, 7, 3)), "Due today")
        self.assertEqual(reminder_status({"due_date": "2026-07-02"}, date(2026, 7, 3)), "Overdue")
        self.assertEqual(reminder_status({"due_date": "not a date"}, date(2026, 7, 3)), "Unscheduled")
        self.assertEqual(reminder_status({"due_date": "2026-07-02", "completed": True}, date(2026, 7, 3)), "Completed")
        self.assertEqual(reminder_status({"due_date": "not a date", "completed": True}, date(2026, 7, 3)), "Completed")

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

    def test_structured_bundle_exports_allergies_separately(self) -> None:
        bundle = build_fhir_bundle(
            {
                "patient_name": "Patient 1",
                "allergies": "penicillin; peanuts",
                "conditions": [],
                "medications": "",
            }
        )
        allergies = [
            entry["resource"]
            for entry in bundle["entry"]
            if entry["resource"]["resourceType"] == "AllergyIntolerance"
        ]

        self.assertEqual([item["code"]["text"] for item in allergies], ["penicillin", "peanuts"])
        self.assertTrue(all(item["patient"]["reference"] == "Patient/Patient-1" for item in allergies))

    def test_fhir_patient_id_is_safe_for_names_with_symbols(self) -> None:
        self.assertEqual(safe_fhir_id("Jane Doe / Child #1"), "Jane-Doe-Child-1")
        self.assertLessEqual(len(safe_fhir_id("x" * 100)), 64)

        bundle = build_fhir_bundle({"patient_name": "Jane Doe / Child #1", "conditions": ["Asthma"]})
        patient = bundle["entry"][0]["resource"]
        condition = bundle["entry"][1]["resource"]

        self.assertEqual(patient["id"], "Jane-Doe-Child-1")
        self.assertEqual(condition["subject"]["reference"], "Patient/Jane-Doe-Child-1")

    def test_structured_bundle_accepts_text_conditions(self) -> None:
        bundle = build_fhir_bundle({"patient_name": "Patient 1", "conditions": "Asthma, Diabetes"})
        conditions = [
            entry["resource"]["code"]["text"]
            for entry in bundle["entry"]
            if entry["resource"]["resourceType"] == "Condition"
        ]

        self.assertEqual(conditions, ["Asthma", "Diabetes"])

    def test_split_list_items_accepts_saved_text_and_missing_values(self) -> None:
        self.assertEqual(split_list_items("Fever, cough\nfatigue; chills"), ["Fever", "cough", "fatigue", "chills"])
        self.assertEqual(split_list_items(("Asthma", " Diabetes ")), ["Asthma", "Diabetes"])
        self.assertEqual(split_list_items(None), [])

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
