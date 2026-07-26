from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.ml_model import predict_with_model, patient_to_features


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

    def test_predict_with_model_formats_fake_model_output(self) -> None:
        class FakeModel:
            classes_ = ["Self-Care", "Emergency"]

            def predict(self, _features):
                return ["Emergency"]

            def predict_proba(self, _features):
                return [[0.1, 0.9]]

        with patch("backend.ml_model.train_or_load_model", return_value=FakeModel()):
            result = predict_with_model({"symptoms": ["chest pain"]})

        self.assertEqual(result["prediction"], "Emergency")
        self.assertEqual(result["confidence"], 0.9)
        self.assertEqual(result["probabilities"]["Emergency"], 0.9)


if __name__ == "__main__":
    unittest.main()
