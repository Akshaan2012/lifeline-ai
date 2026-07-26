from __future__ import annotations

import unittest

from backend.ml_model import patient_to_features


class MLModelFeatureTests(unittest.TestCase):
    def test_patient_to_features_tolerates_saved_text_values(self) -> None:
        features = patient_to_features(
            {
                "age": "not entered",
                "duration_days": "",
                "pain_level": None,
                "temperature": "warm",
                "heart_rate": "fast",
                "systolic_bp": "unknown",
                "diastolic_bp": "unknown",
                "oxygen": "normal",
                "conditions": "asthma, diabetes",
                "symptoms": "chest pain, confusion",
            }
        )

        self.assertEqual(features[:9], [0, 0, 0, 37.0, 80, 120, 80, 98, 2])
        self.assertEqual(features[14], 1.0)
        self.assertEqual(features[17], 1.0)


if __name__ == "__main__":
    unittest.main()
