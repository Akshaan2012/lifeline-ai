from types import SimpleNamespace
import unittest

from backend.doctor_summary import build_doctor_summary


class UserFriendlyOutputTests(unittest.TestCase):
    def test_doctor_summary_keeps_medicines_and_allergies_separate(self) -> None:
        patient = {
            "patient_name": "Patient 1",
            "age": 30,
            "gender": "Prefer not to say",
            "duration_days": 2,
            "pain_level": 4,
            "symptoms": ["Fever"],
            "conditions": [],
            "medications": "metformin",
            "allergies": "penicillin",
        }
        result = SimpleNamespace(
            risk_level="Doctor Visit Recommended",
            score=30,
            possible_category="General symptoms",
            recommendation="Contact a doctor.",
        )
        advice = {"timeframe": "Within 24 hours.", "risk_summary": "Review advised."}

        summary = build_doctor_summary(patient, result, advice)

        self.assertIn("Current medicines: metformin", summary)
        self.assertIn("Allergies: penicillin", summary)


if __name__ == "__main__":
    unittest.main()
