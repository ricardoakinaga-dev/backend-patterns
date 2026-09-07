import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent


def run_script(relative, *args):
    return subprocess.run(
        [sys.executable, "-B", str(ROOT / relative), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class PackageContractTests(unittest.TestCase):
    def test_static_package_validator(self):
        result = run_script("scripts/validate-skill.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_links_and_index(self):
        for script in (
            "scripts/validate-links.py",
            "scripts/validate-pattern-index.py",
            "scripts/validate-composition.py",
            "scripts/validate-framework-independence.py",
        ):
            result = run_script(script)
            self.assertEqual(result.returncode, 0, f"{script}: {result.stdout}{result.stderr}")

    def test_eval_fixture_corpus(self):
        result = run_script("tests/run_evals.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertGreaterEqual(report["scenario_count"], 20)
        self.assertEqual(report["model_execution"], "NOT_RUN")

    def test_all_declared_known_bad_mutations_execute(self):
        result = run_script("tests/run_known_bad.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["scenario_count"], 26)
        self.assertEqual(report["executed"], 26)
        self.assertEqual(report["declarations_verified"], 26)
        self.assertEqual(report["passed_oracles"], 26)

    def test_assurance_report_when_workspace_evidence_is_present(self):
        if not (ROOT / "docs" / "assurance-report.md").is_file():
            self.skipTest("consumer package copy does not carry workspace assurance evidence")
        result = run_script("scripts/validate-assurance-report.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
