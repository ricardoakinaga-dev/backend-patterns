#!/usr/bin/env python3
"""Validate the deterministic skill-evaluation corpus and its coverage.

This runner deliberately does not execute an LLM. It proves that the evaluation
fixtures have stable IDs, required observations, known-bad mutations, and that
their requested concepts are represented by the package. Consumer-model
execution remains a separate host-level observation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = ROOT / "tests"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def scenario_files() -> list[Path]:
    return sorted(
        path for path in FIXTURE_ROOT.rglob("scenarios.json")
        if "fixtures" not in path.parts and "benchmark" not in path.parts
    )


def validate(category: str | None = None) -> dict:
    rubric = load_json(FIXTURE_ROOT / "fixtures" / "rubric.json")
    errors: list[str] = []
    scenarios = []
    seen: set[str] = set()
    for path in scenario_files():
        items = load_json(path)
        if not isinstance(items, list):
            errors.append(f"{path.relative_to(ROOT)} must contain an array")
            continue
        for index, item in enumerate(items):
            prefix = f"{path.relative_to(ROOT)}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            missing = sorted(set(rubric["required_fields"]) - set(item))
            if missing:
                errors.append(f"{prefix} missing fields: {', '.join(missing)}")
                continue
            if item["id"] in seen:
                errors.append(f"duplicate scenario id: {item['id']}")
            seen.add(item["id"])
            if item["category"] not in rubric["required_categories"]:
                errors.append(f"{prefix} has unknown category {item['category']}")
            if item["expected_outcome"] not in rubric["outcome_states"]:
                errors.append(f"{prefix} has unknown outcome {item['expected_outcome']}")
            if not isinstance(item["required_observations"], list) or not item["required_observations"]:
                errors.append(f"{prefix}.required_observations must be non-empty")
            if not isinstance(item["required_concepts"], list) or not item["required_concepts"]:
                errors.append(f"{prefix}.required_concepts must be non-empty")
            known_bad = item["known_bad"]
            known_bad_fields = rubric.get(
                "known_bad_required_fields", ("mutation", "target", "expected_result", "diagnostic")
            )
            if not isinstance(known_bad, dict) or not all(known_bad.get(key) for key in known_bad_fields):
                errors.append(f"{prefix}.known_bad must identify mutation, target, expected_result and diagnostic")
            scenarios.append((path, item))

    selected = [(path, item) for path, item in scenarios if category is None or item.get("category") == category]
    if category is not None and not selected:
        errors.append(f"no scenarios found for category {category}")
    categories = {item.get("category") for _, item in scenarios}
    for required in rubric["required_categories"]:
        if required not in categories:
            errors.append(f"required category has no fixture: {required}")

    package_text = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in [ROOT / "SKILL.md", ROOT / "README.md", *(ROOT / "references").glob("*.md")]
        if path.is_file()
    )
    for path, item in selected:
        for concept in item["required_concepts"]:
            if concept.lower() not in package_text:
                errors.append(f"{item['id']}: required concept is absent from package: {concept}")

    return {
        "scope": "DETERMINISTIC_SKILL_EVAL_FIXTURES",
        "model_execution": "NOT_RUN",
        "scenario_count": len(selected),
        "category": category,
        "categories": sorted(categories),
        "errors": errors,
        "known_bad_mutations_declared": sum(1 for _, item in selected if isinstance(item.get("known_bad"), dict)),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=["activation", "selection", "rejection", "adversarial", "composition", "regression"])
    args = parser.parse_args()
    result = validate(args.category)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(1 if result["errors"] else 0)
