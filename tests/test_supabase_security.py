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


if __name__ == "__main__":
    unittest.main()
