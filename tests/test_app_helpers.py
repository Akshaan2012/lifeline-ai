from __future__ import annotations

import json
import unittest

from backend.care_features import parse_case_raw_data


class AppHelperTests(unittest.TestCase):
    def test_parse_case_raw_data_accepts_dict(self) -> None:
        self.assertEqual(parse_case_raw_data({"symptoms": ["fever"]}), {"symptoms": ["fever"]})

    def test_parse_case_raw_data_accepts_json_bytes(self) -> None:
        raw = json.dumps({"symptoms": ["cough"], "pain_level": 2}).encode("utf-8")

        self.assertEqual(
            parse_case_raw_data(raw),
            {"symptoms": ["cough"], "pain_level": 2},
        )

    def test_parse_case_raw_data_accepts_double_encoded_json(self) -> None:
        raw = json.dumps(json.dumps({"conditions": ["asthma"]}))

        self.assertEqual(parse_case_raw_data(raw), {"conditions": ["asthma"]})

    def test_parse_case_raw_data_rejects_bad_or_non_object_data(self) -> None:
        self.assertEqual(parse_case_raw_data("not json"), {})
        self.assertEqual(parse_case_raw_data("[1, 2, 3]"), {})
        self.assertEqual(parse_case_raw_data(b"\xff"), {})


if __name__ == "__main__":
    unittest.main()
