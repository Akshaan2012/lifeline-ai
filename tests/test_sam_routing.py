from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
