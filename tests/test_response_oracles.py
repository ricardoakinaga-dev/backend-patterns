from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent


class ResponseOracleTests(unittest.TestCase):
    def test_known_bad_response_mutations_are_causally_sensitive(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", "scripts/run-response-mutations.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertGreaterEqual(report["oracle_count"], 15)
        self.assertEqual(report["failed"], 0)
        self.assertTrue(all(item["causal_sensitivity"] for item in report["results"]))
        self.assertTrue(all(item["shared_context_held_constant"] for item in report["results"]))
        self.assertTrue(all(item["mutation_metadata_safe"] for item in report["results"]))
        self.assertTrue(all(item["body_shape_safe"] for item in report["results"]))


if __name__ == "__main__":
    unittest.main()
