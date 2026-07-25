from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from backend import translator
from backend.translator import _fallback_text, translate_text


class TranslatorFallbackTests(unittest.TestCase):
    def test_offline_hindi_keeps_valid_static_fallback(self) -> None:
        with patch.dict(os.environ, {"LIFELINE_OFFLINE_MODE": "true"}, clear=False):
            translated = translate_text("Language", "🇮🇳 Hindi")

        self.assertEqual(translated, "भाषा")

    def test_offline_hindi_ignores_corrupted_static_fallback(self) -> None:
        with patch.dict(translator.HINDI_FALLBACKS, {"Broken Label": "à¤¸à¥"}, clear=False):
            translated = _fallback_text("Broken Label", "🇮🇳 Hindi")

        self.assertEqual(translated, "Broken Label")

if __name__ == "__main__":
    unittest.main()
