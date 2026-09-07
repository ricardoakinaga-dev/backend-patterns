#!/usr/bin/env python3
"""Report structural and executable generalization gates for the benchmark."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "tests" / "benchmark" / "scenarios.json"
FINAL = ROOT / "tests" / "benchmark" / "final-gauntlet.json"
RELATIONS = ROOT / "tests" / "benchmark" / "relations.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def structure(scenarios: list[dict], relations: dict) -> dict:
    groups = {}
    for field in ("metamorphic_group", "stability_group"):
        values = defaultdict(list)
        for scenario in scenarios:
            group = scenario.get(field)
            if group:
                values[str(group)].append(str(scenario.get("id")))
        groups[field] = {key: sorted(set(value)) for key, value in sorted(values.items())}
    holdout = sum(item.get("split") == "holdout" for item in scenarios)
    relation_sets = {
        "metamorphic": relations.get("metamorphic", {}) if isinstance(relations, dict) else {},
        "stability": relations.get("stability", {}) if isinstance(relations, dict) else {},
    }
    relation_errors = []
    for label, relation_map in relation_sets.items():
        for group in groups[f"{label}_group"]:
            item = relation_map.get(group)
            if not isinstance(item, dict) or not all(
                isinstance(item.get(field), str) and item[field].strip()
                for field in ("axis", "relation", "expected_behavior")
            ):
                relation_errors.append(f"{label}:{group}")
    return {
        "scenario_count": len(scenarios),
        "split_counts": {
            split: sum(item.get("split") == split for item in scenarios)
            for split in ("development", "adversarial", "holdout")
        },
        "holdout_fraction": round(holdout / len(scenarios), 4) if scenarios else 0.0,
        "metamorphic_groups": groups["metamorphic_group"],
        "metamorphic_pair_groups": sum(len(items) >= 2 for items in groups["metamorphic_group"].values()),
        "stability_groups": groups["stability_group"],
        "stability_pair_groups": sum(len(items) >= 2 for items in groups["stability_group"].values()),
        "metamorphic_relations": relation_sets["metamorphic"],
        "stability_relations": relation_sets["stability"],
        "relation_errors": relation_errors,
    }


def run(args: argparse.Namespace) -> dict:
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    final = json.loads(FINAL.read_text(encoding="utf-8"))
    relations = json.loads(RELATIONS.read_text(encoding="utf-8"))
    corpus_structure = structure(scenarios, relations)
    final_count = len(final.get("cases", []))
    report = {
        "scope": "GENERALIZATION_GATES",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "model_execution": "NOT_INFERRED",
        "corpus_fingerprint": sha256(SCENARIOS),
        "structure": corpus_structure,
        "final_gauntlet": {
            "count": final_count,
            "structure_status": "PASS" if final_count == 20 else "FAIL",
            "execution_status": "BLOCKED",
            "status": "BLOCKED" if final_count == 20 else "FAIL",
            "reason": "Final-gauntlet cases are structurally present; consumer-model response capture was not supplied.",
        },
        "holdout": {
            "status": "PASS" if corpus_structure["split_counts"]["holdout"] >= 15 else "FAIL",
            "execution_status": "BLOCKED",
            "reason": "No consumer-model response capture was supplied.",
        },
        "metamorphic": {
            "structure_status": "PASS" if corpus_structure["metamorphic_pair_groups"] >= 1 and not corpus_structure["relation_errors"] else "FAIL",
            "relations_status": "PASS" if corpus_structure["metamorphic_relations"] and not corpus_structure["relation_errors"] else "FAIL",
            "execution_status": "BLOCKED",
            "reason": "Pairwise response comparison requires model output.",
        },
        "minimality": {
            "status": "BLOCKED",
            "reason": "Minimal-context response comparison requires model output.",
        },
        "decision_stability": {
            "structure_status": "PASS" if corpus_structure["stability_pair_groups"] >= 1 and not corpus_structure["relation_errors"] else "FAIL",
            "relations_status": "PASS" if corpus_structure["stability_relations"] and not corpus_structure["relation_errors"] else "FAIL",
            "execution_status": "BLOCKED",
            "reason": "Framework/wording/scale stability requires model output.",
        },
        "status": "BLOCKED",
        "errors": corpus_structure["relation_errors"],
    }
    if report["errors"]:
        report["status"] = "FAIL"
    if args.response_file:
        report["response_file"] = str(Path(args.response_file).resolve())
        report["status"] = "NOT_RUN"
        report["errors"].append("Response comparison adapter is not implemented by this structural runner; use the behavioral evaluator capture.")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--response-file")
    parser.add_argument("--output", help="write the JSON evidence artifact to this path")
    args = parser.parse_args()
    try:
        result = run(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"scope": "GENERALIZATION_GATES", "status": "FAIL", "errors": [str(exc)]}
    encoded = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    raise SystemExit(0 if result.get("status") in {"PASS", "BLOCKED", "NOT_RUN"} else 1)
