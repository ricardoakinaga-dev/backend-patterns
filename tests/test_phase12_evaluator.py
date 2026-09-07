import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BEHAVIORAL = runpy.run_path(str(ROOT / "scripts" / "run-behavioral-eval.py"))
GENERALIZATION = runpy.run_path(str(ROOT / "scripts" / "run-generalization-gates.py"))
COMPOSITION = runpy.run_path(str(ROOT / "scripts" / "run-composition-eval.py"))


def fingerprints():
    return {
        "corpus_sha256": BEHAVIORAL["sha256"](BEHAVIORAL["SCENARIOS"]),
        "package_sha256": BEHAVIORAL["package_fingerprint"](),
    }


def metadata(holdout_first_result_only=False):
    result = {
        "capture_status": "EXECUTED",
        "consumer_identity": "host-consumer",
        "consumer_version": "consumer-1",
        "adapter_identity": "test-adapter",
        "adapter_version": "adapter-1",
        "model_identity": "model-under-test",
        "model_version": "model-1",
        "captured_at": "2026-09-07T18:00:00+00:00",
        "fingerprints": fingerprints(),
    }
    if holdout_first_result_only:
        result["holdout_first_result_only"] = True
    return result


def fairness():
    return {
        "paired_scenarios": True,
        "same_model": True,
        "same_prompt": True,
        "same_generation_parameters": True,
        "control": {"package_access": "withheld"},
        "treatment": {"package_access": "supplied"},
    }


def capture(mapping, include_all=False, holdout_first_result_only=False, comparisons=None):
    public_ids = sorted(mapping)
    if not include_all:
        public_ids = public_ids[:2]
    records = []
    for public_id in public_ids:
        for lane in ("control", "treatment"):
            records.append(
                {
                    "scenario_id": public_id,
                    "lane": lane,
                    "status": "EXECUTED",
                    "text": f"Decision: {lane} response for {public_id}; verify evidence and preserve unknowns.",
                    "decision": "SHOULD_USE" if lane == "treatment" else "NEED_MORE_EVIDENCE",
                }
            )
    result = {
        "protocol": BEHAVIORAL["ADAPTER_PROTOCOL"],
        "metadata": metadata(holdout_first_result_only),
        "fairness": fairness(),
        "responses": records,
    }
    if comparisons is not None:
        result["comparisons"] = comparisons
    return result


class Phase12EvaluatorTests(unittest.TestCase):
    def test_strict_capture_requires_opaque_complete_paired_lanes(self):
        _, mapping = BEHAVIORAL["request_payload"](None, 2)
        raw = json.dumps(capture(mapping))
        checked = BEHAVIORAL["validate_adapter_capture"](
            raw,
            mapping,
            expected_public_ids=set(mapping),
            expected_fingerprints=fingerprints(),
            require_complete=True,
        )
        self.assertEqual(len(checked["records"]), 4)
        self.assertEqual(
            {(item["scenario_id"], item["lane"]) for item in checked["records"]},
            {("G-08", "control"), ("G-08", "treatment"), ("SU-002", "control"), ("SU-002", "treatment")},
        )
        self.assertEqual(checked["fairness"]["control"]["package_access"], "withheld")
        self.assertEqual(checked["fairness"]["treatment"]["package_access"], "supplied")

    def test_malformed_unknown_gold_missing_lane_and_duplicate_lane_are_rejected(self):
        _, mapping = BEHAVIORAL["request_payload"](None, 1)
        base = {"scenario_id": "case-001", "lane": "control", "response": "ok"}
        cases = [
            ({**base, "scenario_id": "G-08"}, "unknown or non-opaque"),
            ({"scenario_id": "case-001", "response": "ok"}, "missing lane"),
            ({**base, "expected_decision": {"stance": "SHOULD_USE"}}, "gold/rubric"),
        ]
        for record, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(ValueError) as caught:
                    BEHAVIORAL["normalize_adapter_response"](json.dumps([record]), mapping)
                self.assertIn(expected, str(caught.exception))
        duplicate = json.dumps([base, dict(base)])
        with self.assertRaises(ValueError) as caught:
            BEHAVIORAL["normalize_adapter_response"](duplicate, mapping)
        self.assertIn("duplicates scenario/lane", str(caught.exception))

    def test_raw_adapter_output_is_persisted_and_hashed_before_scoring(self):
        payload, mapping = BEHAVIORAL["request_payload"](None, 1)
        raw = json.dumps(capture(mapping), ensure_ascii=False) + "\n"
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            source = directory_path / "capture.json"
            source.write_text(raw, encoding="utf-8")
            adapter = directory_path / "adapter.py"
            adapter.write_text(
                "import pathlib\n"
                "print(pathlib.Path(__file__).with_name('capture.json').read_text(), end='')\n",
                encoding="utf-8",
            )
            raw_path = directory_path / "raw-output.json"
            result = BEHAVIORAL["run"](
                argparse.Namespace(
                    adapter_command=f"{sys.executable} {adapter}",
                    response_file=None,
                    split=None,
                    limit=1,
                    raw_capture=str(raw_path),
                    output=None,
                )
            )
            self.assertTrue(raw_path.is_file())
            self.assertEqual(result["raw_capture"]["sha256"], hashlib.sha256(raw.encode("utf-8")).hexdigest())
            self.assertEqual(raw_path.read_text(encoding="utf-8"), raw)
            self.assertEqual(result["model_execution"], "EXECUTED")
            self.assertIn(result["status"], {"PASS", "FAIL"})

    def test_supplied_fixture_array_is_not_execution_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            response_file = Path(directory) / "fixture.json"
            response_file.write_text(json.dumps([{"scenario_id": "case-001", "lane": "control", "text": "fixture"}]), encoding="utf-8")
            result = BEHAVIORAL["run"](
                argparse.Namespace(
                    adapter_command=None,
                    response_file=str(response_file),
                    split=None,
                    limit=1,
                    raw_capture=None,
                    output=None,
                )
            )
            self.assertEqual(result["status"], "INVALID")
            self.assertEqual(result["model_execution"], "INVALID")
            self.assertIn("unwrapped response array", result["errors"][0])

    def test_generalization_without_capture_is_structural_only_and_blocked(self):
        result = GENERALIZATION["run"](argparse.Namespace(response_file=None, output=None))
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["structure"]["relation_errors"], [])
        self.assertEqual(result["holdout"]["structure_status"], "PASS")
        self.assertEqual(result["holdout"]["response_execution"], "BLOCKED")
        self.assertEqual(result["holdout"]["scores"], "NOT_INFERRED")

    def test_generalization_compares_captured_responses_without_scores(self):
        _, mapping = BEHAVIORAL["request_payload"](None, None)
        comparisons = {
            "minimality": [
                {"comparison_id": "min-001", "scenario_id": "case-001", "lane": "treatment", "variant": "baseline", "text": "baseline response", "decision": "NEED_MORE_EVIDENCE"},
                {"comparison_id": "min-001", "scenario_id": "case-001", "lane": "treatment", "variant": "candidate", "text": "candidate response", "decision": "SHOULD_USE"},
            ]
        }
        raw = json.dumps(capture(mapping, include_all=True, holdout_first_result_only=True, comparisons=comparisons))
        with tempfile.TemporaryDirectory() as directory:
            response_file = Path(directory) / "consumer-capture.json"
            response_file.write_text(raw, encoding="utf-8")
            result = GENERALIZATION["run"](argparse.Namespace(response_file=str(response_file), output=None))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["holdout"]["response_execution"], "PASS")
        self.assertEqual(result["holdout"]["first_result_discipline"], "first_result_only")
        self.assertEqual(result["metamorphic"]["comparison_status"], "OBSERVED_NOT_SCORED")
        self.assertEqual(result["decision_stability"]["response_execution"], "PASS")
        self.assertEqual(result["minimality"]["response_execution"], "PASS")
        self.assertEqual(result["minimality"]["scores"], "NOT_INFERRED")
        self.assertNotIn("overall_score", json.dumps(result))

    def test_composition_requires_executed_identified_fingerprinted_trace(self):
        events = [
            {"stage": "backend-engineering-vNext", "observed": True, "output": "backend"},
            {"stage": "backend-patterns", "observed": True, "output": "patterns"},
            {"stage": "security-engineering-vNext", "observed": True, "output": "security"},
            {"stage": "verification-loop-vNext", "observed": True, "output": "verification"},
            {"stage": "repair", "observed": True, "output": "repair"},
            {"stage": "re-verification", "observed": True, "output": "rerun"},
        ]
        contract_fingerprint = COMPOSITION["fingerprint"](COMPOSITION["CONTRACT"])
        package_fingerprint = COMPOSITION["package_fingerprint"]()
        envelope = {
            "protocol": COMPOSITION["COMPOSITION_PROTOCOL"],
            "metadata": {
                "capture_status": "EXECUTED",
                "consumer_identity": "neighboring-skills-host",
                "consumer_version": "host-1",
                "adapter_identity": "composition-adapter",
                "adapter_version": "adapter-1",
                "captured_at": "2026-09-07T18:00:00+00:00",
                "fingerprints": {"package_sha256": package_fingerprint, "contract_sha256": contract_fingerprint},
            },
            "trace": {"events": events},
        }
        checked = COMPOSITION["validate_composition_capture"](json.dumps(envelope))
        self.assertEqual(checked["trace_report"]["status"], "PASS")
        self.assertTrue(checked["trace_report"]["repair_loop_observed"])
        envelope["metadata"].pop("consumer_identity")
        with self.assertRaises(ValueError):
            COMPOSITION["validate_composition_capture"](json.dumps(envelope))


if __name__ == "__main__":
    unittest.main()
