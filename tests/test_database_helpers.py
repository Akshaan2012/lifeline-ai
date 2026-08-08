from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend import database
from backend.database import MAX_CASE_TEXT_CHARS, MAX_DOCTOR_NOTE_CHARS, REVIEW_STATUSES, clear_cases, database_error_message, delete_patient_cases, get_case_by_share_code, init_db, normalize_doctor_notes, normalize_patient_name, normalize_review_status, normalize_share_code, safe_case_age, safe_case_score, safe_case_text, save_case, update_case_review, valid_share_code


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

    def test_case_text_is_clean_and_bounded_before_save(self) -> None:
        self.assertEqual(safe_case_text("  Book\n\nvisit  "), "Book visit")
        self.assertEqual(safe_case_text(None, "Review recommended"), "Review recommended")
        self.assertEqual(len(safe_case_text("x" * 3000)), MAX_CASE_TEXT_CHARS)

    def test_patient_name_is_clean_for_dashboard_grouping(self) -> None:
        self.assertEqual(normalize_patient_name("  Patient   001  "), "Patient 001")
        self.assertEqual(normalize_patient_name("   "), "Anonymous")
        self.assertEqual(normalize_patient_name(None), "Anonymous")
        self.assertEqual(len(normalize_patient_name("x" * 200)), 120)

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

    def test_supabase_clear_cases_reports_delete_failure(self) -> None:
        class FakeDelete:
            def neq(self, *_args):
                return self

            def execute(self):
                raise RuntimeError("delete denied")

        class FakeTable:
            def delete(self):
                return FakeDelete()

        class FakeClient:
            def table(self, *_args):
                return FakeTable()

        with patch("backend.database._supabase_client", return_value=FakeClient()):
            with patch("backend.database._supabase_configured", return_value=True):
                self.assertFalse(clear_cases())

        self.assertIn("delete denied", database_error_message())

    def test_supabase_delete_patient_cases_reports_delete_failure(self) -> None:
        class FakeDelete:
            def eq(self, *_args):
                return self

            def execute(self):
                raise RuntimeError("delete denied")

        class FakeTable:
            def delete(self):
                return FakeDelete()

        class FakeClient:
            def table(self, *_args):
                return FakeTable()

        with patch("backend.database._supabase_client", return_value=FakeClient()):
            with patch("backend.database._supabase_configured", return_value=True):
                self.assertFalse(delete_patient_cases(" Patient 001 "))

        self.assertIn("delete denied", database_error_message())

    def test_supabase_legacy_save_fallback_reports_missing_private_code(self) -> None:
        class FakeInsert:
            def __init__(self, table):
                self.table = table

            def execute(self):
                self.table.calls += 1
                if self.table.calls == 1:
                    raise RuntimeError("missing column share_code")
                return SimpleNamespace(data=[{"id": 1}])

        class FakeTable:
            def __init__(self):
                self.calls = 0
                self.rows = []

            def insert(self, row):
                self.rows.append(row)
                return FakeInsert(self)

        class FakeClient:
            def __init__(self):
                self.patient_cases = FakeTable()

            def table(self, name):
                self.table_name = name
                return self.patient_cases

        fake_client = FakeClient()
        result = {
            "possible_category": "General Health",
            "risk_level": "Doctor Visit Recommended",
            "recommendation": "Book a doctor visit.",
            "score": "40",
        }

        with patch("backend.database._supabase_client", return_value=fake_client):
            self.assertEqual(
                save_case({"patient_name": "Ava", "age": "31", "symptoms": ["cough"]}, result),
                "",
            )

        self.assertEqual(fake_client.patient_cases.calls, 2)
        self.assertIn("share_code", fake_client.patient_cases.rows[0])
        self.assertNotIn("share_code", fake_client.patient_cases.rows[1])
        self.assertIn("schema is outdated", database_error_message())

    def test_production_never_falls_back_to_local_patient_storage(self) -> None:
        patient = {"patient_name": "Ava", "age": 31, "symptoms": ["cough"]}
        result = {
            "possible_category": "Respiratory",
            "risk_level": "Doctor Visit Recommended",
            "recommendation": "Book a doctor visit.",
            "score": 30,
        }
        with patch("backend.database._supabase_client", return_value=None), patch(
            "backend.database._production_mode", return_value=True
        ), patch("backend.database._offline_mode", return_value=False), patch(
            "backend.database.sqlite3.connect"
        ) as local_connect:
            self.assertEqual(save_case(patient, result), "")
            self.assertEqual(database.database_backend(), "Storage unavailable")
            local_connect.assert_not_called()
        self.assertIn("Secure patient storage is unavailable", database_error_message())

    def test_full_disk_database_error_does_not_crash_patient_page(self) -> None:
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            with patch.object(database, "DB_PATH", Path(tmp) / "cases.db"), patch(
                "backend.database._local_storage_allowed", return_value=True
            ), patch(
                "backend.database.sqlite3.connect",
                side_effect=database.sqlite3.OperationalError("database or disk is full"),
            ):
                self.assertFalse(init_db())
                self.assertEqual(database.list_cases(), [])
        self.assertIn("failed safely", database_error_message())


if __name__ == "__main__":
    unittest.main()
