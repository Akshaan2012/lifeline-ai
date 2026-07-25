from __future__ import annotations

import unittest

from backend.disease_qa import answer_question


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


if __name__ == "__main__":
    unittest.main()
