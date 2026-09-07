import json
from pathlib import Path
import runpy
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BehavioralPayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = runpy.run_path(str(ROOT / "scripts" / "run-behavioral-eval.py"))

    def test_model_payload_is_opaque_and_excludes_gold_fields(self):
        payload, mapping = self.module["request_payload"](None, 2)
        self.assertEqual(len(payload["scenarios"]), 2)
        self.assertEqual(set(payload["scenarios"][0]), {"scenario_id", *self.module["PUBLIC_SCENARIO_FIELDS"]})
        self.assertEqual(payload["scenarios"][0]["scenario_id"], "case-001")
        self.assertEqual(mapping["case-001"], "G-08")
        for field in self.module["GOLD_SCENARIO_FIELDS"]:
            self.assertNotIn(field, payload["scenarios"][0])

    def test_adapter_ids_are_remapped_only_from_opaque_ids(self):
        payload, mapping = self.module["request_payload"](None, 1)
        raw = json.dumps([{"scenario_id": "case-001", "lane": "control", "response": "ok"}])
        normalized = json.loads(self.module["normalize_adapter_response"](raw, mapping))
        self.assertEqual(normalized[0]["scenario_id"], "G-08")
        with self.assertRaises(ValueError):
            self.module["normalize_adapter_response"](
                json.dumps([{"scenario_id": "G-08", "lane": "control", "response": "ok"}]),
                mapping,
            )


if __name__ == "__main__":
    unittest.main()
