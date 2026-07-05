from types import SimpleNamespace
import unittest
from unittest.mock import patch

from backend.database import current_staff_user, sign_in_staff


class FakeAuth:
    def __init__(self, role: str | None) -> None:
        self.user = SimpleNamespace(
            id="user-1",
            email="clinic@example.com",
            app_metadata={"role": role} if role else {},
        )
        self.signed_out = False

    def sign_in_with_password(self, credentials):
        return SimpleNamespace(user=self.user)

    def get_session(self):
        return SimpleNamespace(user=self.user)

    def sign_out(self):
        self.signed_out = True


class StaffAuthTests(unittest.TestCase):
    def test_staff_role_is_accepted(self) -> None:
        client = SimpleNamespace(auth=FakeAuth("staff"))
        with patch("backend.database._supabase_client", return_value=client):
            ok, _ = sign_in_staff("clinic@example.com", "secret")
            self.assertTrue(ok)
            self.assertEqual(current_staff_user()["email"], "clinic@example.com")

    def test_non_staff_account_is_rejected_and_signed_out(self) -> None:
        auth = FakeAuth("patient")
        client = SimpleNamespace(auth=auth)
        with patch("backend.database._supabase_client", return_value=client):
            ok, message = sign_in_staff("person@example.com", "secret")
            self.assertFalse(ok)
            self.assertIn("does not have clinic staff access", message)
            self.assertTrue(auth.signed_out)


if __name__ == "__main__":
    unittest.main()
