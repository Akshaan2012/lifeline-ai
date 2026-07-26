from __future__ import annotations

import unittest
from pathlib import Path


class SupabaseSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = Path("supabase_schema.sql").read_text(encoding="utf-8").lower()

    def test_anonymous_users_cannot_read_update_or_delete_patient_table(self) -> None:
        self.assertNotIn("for select\nto anon", self.schema)
        self.assertNotIn("for update\nto anon", self.schema)
        self.assertNotIn("for delete\nto anon", self.schema)

    def test_staff_policies_require_server_controlled_role(self) -> None:
        self.assertGreaterEqual(
            self.schema.count("app_metadata' ->> 'role') = 'staff'"), 4
        )

    def test_private_code_lookup_returns_limited_columns(self) -> None:
        self.assertIn("get_patient_case_by_share_code", self.schema)
        self.assertIn("security definer", self.schema)
        self.assertIn("grant execute", self.schema)

    def test_private_code_lookup_normalizes_spaces_and_missing_dash(self) -> None:
        self.assertIn("regexp_replace(coalesce(input_code, ''), '\\s+', '', 'g')", self.schema)
        self.assertIn("'ll-' || substring", self.schema)

    def test_private_code_lookup_validates_code_shape_in_rpc(self) -> None:
        self.assertIn("~ '^ll-[0-9a-f]{12}$'", self.schema)
        self.assertIn("cross join normalized", self.schema)

    def test_review_status_and_patient_visible_note_constraints_exist(self) -> None:
        self.assertIn("patient_cases_review_status_check", self.schema)
        self.assertIn("'seek urgent care'", self.schema)
        self.assertIn("patient_cases_doctor_notes_length_check", self.schema)
        self.assertIn("char_length(doctor_notes) <= 1200", self.schema)

    def test_review_migration_cleans_existing_rows_before_constraints(self) -> None:
        self.assertIn("set review_status = 'new'", self.schema)
        self.assertIn("review_status not in", self.schema)
        self.assertIn("set doctor_notes = left(coalesce(doctor_notes, ''), 1200)", self.schema)
        self.assertIn("set patient_consent = false", self.schema)
        self.assertIn("alter column review_status set not null", self.schema)
        self.assertIn("alter column doctor_notes set not null", self.schema)
        self.assertIn("alter column patient_consent set not null", self.schema)


if __name__ == "__main__":
    unittest.main()
