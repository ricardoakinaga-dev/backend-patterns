import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent


class KnownBadHarnessTests(unittest.TestCase):
    def run_script(self, root: Path, relative: str):
        return subprocess.run(
            [sys.executable, "-B", str(root / relative)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def copy_package(self) -> Path:
        temp = Path(tempfile.mkdtemp(prefix="backend-patterns-known-bad-"))
        for name in ("SKILL.md", "README.md", "composition-contract.json"):
            shutil.copy2(ROOT / name, temp / name)
        for directory in ("references", "scripts", "tests"):
            shutil.copytree(ROOT / directory, temp / directory)
        return temp

    def test_missing_required_heading_is_rejected(self):
        temp = self.copy_package()
        self.addCleanup(shutil.rmtree, temp)
        path = temp / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("## Decision record", "## Removed decision record", 1), encoding="utf-8")
        result = self.run_script(temp, "scripts/validate-skill.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Decision record", result.stdout)

    def test_broken_index_route_is_rejected(self):
        temp = self.copy_package()
        self.addCleanup(shutil.rmtree, temp)
        path = temp / "references" / "pattern-index.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("(api-patterns.md)", "(missing-api-patterns.md)", 1), encoding="utf-8")
        result = self.run_script(temp, "scripts/validate-links.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing", result.stdout)

    def test_fixture_without_oracle_is_rejected(self):
        temp = self.copy_package()
        self.addCleanup(shutil.rmtree, temp)
        path = temp / "tests" / "selection" / "scenarios.json"
        items = json.loads(path.read_text(encoding="utf-8"))
        del items[0]["known_bad"]
        path.write_text(json.dumps(items), encoding="utf-8")
        result = self.run_script(temp, "tests/run_evals.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("known_bad", result.stdout)

    def test_false_declared_target_is_rejected(self):
        temp = self.copy_package()
        self.addCleanup(shutil.rmtree, temp)
        path = temp / "tests" / "activation" / "scenarios.json"
        items = json.loads(path.read_text(encoding="utf-8"))
        items[0]["known_bad"]["target"] = "prompt"
        path.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        result = self.run_script(temp, "tests/run_known_bad.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("target mismatch", result.stdout)

    def test_unrelated_failure_does_not_satisfy_diagnostic_oracle(self):
        temp = self.copy_package()
        self.addCleanup(shutil.rmtree, temp)
        validator = temp / "scripts" / "validate-framework-independence.py"
        validator.write_text(
            "print('UNRELATED_FAILURE_ONLY')\nraise SystemExit(1)\n",
            encoding="utf-8",
        )
        result = self.run_script(temp, "tests/run_known_bad.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("without its declared diagnostic", result.stdout)


if __name__ == "__main__":
    unittest.main()
