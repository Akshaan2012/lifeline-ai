from __future__ import annotations

from types import SimpleNamespace
import unittest

from backend.recommender import build_recommendations


class RecommenderSafetyTests(unittest.TestCase):
    def test_unknown_risk_level_uses_safe_recommendation_fallback(self) -> None:
        result = SimpleNamespace(
            risk_level="Needs review",
            score=33,
            possible_category="Unknown",
            explanation="Partial imported result.",
            signals="fever, cough",
        )

        advice = build_recommendations(result, enhance=False)

        self.assertEqual(advice["doctor_visit"], "A doctor visit is recommended.")
        self.assertIn("Moderate risk", advice["risk_summary"])
        self.assertIn("Doctor Visit Recommended", advice["report_summary"])


if __name__ == "__main__":
    unittest.main()
