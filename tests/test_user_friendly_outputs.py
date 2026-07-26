from types import SimpleNamespace
import unittest

from backend.doctor_summary import build_doctor_summary
from backend.followup import evaluate_follow_up
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
        self.assertIn("decision-support risk level", summary)
        self.assertIn("possible symptom pattern", summary)
        self.assertIn("not a diagnosis or prescription", summary)

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

    def test_pdf_report_tolerates_partial_advice(self) -> None:
        patient = {"symptoms": ["Fever"], "conditions": []}
        result = SimpleNamespace(
            risk_level="Doctor Visit Recommended",
            score=30,
            possible_category="General Health",
            recommendation="Book a doctor visit.",
            signals=["Symptoms should be checked."],
        )

        pdf = generate_health_report_pdf(patient, result, {})

        self.assertGreater(len(pdf), 1000)
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_doctor_summary_tolerates_partial_advice(self) -> None:
        patient = {"symptoms": ["Fever"], "conditions": []}
        result = SimpleNamespace(
            risk_level="Doctor Visit Recommended",
            score=30,
            possible_category="General Health",
            recommendation="Book a doctor visit.",
        )

        summary = build_doctor_summary(patient, result, {})

        self.assertIn("Recommended timeframe: not provided", summary)
        self.assertIn("not a diagnosis or prescription", summary)

    def test_doctor_summary_accepts_saved_text_lists(self) -> None:
        patient = {
            "symptoms": "Fever, cough",
            "conditions": "Asthma; Diabetes",
        }
        result = SimpleNamespace(
            risk_level="Doctor Visit Recommended",
            score=30,
            possible_category="General Health",
            recommendation="Book a doctor visit.",
        )

        summary = build_doctor_summary(patient, result, {"timeframe": "Today."})

        self.assertIn("reports symptoms for not provided day(s): Fever, cough.", summary)
        self.assertIn("Existing conditions: Asthma, Diabetes.", summary)
        self.assertNotIn("F, e, v, e, r", summary)

    def test_pdf_report_accepts_saved_text_lists(self) -> None:
        patient = {"symptoms": "Fever, cough", "conditions": "Asthma; Diabetes"}
        result = SimpleNamespace(
            risk_level="Doctor Visit Recommended",
            score=30,
            possible_category="General Health",
            recommendation="Book a doctor visit.",
            signals=["Symptoms should be checked."],
        )

        pdf = generate_health_report_pdf(patient, result, {})

        self.assertGreater(len(pdf), 1000)
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_outputs_accept_restored_result_dicts(self) -> None:
        patient = {"symptoms": "Fever, cough", "conditions": "Asthma"}
        result = {
            "risk_level": "Doctor Visit Recommended",
            "score": 30,
            "possible_category": "General Health",
            "recommendation": "Book a doctor visit.",
            "signals": "Fever should be watched, cough should be checked",
        }

        summary = build_doctor_summary(patient, result, {"timeframe": "Today."})
        pdf = generate_health_report_pdf(patient, result, {})
        followup = evaluate_follow_up(result, "Same", "No new danger signs", 24)

        self.assertIn("Doctor Visit Recommended (30/100)", summary)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertEqual(followup["level"], "Doctor review is safer")

    def test_summary_preserves_zero_duration_and_clamps_score(self) -> None:
        patient = {
            "age": None,
            "gender": None,
            "duration_days": 0,
            "pain_level": 0,
            "symptoms": ["COPD flare"],
            "conditions": ["COPD"],
            "medications": None,
            "allergies": None,
        }
        result = {
            "risk_level": "",
            "score": 150,
            "possible_category": "",
            "recommendation": "",
        }

        summary = build_doctor_summary(patient, result, {})
        pdf = generate_health_report_pdf(patient, result, {})

        self.assertIn("age not provided years old", summary)
        self.assertIn("reports symptoms for 0 day(s): COPD flare", summary)
        self.assertIn("Pain level: 0/10", summary)
        self.assertIn("(100/100)", summary)
        self.assertNotIn("None", summary)
        self.assertTrue(pdf.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
