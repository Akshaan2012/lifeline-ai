from __future__ import annotations

import unittest

from backend.database import normalize_share_code


class DatabaseHelperTests(unittest.TestCase):
    def test_share_code_normalization_accepts_common_user_typing(self) -> None:
        self.assertEqual(normalize_share_code("ll-1a2b3c4d5e6f"), "LL-1A2B3C4D5E6F")
        self.assertEqual(normalize_share_code(" LL 1a2b 3c4d5e6f "), "LL-1A2B3C4D5E6F")


if __name__ == "__main__":
    unittest.main()
