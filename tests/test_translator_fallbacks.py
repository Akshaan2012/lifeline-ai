from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from backend import translator
from backend.translator import _fallback_text, translate_items, translate_text


class TranslatorFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        translate_text.cache_clear()
        translator._translate_batch_cached.cache_clear()

    def tearDown(self) -> None:
        translate_text.cache_clear()
        translator._translate_batch_cached.cache_clear()

    def test_offline_hindi_keeps_valid_static_fallback(self) -> None:
        with patch.dict(os.environ, {"LIFELINE_OFFLINE_MODE": "true"}, clear=False):
            translated = translate_text("Language", "Hindi")

        self.assertEqual(translated, "\u092d\u093e\u0937\u093e")

    def test_offline_hindi_ignores_corrupted_static_fallback(self) -> None:
        with patch.dict(translator.HINDI_FALLBACKS, {"Broken Label": "Ã Â¤Â¸Ã Â¥Â"}, clear=False):
            translated = _fallback_text("Broken Label", "Hindi")

        self.assertEqual(translated, "Broken Label")

    def test_online_hindi_static_fallback_ignores_corrupted_text(self) -> None:
        with patch.dict(translator.HINDI_FALLBACKS, {"Broken Label": "Ã Â¤Â¸Ã Â¥Â"}, clear=False):
            translated = translate_text("Broken Label", "Hindi")

        self.assertEqual(translated, "Broken Label")

    def test_batch_hindi_static_fallback_ignores_corrupted_text(self) -> None:
        with patch.dict(translator.HINDI_FALLBACKS, {"Broken Label": "Ã Â¤Â¸Ã Â¥Â"}, clear=False):
            translated = translate_items(["Broken Label"], "Hindi")

        self.assertEqual(translated, ["Broken Label"])


if __name__ == "__main__":
    unittest.main()
