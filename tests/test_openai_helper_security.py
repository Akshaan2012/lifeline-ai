from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from backend import openai_helper


class OpenAIHelperSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        openai_helper.setting.cache_clear()
        openai_helper._OPENAI_CALL_TIMES.clear()

    def tearDown(self) -> None:
        openai_helper.setting.cache_clear()
        openai_helper._OPENAI_CALL_TIMES.clear()

    def test_environment_specific_key_is_preferred(self) -> None:
        env = {
            "LIFELINE_ENV": "production",
            "OPENAI_API_KEY": "fallback-key",
            "OPENAI_API_KEY_DEV": "dev-key",
            "OPENAI_API_KEY_PROD": "prod-key",
        }
        with patch.dict(os.environ, env, clear=False):
            openai_helper.setting.cache_clear()
            self.assertEqual(openai_helper.provider_api_key(), "prod-key")

    def test_identifier_minimization_removes_common_direct_identifiers(self) -> None:
        text = (
            "Patient name: Asha Mehta\n"
            "MRN: 123456789\n"
            "Email asha@example.com and phone +91 98765 43210.\n"
            "Symptoms: cough and fever."
        )

        minimized = openai_helper.minimize_patient_identifiers(text)

        self.assertNotIn("Asha Mehta", minimized)
        self.assertNotIn("asha@example.com", minimized)
        self.assertNotIn("+91 98765 43210", minimized)
        self.assertIn("Symptoms: cough and fever.", minimized)

    def test_rate_limit_blocks_after_configured_limit(self) -> None:
        env = {"OPENAI_RATE_LIMIT_PER_MINUTE": "1"}
        with patch.dict(os.environ, env, clear=False):
            openai_helper.setting.cache_clear()
            self.assertTrue(openai_helper._rate_limit_allows_call())
            self.assertFalse(openai_helper._rate_limit_allows_call())


if __name__ == "__main__":
    unittest.main()
