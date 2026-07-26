from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.disease_qa import _ai_health_answer, answer_question


class DiseaseQaSafetyTests(unittest.TestCase):
    def test_casual_chest_pain_question_gets_urgent_safety_frame(self) -> None:
        answer = answer_question("is chest pain normal")

        self.assertEqual(answer["intent"], "emergency")
        self.assertIn("urgent", answer["doctor"].lower())
        self.assertTrue(any("chest pain" in item.lower() for item in answer["emergency"]))

    def test_possible_overdose_question_does_not_wait_for_general_medicine_answer(self) -> None:
        answer = answer_question("i took too many pills what should i do")

        self.assertEqual(answer["intent"], "emergency")
        self.assertIn("urgent", answer["doctor"].lower())
        self.assertTrue(any("overdose" in item.lower() for item in answer["emergency"]))

    def test_general_unknown_question_still_returns_complete_safe_answer(self) -> None:
        answer = answer_question("what causes mild tiredness")

        self.assertIn("meaning", answer)
        self.assertTrue(answer["symptoms"])
        self.assertTrue(answer["precautions"])
        self.assertTrue(answer["emergency"])

    def test_ai_answer_parser_accepts_text_lists_without_character_split(self) -> None:
        ai_payload = {
            "title": "Mild tiredness",
            "meaning": "Tiredness can have many causes.",
            "symptoms": "fatigue, weakness",
            "precautions": "rest; drink water",
            "prevention": "sleep well\n eat balanced meals",
            "doctor": "Ask a doctor if it continues.",
            "emergency": "chest pain, fainting",
            "kind": "general",
            "intent": "meaning",
        }

        with patch("backend.disease_qa.ai_json", return_value=ai_payload):
            answer = _ai_health_answer("why am I tired", {"kind": "general"})

        self.assertIsNotNone(answer)
        assert answer is not None
        self.assertEqual(answer["symptoms"], ["fatigue", "weakness"])
        self.assertEqual(answer["emergency"], ["chest pain", "fainting"])
        self.assertNotIn("f", answer["symptoms"])


if __name__ == "__main__":
    unittest.main()
