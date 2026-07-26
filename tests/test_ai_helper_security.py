from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from backend import ai_helper


class AIHelperSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        ai_helper.setting.cache_clear()
        ai_helper._AI_CALL_TIMES.clear()

    def tearDown(self) -> None:
        ai_helper.setting.cache_clear()
        ai_helper._AI_CALL_TIMES.clear()

    def test_gemini_key_is_preferred_over_google_alias(self) -> None:
        env = {
            "GEMINI_API_KEY": "gemini-key",
            "GOOGLE_API_KEY": "google-alias-key",
        }
        with patch.dict(os.environ, env, clear=False):
            ai_helper.setting.cache_clear()
            self.assertEqual(ai_helper.provider_api_key(), "gemini-key")

    def test_gemini_model_is_configurable(self) -> None:
        with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-test-model"}, clear=False):
            ai_helper.setting.cache_clear()
            self.assertEqual(ai_helper.provider_model(), "gemini-test-model")

    def test_identifier_minimization_removes_common_direct_identifiers(self) -> None:
        text = (
            "Patient name: Asha Mehta\n"
            "MRN: 123456789\n"
            "Email asha@example.com and phone +91 98765 43210.\n"
            "Symptoms: cough and fever."
        )

        minimized = ai_helper.minimize_patient_identifiers(text)

        self.assertNotIn("Asha Mehta", minimized)
        self.assertNotIn("asha@example.com", minimized)
        self.assertNotIn("+91 98765 43210", minimized)
        self.assertIn("Symptoms: cough and fever.", minimized)

    def test_identifier_minimization_removes_casual_name_and_birth_date(self) -> None:
        text = "My name is Asha Mehta. I was born on July 4 2010. Symptoms: chest pain."

        minimized = ai_helper.minimize_patient_identifiers(text)

        self.assertNotIn("Asha Mehta", minimized)
        self.assertNotIn("July 4 2010", minimized)
        self.assertIn("Symptoms: chest pain.", minimized)

    def test_rate_limit_blocks_after_configured_limit(self) -> None:
        env = {"AI_RATE_LIMIT_PER_MINUTE": "1"}
        with patch.dict(os.environ, env, clear=False):
            ai_helper.setting.cache_clear()
            self.assertTrue(ai_helper._rate_limit_allows_call())
            self.assertFalse(ai_helper._rate_limit_allows_call())

    def test_bad_numeric_ai_settings_use_safe_defaults(self) -> None:
        env = {
            "AI_RATE_LIMIT_PER_MINUTE": "not-a-number",
            "AI_MAX_OUTPUT_TOKENS": "many",
            "AI_TIMEOUT_SECONDS": "soon",
        }
        with patch.dict(os.environ, env, clear=False):
            ai_helper.setting.cache_clear()

            self.assertEqual(ai_helper.setting_int("AI_RATE_LIMIT_PER_MINUTE", 30), 30)
            self.assertEqual(ai_helper.setting_int("AI_MAX_OUTPUT_TOKENS", 220), 220)
            self.assertEqual(ai_helper.setting_float("AI_TIMEOUT_SECONDS", 10), 10)


if __name__ == "__main__":
    unittest.main()
