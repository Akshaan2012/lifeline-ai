from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend import database
from backend.database import MAX_DOCTOR_NOTE_CHARS, REVIEW_STATUSES, database_error_message, get_case_by_share_code, init_db, normalize_doctor_notes, normalize_review_status, normalize_share_code, safe_case_age, safe_case_score, update_case_review, valid_share_code


class DatabaseHelperTests(unittest.TestCase):
    def test_share_code_normalization_accepts_common_user_typing(self) -> None:
        self.assertEqual(normalize_share_code("ll-1a2b3c4d5e6f"), "LL-1A2B3C4D5E6F")
        self.assertEqual(normalize_share_code(" LL 1a2b 3c4d5e6f "), "LL-1A2B3C4D5E6F")

    def test_share_code_validation_rejects_bad_codes_before_lookup(self) -> None:
        self.assertTrue(valid_share_code("ll-1a2b3c4d5e6f"))
        self.assertFalse(valid_share_code(""))
        self.assertFalse(valid_share_code("LL-123"))
        self.assertFalse(valid_share_code("LL-1A2B3C4D5E6Z"))
        with patch("backend.database._supabase_client") as supabase_client:
            self.assertIsNone(get_case_by_share_code("LL-123"))
            supabase_client.assert_not_called()

    def test_review_status_falls_back_to_new_if_unrecognized(self) -> None:
        self.assertEqual(normalize_review_status("Book appointment"), "Book appointment")
        self.assertEqual(normalize_review_status("Delete this case"), "New")

    def test_review_statuses_keep_ui_order(self) -> None:
        self.assertEqual(
            REVIEW_STATUSES,
            ("New", "Reviewed", "Book appointment", "Seek urgent care", "Resolved"),
        )

    def test_case_age_is_safe_for_saved_or_imported_values(self) -> None:
        self.assertEqual(safe_case_age("42"), 42)
        self.assertEqual(safe_case_age("not entered"), 0)
        self.assertEqual(safe_case_age(-5), 0)
        self.assertEqual(safe_case_age(150), 120)

    def test_case_score_is_safe_for_saved_or_imported_values(self) -> None:
        self.assertEqual(safe_case_score("55"), 55)
        self.assertEqual(safe_case_score("not entered"), 0)
        self.assertEqual(safe_case_score(-5), 0)
        self.assertEqual(safe_case_score(150), 100)

    def test_doctor_notes_are_patient_visible_and_kept_short(self) -> None:
        messy = "  Please   book\n\nappointment.  " + ("x" * 2000)
        clean = normalize_doctor_notes(messy)

        self.assertTrue(clean.startswith("Please book appointment."))
        self.assertLessEqual(len(clean), MAX_DOCTOR_NOTE_CHARS)
        self.assertNotIn("\n", clean)

    def test_local_review_update_reports_missing_case(self) -> None:
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            with patch.object(database, "DB_PATH", Path(tmp) / "cases.db"):
                with patch("backend.database._supabase_client", return_value=None):
                    init_db()

                    self.assertFalse(update_case_review(999, "Reviewed", "No matching case."))
                    self.assertIn("did not match", database_error_message())

    def test_supabase_review_update_requires_matching_row(self) -> None:
        class FakeUpdate:
            def eq(self, *_args):
                return self

            def select(self, *_args):
                return self

            def execute(self):
                return SimpleNamespace(data=[])

        class FakeTable:
            def update(self, *_args):
                return FakeUpdate()

        class FakeClient:
            def table(self, *_args):
                return FakeTable()

        with patch("backend.database._supabase_client", return_value=FakeClient()):
            self.assertFalse(update_case_review(999, "Reviewed", "No matching case."))
            self.assertIn("did not match", database_error_message())


if __name__ == "__main__":
    unittest.main()
