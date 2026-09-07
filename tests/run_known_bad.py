#!/usr/bin/env python3
"""Execute every declared known-bad mutation in an isolated package copy."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = ROOT / "tests"
COPY_DIRS = ("references", "scripts", "tests")
COPY_FILES = ("SKILL.md", "README.md", "composition-contract.json")
EXPECTED_DIAGNOSTICS = {
    "remove_required_observations": "required_observations",
    "remove_rejected_alternative": "required_observations",
    "remove_required_concepts": "required_concepts",
    "replace_expected_outcome": "unknown outcome",
    "inject_framework_bias": "framework-specific name",
}
EXPECTED_TARGETS = {
    "remove_required_observations": "required_observations",
    "remove_rejected_alternative": "required_observations",
    "remove_required_concepts": "required_concepts",
    "replace_expected_outcome": "expected_outcome",
    "inject_framework_bias": "package_scan",
}


def scenario_files(root: Path) -> list[Path]:
    return sorted(
        path for path in (root / "tests").rglob("scenarios.json")
        if "fixtures" not in path.parts and "benchmark" not in path.parts
    )


def copy_package(destination: Path) -> None:
    for name in COPY_FILES:
        shutil.copy2(ROOT / name, destination / name)
    for name in COPY_DIRS:
        shutil.copytree(
            ROOT / name,
            destination / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )


def mutate(destination: Path, source_path: Path, scenario: dict) -> None:
    mutation = scenario["known_bad"]["mutation"]
    if mutation == "inject_framework_bias":
        path = destination / "SKILL.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\nThis core is Node/Express-first.\n",
            encoding="utf-8",
        )
        return
    target = destination / source_path.relative_to(ROOT)
    items = json.loads(target.read_text(encoding="utf-8"))
    selected = next(item for item in items if item.get("id") == scenario["id"])
    if mutation in {"remove_required_observations", "remove_rejected_alternative"}:
        selected["required_observations"] = []
    elif mutation == "remove_required_concepts":
        selected["required_concepts"] = []
    elif mutation == "replace_expected_outcome":
        selected["expected_outcome"] = "INVALID_OUTCOME"
    else:
        raise ValueError(f"unsupported declared mutation: {mutation}")
    target.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    scenarios = []
    for path in scenario_files(ROOT):
        for scenario in json.loads(path.read_text(encoding="utf-8")):
            scenarios.append((path, scenario))
    failures: list[str] = []
    executed = 0
    declarations_verified = 0
    with tempfile.TemporaryDirectory(prefix="backend-patterns-known-bad-suite-") as temporary:
        base = Path(temporary)
        for source_path, scenario in scenarios:
            isolated = base / scenario["id"]
            isolated.mkdir()
            copy_package(isolated)
            declaration = scenario["known_bad"]
            mutation = declaration["mutation"]
            target = declaration["target"]
            expected_result = declaration["expected_result"]
            declared_diagnostic = declaration.get("diagnostic")
            if mutation not in EXPECTED_TARGETS:
                failures.append(f"{scenario['id']}: unsupported mutation declaration: {mutation}")
            elif target != EXPECTED_TARGETS[mutation]:
                failures.append(
                    f"{scenario['id']}: target mismatch for {mutation}: declared {target}, expected {EXPECTED_TARGETS[mutation]}"
                )
            elif declared_diagnostic != EXPECTED_DIAGNOSTICS[mutation]:
                failures.append(
                    f"{scenario['id']}: diagnostic mismatch for {mutation}: declared {declared_diagnostic}, expected {EXPECTED_DIAGNOSTICS[mutation]}"
                )
            elif expected_result != "FAIL":
                failures.append(f"{scenario['id']}: unsupported expected_result declaration: {expected_result}")
            elif mutation != "inject_framework_bias" and target not in scenario:
                failures.append(f"{scenario['id']}: declared target is not a scenario field: {target}")
            else:
                declarations_verified += 1
            mutate(isolated, source_path, scenario)
            command = (
                [sys.executable, "-B", "scripts/validate-framework-independence.py"]
                if mutation == "inject_framework_bias"
                else [sys.executable, "-B", "tests/run_evals.py"]
            )
            result = subprocess.run(command, cwd=isolated, text=True, capture_output=True, check=False)
            executed += 1
            if result.returncode == 0:
                failures.append(f"{scenario['id']}: mutation {mutation} unexpectedly passed")
            actual_output = (result.stdout + result.stderr).lower()
            expected_diagnostic = str(declared_diagnostic or "").lower()
            if expected_diagnostic and expected_diagnostic not in actual_output:
                failures.append(
                    f"{scenario['id']}: mutation {mutation} failed without its declared diagnostic {expected_diagnostic}"
                )
    report = {
        "scope": "KNOWN_BAD_MUTATION_EXECUTION",
        "model_execution": "NOT_RUN",
        "scenario_count": len(scenarios),
        "executed": executed,
        "declarations_verified": declarations_verified,
        "passed_oracles": executed - len(failures),
        "failures": failures,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if failures or executed != len(scenarios) or declarations_verified != len(scenarios) else 0


if __name__ == "__main__":
    raise SystemExit(main())
