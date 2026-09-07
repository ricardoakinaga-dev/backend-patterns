#!/usr/bin/env python3
"""Run response-level known-bad mutations against the deterministic scorer.

This is a causal sensitivity oracle for captured response text.  It does not
claim model execution: each oracle starts from a deliberately safe response,
applies one named mutation, and requires the relevant hard-fail tag or a
material score drop.
"""

from __future__ import annotations

from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "tests" / "benchmark" / "scenarios.json"
RUBRIC = ROOT / "tests" / "benchmark" / "rubric.json"
ORACLES = ROOT / "tests" / "fixtures" / "response-oracles.json"
SCORER = ROOT / "scripts" / "score-responses.py"


def load_scorer():
    spec = importlib.util.spec_from_file_location("backend_patterns_response_scorer", SCORER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load scorer: {SCORER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def materialize(case: dict, text: str, scenario: dict, *, mutation: bool) -> str:
    # Keep the captured response body unchanged. The shared task context is
    # passed separately to both lanes by record(), so the causal comparison
    # has one fixed covariate and one changed response body.
    return text


def shared_context(scenario: dict) -> str:
    parts = []
    for key in ("current_facts", "unknowns", "invariants", "forces", "simpler_baseline", "required_signals"):
        value = scenario.get(key, [])
        rendered = ". ".join(str(item) for item in value) if isinstance(value, list) else str(value)
        if rendered:
            parts.append(f"{key}: {rendered}")
    return "\n".join(parts)


def record(case: dict, text: str, context: str) -> dict:
    return {
        "scenario_id": case["scenario_id"],
        "lane": "mutation-oracle",
        "model": "deterministic-response-oracle",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "text": text,
        "scoring_context": context,
    }


def body_shape(baseline: str, mutated: str) -> dict:
    baseline_tokens = set(re.findall(r"[a-z0-9]+", baseline.lower()))
    mutated_tokens = set(re.findall(r"[a-z0-9]+", mutated.lower()))
    union = baseline_tokens | mutated_tokens
    return {
        "sequence_ratio": round(difflib.SequenceMatcher(None, baseline, mutated, autojunk=False).ratio(), 4),
        "token_jaccard": round(len(baseline_tokens & mutated_tokens) / len(union), 4) if union else 1.0,
        "changed_token_count": len(baseline_tokens ^ mutated_tokens),
    }


def run() -> dict:
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    rubric = json.loads(RUBRIC.read_text(encoding="utf-8"))
    cases = json.loads(ORACLES.read_text(encoding="utf-8"))
    if not isinstance(scenarios, list) or not isinstance(cases, list):
        raise ValueError("scenarios and response oracles must be arrays")
    scenarios_by_id = {str(item["id"]): item for item in scenarios}
    scorer = load_scorer()
    metadata = scorer.rubric_dimension_metadata(rubric)
    results = []
    errors = []
    for case in cases:
        scenario_id = str(case.get("scenario_id", ""))
        scenario = scenarios_by_id.get(scenario_id)
        if scenario is None:
            errors.append(f"{case.get('id')}: unknown scenario {scenario_id}")
            continue
        baseline_text = materialize(case, case.get("baseline", ""), scenario, mutation=False)
        mutated_text = materialize(case, case.get("mutated", ""), scenario, mutation=True)
        shape = body_shape(baseline_text, mutated_text)
        context = shared_context(scenario)
        baseline = scorer.score_record(record(case, baseline_text, context), {scenario_id: scenario}, rubric, metadata)
        mutated = scorer.score_record(record(case, mutated_text, context), {scenario_id: scenario}, rubric, metadata)
        baseline_score = baseline.get("average_0_4")
        mutated_score = mutated.get("average_0_4")
        delta = (float(baseline_score) - float(mutated_score)) if baseline_score is not None and mutated_score is not None else None
        tags = {item.get("canonical_tag") for item in mutated.get("hard_failures", [])}
        expected_tag = case.get("expected_tag")
        tag_hit = expected_tag in tags if expected_tag else False
        minimum_delta = float(case.get("min_score_delta", 0.1))
        causal = tag_hit or (delta is not None and delta >= minimum_delta)
        baseline_safe = baseline.get("status") == "PASS" and not baseline.get("hard_failures") and baseline_score is not None
        min_sequence_ratio = float(case.get("min_sequence_ratio", 0.65))
        min_token_jaccard = float(case.get("min_token_jaccard", 0.65))
        shape_safe = shape["sequence_ratio"] >= min_sequence_ratio and shape["token_jaccard"] >= min_token_jaccard
        mutation_metadata_safe = bool(case.get("mutation_operator")) and bool(case.get("preserved_contract"))
        passed = baseline_safe and causal and mutated.get("status") == "FAIL" and shape_safe and mutation_metadata_safe
        result = {
            "id": case.get("id"),
            "scenario_id": scenario_id,
            "mutation": case.get("mutation"),
            "status": "PASS" if passed else "FAIL",
            "baseline_status": baseline.get("status"),
            "baseline_safe": baseline_safe,
            "mutated_status": mutated.get("status"),
            "baseline_average_0_4": baseline_score,
            "mutated_average_0_4": mutated_score,
            "score_delta_0_4": round(delta, 4) if delta is not None else None,
            "expected_tag": expected_tag,
            "observed_tags": sorted(tag for tag in tags if tag),
            "tag_hit": tag_hit,
            "minimum_score_delta": minimum_delta,
            "causal_sensitivity": causal,
            "mutation_operator": case.get("mutation_operator"),
            "preserved_contract": case.get("preserved_contract"),
            "body_shape": shape,
            "body_shape_thresholds": {
                "min_sequence_ratio": min_sequence_ratio,
                "min_token_jaccard": min_token_jaccard,
            },
            "body_shape_safe": shape_safe,
            "mutation_metadata_safe": mutation_metadata_safe,
            "shared_context_held_constant": True,
            "shared_context_sha256": hashlib.sha256(context.encode("utf-8")).hexdigest(),
        }
        if not passed:
            errors.append(
                f"{case.get('id')}: baseline={baseline.get('status')} mutated={mutated.get('status')} "
                f"tag_hit={tag_hit} delta={result['score_delta_0_4']} shape={shape}"
            )
        results.append(result)
    status = "PASS" if cases and not errors else "FAIL"
    return {
        "scope": "RESPONSE_LEVEL_MUTATION_ORACLES",
        "status": status,
        "model_execution": "NOT_INFERRED",
        "oracle_count": len(cases),
        "passed": sum(item["status"] == "PASS" for item in results),
        "failed": sum(item["status"] == "FAIL" for item in results),
        "errors": errors,
        "results": results,
        "fingerprints": {
            "scenario_file": __import__("hashlib").sha256(SCENARIOS.read_bytes()).hexdigest(),
            "rubric_file": __import__("hashlib").sha256(RUBRIC.read_bytes()).hexdigest(),
            "oracle_file": __import__("hashlib").sha256(ORACLES.read_bytes()).hexdigest(),
        },
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="write the JSON evidence artifact to this path")
    args = parser.parse_args()
    try:
        report = run()
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        report = {"scope": "RESPONSE_LEVEL_MUTATION_ORACLES", "status": "FAIL", "errors": [str(exc)]}
    encoded = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    raise SystemExit(0 if report.get("status") == "PASS" else 1)
