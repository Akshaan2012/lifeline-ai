from types import SimpleNamespace
import unittest

from backend.doctor_summary import build_doctor_summary
from backend.report import generate_health_report_pdf


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

    def test_pdf_report_handles_user_text_with_symbols(self) -> None:
        patient = {
            "patient_name": "Patient <One>",
            "age": 30,
            "gender": "Prefer not to say",
            "symptoms": ["rash < swelling", "nausea & vomiting"],
            "conditions": ["asthma & allergy"],
            "medications": "metformin & aspirin",
            "allergies": "penicillin < severe",
        }
        result = SimpleNamespace(
            risk_level="Urgent Care",
            score=55,
            possible_category="Allergy & skin",
            recommendation="Seek care if rash < swelling worsens.",
            signals=["rash < swelling", "nausea & vomiting"],
        )
        advice = {
            "timeframe": "Today & sooner if worse.",
            "report_summary": "Symptoms include rash < swelling and nausea & vomiting.",
            "doctor_handoff": "Patient reports allergy-like symptoms < 24 hours.",
            "care_steps": ["Call clinic & monitor breathing"],
            "home_care": ["Rest & fluids"],
            "precautions": ["Avoid triggers < known allergy"],
            "avoid": ["Do not mix medicines & alcohol"],
            "red_flags": ["Breathing trouble & swelling"],
            "doctor_questions": ["Could this be allergy & asthma?"],
        }

        pdf = generate_health_report_pdf(patient, result, advice)

        self.assertGreater(len(pdf), 1000)
        self.assertTrue(pdf.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
