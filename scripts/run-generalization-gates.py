#!/usr/bin/env python3
"""Report structural and executable generalization gates for the benchmark.

Structural relations are checked from the private corpus. Optional response
capture is checked through the behavioral evaluator's versioned, opaque-ID
protocol. Response comparisons expose first-result observations and response
digests only; this runner never calls the rubric scorer and never infers a
model score or a gold decision.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "tests" / "benchmark" / "scenarios.json"
FINAL = ROOT / "tests" / "benchmark" / "final-gauntlet.json"
RELATIONS = ROOT / "tests" / "benchmark" / "relations.json"
BEHAVIORAL = ROOT / "scripts" / "run-behavioral-eval.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def behavioral_module() -> Any:
    spec = importlib.util.spec_from_file_location("backend_patterns_behavioral_eval", BEHAVIORAL)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load behavioral capture protocol")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def _capture_digest(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "source": "supplied_response_file",
    }


def _record_observation(record: dict[str, Any]) -> dict[str, Any]:
    text = record.get("text")
    text_bytes = text.encode("utf-8") if isinstance(text, str) else b""
    decision = record.get("decision")
    return {
        "scenario_id": record.get("scenario_id"),
        "lane": record.get("lane"),
        "status": record.get("status"),
        "decision": decision if isinstance(decision, str) else None,
        "text_sha256": sha256_bytes(text_bytes),
        "text_present": bool(text_bytes.strip()),
    }


def _records_by_key(records: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(record.get("scenario_id")), str(record.get("lane"))): record for record in records}


def _group_comparisons(
    label: str,
    groups: dict[str, list[str]],
    records: list[dict[str, Any]],
    lane: str = "treatment",
) -> dict[str, Any]:
    by_key = _records_by_key(records)
    observations: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for group, identifiers in sorted(groups.items()):
        selected = [by_key.get((identifier, lane)) for identifier in identifiers]
        if any(record is None for record in selected):
            missing.append(
                {
                    "group": group,
                    "lane": lane,
                    "missing_scenario_ids": [identifier for identifier, record in zip(identifiers, selected) if record is None],
                }
            )
            continue
        if any(str(record.get("status")) not in {"PASS", "FAIL", "EXECUTED", "COMPLETED", "DONE", "SUCCESS"} for record in selected):
            missing.append({"group": group, "lane": lane, "reason": "one or more captured records are not executed"})
            continue
        entries = [_record_observation(record) for record in selected]
        decisions = [entry["decision"] for entry in entries]
        known_decisions = [value for value in decisions if value is not None]
        text_digests = [entry["text_sha256"] for entry in entries]
        observations.append(
            {
                "group": group,
                "lane": lane,
                "scenario_ids": identifiers,
                "first_result_only": True,
                "records": entries,
                "decision_values": decisions,
                "distinct_decision_count": len(set(known_decisions)),
                "decision_consistent": (len(set(known_decisions)) <= 1) if known_decisions else None,
                "response_changed": len(set(text_digests)) > 1,
                "comparison_status": "OBSERVED_NOT_SCORED",
            }
        )
    return {
        "response_execution": "PASS" if not missing and observations else "BLOCKED",
        "comparison_status": "OBSERVED_NOT_SCORED" if not missing and observations else "INSUFFICIENT_CAPTURE",
        "lane": lane,
        "first_result_discipline": "first_result_only",
        "groups_observed": len(observations),
        "groups_required": len(groups),
        "observations": observations,
        "missing": missing,
        "scores": "NOT_INFERRED",
    }


def _holdout_comparison(scenarios: list[dict], records: list[dict[str, Any]]) -> dict[str, Any]:
    holdout_ids = [str(item["id"]) for item in scenarios if item.get("split") == "holdout"]
    by_key = _records_by_key(records)
    missing = [
        {"scenario_id": identifier, "lane": lane}
        for identifier in holdout_ids
        for lane in ("control", "treatment")
        if (identifier, lane) not in by_key
    ]
    non_executed = [
        {"scenario_id": identifier, "lane": lane, "status": by_key[(identifier, lane)].get("status")}
        for identifier in holdout_ids
        for lane in ("control", "treatment")
        if (identifier, lane) in by_key
        and str(by_key[(identifier, lane)].get("status")) not in {"PASS", "FAIL", "EXECUTED", "COMPLETED", "DONE", "SUCCESS"}
    ]
    if missing or non_executed:
        return {
            "structure_status": "PASS" if len(holdout_ids) >= 1 else "FAIL",
            "response_execution": "BLOCKED",
            "comparison_status": "INSUFFICIENT_CAPTURE",
            "first_result_discipline": "first_result_only",
            "records_considered": 0,
            "missing": missing,
            "non_executed": non_executed,
            "reason": "Holdout comparison requires one executed first result per holdout scenario in both lanes.",
            "scores": "NOT_INFERRED",
        }
    first_results = [
        _record_observation(by_key[(identifier, lane)])
        for identifier in holdout_ids
        for lane in ("control", "treatment")
    ]
    return {
        "structure_status": "PASS",
        "response_execution": "PASS",
        "comparison_status": "OBSERVED_NOT_SCORED",
        "first_result_discipline": "first_result_only",
        "records_considered": len(first_results),
        "first_results": first_results,
        "missing": [],
        "scores": "NOT_INFERRED",
    }


def _minimality_comparison(comparisons: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    items = comparisons.get("minimality", [])
    if not items:
        return {
            "structure_status": "NOT_DEFINED",
            "response_execution": "BLOCKED",
            "comparison_status": "INSUFFICIENT_CAPTURE",
            "reason": "Minimality requires an explicit baseline/candidate comparison capture; no rubric baseline is joined or inferred.",
            "scores": "NOT_INFERRED",
        }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[str(item.get("comparison_id"))].append(item)
    observations = []
    missing = []
    for comparison_id, values in sorted(grouped.items()):
        variants = {str(item.get("variant")) for item in values}
        if len(variants) < 2:
            missing.append({"comparison_id": comparison_id, "reason": "requires at least two explicit variants"})
            continue
        observations.append(
            {
                "comparison_id": comparison_id,
                "variants": sorted(variants),
                "responses": [_record_observation(item) for item in values],
                "comparison_status": "OBSERVED_NOT_SCORED",
            }
        )
    return {
        "structure_status": "PASS",
        "response_execution": "PASS" if observations and not missing else "BLOCKED",
        "comparison_status": "OBSERVED_NOT_SCORED" if observations and not missing else "INSUFFICIENT_CAPTURE",
        "observations": observations,
        "missing": missing,
        "scores": "NOT_INFERRED",
    }


def _final_gauntlet(final: dict, records: list[dict[str, Any]]) -> dict[str, Any]:
    required = [str(item.get("scenario_id")) for item in final.get("cases", [])]
    by_key = _records_by_key(records)
    missing = [
        {"scenario_id": identifier, "lane": lane}
        for identifier in required
        for lane in ("control", "treatment")
        if (identifier, lane) not in by_key
    ]
    return {
        "count": len(required),
        "structure_status": "PASS" if len(required) == 20 else "FAIL",
        "response_execution": "PASS" if not missing and required else "BLOCKED",
        "comparison_status": "OBSERVED_NOT_SCORED" if not missing and required else "INSUFFICIENT_CAPTURE",
        "missing": missing,
        "scores": "NOT_INFERRED",
    }


def _blocked_response_sections(structure_data: dict[str, Any], final: dict) -> dict[str, Any]:
    reason = "No consumer-model response capture was supplied."
    return {
        "final_gauntlet": {
            "count": len(final.get("cases", [])),
            "structure_status": "PASS" if len(final.get("cases", [])) == 20 else "FAIL",
            "response_execution": "BLOCKED",
            "comparison_status": "NOT_RUN",
            "reason": reason,
            "scores": "NOT_INFERRED",
        },
        "holdout": {
            "structure_status": "PASS" if structure_data["split_counts"]["holdout"] >= 1 else "FAIL",
            "response_execution": "BLOCKED",
            "comparison_status": "NOT_RUN",
            "first_result_discipline": "first_result_only_required",
            "reason": reason,
            "scores": "NOT_INFERRED",
        },
        "metamorphic": {
            "structure_status": "PASS" if structure_data["metamorphic_pair_groups"] >= 1 and not structure_data["relation_errors"] else "FAIL",
            "relations_status": "PASS" if structure_data["metamorphic_relations"] and not structure_data["relation_errors"] else "FAIL",
            "response_execution": "BLOCKED",
            "comparison_status": "NOT_RUN",
            "reason": "Pairwise response comparison requires an identified consumer-model capture.",
            "scores": "NOT_INFERRED",
        },
        "minimality": {
            "structure_status": "NOT_DEFINED",
            "response_execution": "BLOCKED",
            "comparison_status": "NOT_RUN",
            "reason": "Minimality requires an explicit baseline/candidate comparison capture.",
            "scores": "NOT_INFERRED",
        },
        "decision_stability": {
            "structure_status": "PASS" if structure_data["stability_pair_groups"] >= 1 and not structure_data["relation_errors"] else "FAIL",
            "relations_status": "PASS" if structure_data["stability_relations"] and not structure_data["relation_errors"] else "FAIL",
            "response_execution": "BLOCKED",
            "comparison_status": "NOT_RUN",
            "reason": "Framework/wording/scale stability requires identified model responses.",
            "scores": "NOT_INFERRED",
        },
    }


def run(args: argparse.Namespace) -> dict:
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    final = json.loads(FINAL.read_text(encoding="utf-8"))
    relations = json.loads(RELATIONS.read_text(encoding="utf-8"))
    corpus_structure = structure(scenarios, relations)
    final_count = len(final.get("cases", []))
    behavioral = behavioral_module()
    payload, public_to_internal = behavioral.request_payload(None, None)
    fingerprints = {
        "corpus_sha256": sha256(SCENARIOS),
        "package_sha256": behavioral.package_fingerprint(),
    }
    report: dict[str, Any] = {
        "scope": "GENERALIZATION_GATES",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "model_execution": "NOT_INFERRED",
        "response_execution": "BLOCKED",
        "reason": "No consumer-model response capture was supplied.",
        "corpus_fingerprint": fingerprints["corpus_sha256"],
        "package_fingerprint": fingerprints["package_sha256"],
        "structure": corpus_structure,
        "response_comparison_policy": {
            "scores": "NOT_INFERRED",
            "holdout": "first_result_only",
            "lane": "treatment comparisons are paired with control capture; no expected decision is joined",
        },
    }

    if not args.response_file:
        report.update(_blocked_response_sections(corpus_structure, final))
        report["status"] = "FAIL" if report["structure"]["relation_errors"] else "BLOCKED"
        report["errors"] = corpus_structure["relation_errors"]
        return report

    response_path = Path(args.response_file).resolve()
    if not response_path.is_file():
        report.update(_blocked_response_sections(corpus_structure, final))
        report.update(
            {
                "response_execution": "INVALID",
                "response_capture": None,
                "status": "INVALID",
                "errors": [f"supplied response file does not exist: {response_path}"],
            }
        )
        return report

    try:
        raw = response_path.read_text(encoding="utf-8")
        capture = behavioral.validate_adapter_capture(
            raw,
            public_to_internal,
            expected_fingerprints=fingerprints,
            require_holdout_first_result=True,
        )
    except (OSError, behavioral.AdapterValidationError) as exc:
        report.update(_blocked_response_sections(corpus_structure, final))
        report.update(
            {
                "response_execution": "INVALID",
                "response_capture": {"path": str(response_path), "sha256": sha256(response_path), "bytes": response_path.stat().st_size, "source": "supplied_response_file"},
                "status": "INVALID",
                "errors": list(getattr(exc, "errors", [str(exc)])),
            }
        )
        return report

    report["model_execution"] = "EXECUTED_NOT_SCORED"
    report["response_execution"] = "PASS"
    report["response_capture"] = {
        **_capture_digest(response_path),
        "identity": {
            "consumer_identity": capture["metadata"]["consumer_identity"],
            "consumer_version": capture["metadata"]["consumer_version"],
            "adapter_identity": capture["metadata"]["adapter_identity"],
            "adapter_version": capture["metadata"]["adapter_version"],
            "model_identity": capture["metadata"]["model_identity"],
            "model_version": capture["metadata"]["model_version"],
            "capture_status": capture["metadata"]["capture_status"],
        },
        "fingerprints": capture["metadata"]["fingerprints"],
        "fairness": capture["fairness"],
    }
    records = capture["records"]
    metamorphic = _group_comparisons("metamorphic", corpus_structure["metamorphic_groups"], records)
    stability = _group_comparisons("stability", corpus_structure["stability_groups"], records)
    report["holdout"] = _holdout_comparison(scenarios, records)
    report["final_gauntlet"] = _final_gauntlet(final, records)
    report["metamorphic"] = {
        "structure_status": "PASS" if corpus_structure["metamorphic_pair_groups"] >= 1 and not corpus_structure["relation_errors"] else "FAIL",
        "relations_status": "PASS" if corpus_structure["metamorphic_relations"] and not corpus_structure["relation_errors"] else "FAIL",
        **metamorphic,
    }
    report["minimality"] = _minimality_comparison(capture["comparisons"])
    report["decision_stability"] = {
        "structure_status": "PASS" if corpus_structure["stability_pair_groups"] >= 1 and not corpus_structure["relation_errors"] else "FAIL",
        "relations_status": "PASS" if corpus_structure["stability_relations"] and not corpus_structure["relation_errors"] else "FAIL",
        **stability,
    }

    response_statuses = [
        report["holdout"]["response_execution"],
        report["final_gauntlet"]["response_execution"],
        report["metamorphic"]["response_execution"],
        report["minimality"]["response_execution"],
        report["decision_stability"]["response_execution"],
    ]
    if corpus_structure["relation_errors"]:
        report["status"] = "FAIL"
    elif "INVALID" in response_statuses:
        report["status"] = "INVALID"
    elif all(value == "PASS" for value in response_statuses):
        report["status"] = "PASS"
    else:
        report["status"] = "BLOCKED"
    report["errors"] = corpus_structure["relation_errors"]
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--response-file", help="identified v2 consumer-model capture for response comparison")
    parser.add_argument("--output", help="write the JSON evidence artifact to this path")
    args = parser.parse_args()
    try:
        result = run(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"scope": "GENERALIZATION_GATES", "status": "INVALID", "response_execution": "INVALID", "errors": [str(exc)]}
    encoded = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    raise SystemExit(0 if result.get("status") in {"PASS", "BLOCKED", "NOT_RUN"} else 1)
