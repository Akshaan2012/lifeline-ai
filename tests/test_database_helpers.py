from __future__ import annotations

import unittest

from backend.database import MAX_DOCTOR_NOTE_CHARS, REVIEW_STATUSES, normalize_doctor_notes, normalize_review_status, normalize_share_code


class DatabaseHelperTests(unittest.TestCase):
    def test_share_code_normalization_accepts_common_user_typing(self) -> None:
        self.assertEqual(normalize_share_code("ll-1a2b3c4d5e6f"), "LL-1A2B3C4D5E6F")
        self.assertEqual(normalize_share_code(" LL 1a2b 3c4d5e6f "), "LL-1A2B3C4D5E6F")

    def test_review_status_falls_back_to_new_if_unrecognized(self) -> None:
        self.assertEqual(normalize_review_status("Book appointment"), "Book appointment")
        self.assertEqual(normalize_review_status("Delete this case"), "New")

    def test_review_statuses_keep_ui_order(self) -> None:
        self.assertEqual(
            REVIEW_STATUSES,
            ("New", "Reviewed", "Book appointment", "Seek urgent care", "Resolved"),
        )

    def test_doctor_notes_are_patient_visible_and_kept_short(self) -> None:
        messy = "  Please   book\n\nappointment.  " + ("x" * 2000)
        clean = normalize_doctor_notes(messy)

        self.assertTrue(clean.startswith("Please book appointment."))
        self.assertLessEqual(len(clean), MAX_DOCTOR_NOTE_CHARS)
        self.assertNotIn("\n", clean)


if __name__ == "__main__":
    unittest.main()
