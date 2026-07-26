from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.sam import answer_message


class SamRoutingTests(unittest.TestCase):
    def test_patient_workspace_does_not_offer_doctor_dashboard(self) -> None:
        command = answer_message(
            "open doctor dashboard",
            available_pages=[
                "Home",
                "Patient Health Checker",
                "Health Timeline",
                "Disease Q&A Assistant",
            ],
        )

        self.assertEqual(command.target_page, "Health Timeline")
        self.assertIn("not available", command.message.lower())

    def test_professional_workspace_can_offer_doctor_dashboard(self) -> None:
        command = answer_message(
            "open doctor dashboard",
            available_pages=["Home", "Doctor Dashboard", "Clinic Pilot Plan"],
        )

        self.assertEqual(command.target_page, "Doctor Dashboard")

    def test_danger_question_uses_local_safety_route(self) -> None:
        command = answer_message(
            "is chest pain and confusion normal",
            available_pages=["Home", "Patient Health Checker", "Disease Q&A Assistant"],
        )

        self.assertEqual(command.intent, "safety_route")
        self.assertEqual(command.target_page, "Patient Health Checker")
        self.assertIn("warning sign", command.message.lower())
        self.assertIn("emergency", command.message.lower())

    def test_overdose_wording_uses_local_safety_route(self) -> None:
        command = answer_message("i took too many pills what should i do")

        self.assertEqual(command.intent, "safety_route")
        self.assertEqual(command.target_page, "Patient Health Checker")
        self.assertIn("overdose", command.message.lower())

    def test_patient_ai_prompt_omits_clinic_only_pages(self) -> None:
        captured = {}

        def fake_ai_text(system, *_args, **_kwargs):
            captured["system"] = system
            return "Here are the patient tools you can use."

        with patch("backend.sam.offline_mode", return_value=False):
            with patch("backend.sam.ai_text", side_effect=fake_ai_text):
                answer_message(
                    "what tools are available for me",
                    available_pages=[
                        "Home",
                        "Patient Health Checker",
                        "Health Timeline",
                        "Disease Q&A Assistant",
                    ],
                )

        self.assertIn("Patient Health Checker", captured["system"])
        self.assertNotIn("Doctor Dashboard", captured["system"])
        self.assertNotIn("Clinic Pilot Plan", captured["system"])

    def test_professional_ai_prompt_can_include_staff_pages(self) -> None:
        captured = {}

        def fake_ai_text(system, *_args, **_kwargs):
            captured["system"] = system
            return "Here are the clinic tools you can use."

        with patch("backend.sam.offline_mode", return_value=False):
            with patch("backend.sam.ai_text", side_effect=fake_ai_text):
                answer_message(
                    "what tools are available for clinic work",
                    available_pages=["Home", "Doctor Dashboard", "Clinic Pilot Plan"],
                )

        self.assertIn("Doctor Dashboard", captured["system"])
        self.assertIn("Clinic Pilot Plan", captured["system"])


if __name__ == "__main__":
    unittest.main()
