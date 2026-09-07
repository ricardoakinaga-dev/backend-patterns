#!/usr/bin/env python3
"""Validate the phase-1.1 architectural judgment corpus and rubric."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
BENCHMARK = ROOT / "tests" / "benchmark"
SCENARIOS = BENCHMARK / "scenarios.json"
RUBRIC = BENCHMARK / "rubric.json"
FINAL = BENCHMARK / "final-gauntlet.json"
RELATIONS = BENCHMARK / "relations.json"
ALLOWED_STANCES = {"SHOULD_USE", "SHOULD_REJECT", "NEED_MORE_EVIDENCE"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        rubric = load(RUBRIC)
        scenarios = load(SCENARIOS)
        final = load(FINAL)
        relations = load(RELATIONS)
    except (OSError, json.JSONDecodeError) as exc:
        return {"scope": "BENCHMARK_CORPUS", "status": "FAIL", "errors": [str(exc)], "warnings": []}

    if not isinstance(rubric, dict):
        errors.append("rubric must be an object")
        rubric = {}
    if not isinstance(scenarios, list):
        errors.append("scenarios must be an array")
        scenarios = []
    if not isinstance(final, dict) or not isinstance(final.get("cases"), list):
        errors.append("final-gauntlet must contain a cases array")
        final_cases = []
    else:
        final_cases = final["cases"]
    if not isinstance(relations, dict):
        errors.append("relations must be an object")
        relations = {}

    required_fields = set(rubric.get("required_fields", []))
    required_families = set(rubric.get("required_families", []))
    required_splits = set(rubric.get("required_splits", []))
    required_domains = set(rubric.get("required_domains", []))
    required_tags = set(rubric.get("required_tags", []))
    minimums = rubric.get("minimums", {})
    thresholds = rubric.get("thresholds", {})

    ids: set[str] = set()
    prompts: set[str] = set()
    family_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    domains: set[str] = set()
    tags: set[str] = set()
    decision_signatures: list[str] = []
    metamorphic: dict[str, list[str]] = {}
    stability: dict[str, list[str]] = {}
    preferred_components: Counter[str] = Counter()
    rejected_components: Counter[str] = Counter()
    mutation_diagnostics: Counter[str] = Counter()
    for index, scenario in enumerate(scenarios):
        prefix = f"scenarios[{index}]"
        if not isinstance(scenario, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = sorted(required_fields - set(scenario))
        if missing:
            errors.append(f"{prefix} missing fields: {', '.join(missing)}")
        identifier = scenario.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"{prefix}.id must be a non-empty string")
        elif identifier in ids:
            errors.append(f"duplicate scenario id: {identifier}")
        else:
            ids.add(identifier)
        prompt = str(scenario.get("prompt", "")).strip()
        prompt_key = " ".join(prompt.lower().split())
        if not prompt:
            errors.append(f"{prefix}.prompt must be non-empty")
        elif prompt_key in prompts:
            errors.append(f"duplicate prompt: {identifier}")
        prompts.add(prompt_key)
        family = scenario.get("family")
        split = scenario.get("split")
        family_counts[family] += 1
        split_counts[split] += 1
        if family not in required_families:
            errors.append(f"{prefix}.family is not required: {family}")
        if split not in required_splits:
            errors.append(f"{prefix}.split is not required: {split}")
        for field in ("current_facts", "unknowns", "invariants", "forces", "required_signals", "domains", "recommended_references", "known_bad_mutations"):
            value = scenario.get(field)
            if not isinstance(value, list) or not value:
                errors.append(f"{prefix}.{field} must be a non-empty array")
        domains.update(str(value) for value in scenario.get("domains", []) if isinstance(value, str))
        tags.update(str(value) for value in scenario.get("tags", []) if isinstance(value, str))
        decision = scenario.get("expected_decision")
        if not isinstance(decision, dict) or decision.get("stance") not in ALLOWED_STANCES:
            errors.append(f"{prefix}.expected_decision.stance is invalid")
        if not isinstance(decision, dict) or not decision.get("rationale"):
            errors.append(f"{prefix}.expected_decision.rationale is required")
        else:
            decision_signatures.append(json.dumps(decision, sort_keys=True, ensure_ascii=False))
            for component in decision.get("preferred", []):
                if isinstance(component, str) and component.strip():
                    preferred_components[component.strip().lower()] += 1
            for component in decision.get("rejected", []):
                if isinstance(component, str) and component.strip():
                    rejected_components[component.strip().lower()] += 1
        for key, store in (("metamorphic_group", metamorphic), ("stability_group", stability)):
            group = scenario.get(key)
            if group:
                store.setdefault(str(group), []).append(str(identifier))
        for mutation in scenario.get("known_bad_mutations", []):
            if not isinstance(mutation, dict) or not all(mutation.get(key) for key in ("id", "target", "expected", "diagnostic")):
                errors.append(f"{prefix}.known_bad_mutations contains an incomplete declaration")
            elif isinstance(mutation.get("diagnostic"), str):
                mutation_diagnostics[mutation["diagnostic"].strip().lower()] += 1

    min_scenarios = int(minimums.get("scenarios", 60))
    if len(scenarios) < min_scenarios:
        errors.append(f"scenario count {len(scenarios)} is below minimum {min_scenarios}")
    min_per_family = int(minimums.get("minimum_per_family", 8))
    for family in sorted(required_families):
        if family_counts[family] < min_per_family:
            errors.append(f"family {family} has {family_counts[family]}, minimum is {min_per_family}")
    holdout_fraction = float(minimums.get("holdout_fraction", 0.2))
    min_holdout = int(minimums.get("minimum_holdout", 1))
    if split_counts["holdout"] < min_holdout or split_counts["holdout"] / max(len(scenarios), 1) < holdout_fraction:
        errors.append(f"holdout count {split_counts['holdout']} is below required fraction/count")
    missing_domains = sorted(required_domains - domains)
    if missing_domains:
        errors.append("required domains missing: " + ", ".join(missing_domains))
    missing_tags = sorted(required_tags - tags)
    if missing_tags:
        errors.append("required tags missing: " + ", ".join(missing_tags))
    duplicate_decisions = len(decision_signatures) - len(set(decision_signatures))
    duplicate_decision_rate = duplicate_decisions / max(len(decision_signatures), 1)
    if float(thresholds.get("duplicate_decision_rate", 1.0)) < duplicate_decision_rate:
        errors.append(f"duplicate decision rate {duplicate_decision_rate:.4f} exceeds threshold")
    max_component_frequency = int(thresholds.get("max_decision_component_frequency", 8))
    repeated_components = {
        component: count
        for component, count in (preferred_components + rejected_components).items()
        if count > max_component_frequency
    }
    if repeated_components:
        errors.append("decision components are over-reused: " + ", ".join(f"{key} ({value})" for key, value in sorted(repeated_components.items())))
    max_diagnostic_frequency = int(thresholds.get("max_mutation_diagnostic_frequency", 2))
    repeated_diagnostics = {
        diagnostic: count
        for diagnostic, count in mutation_diagnostics.items()
        if count > max_diagnostic_frequency
    }
    if repeated_diagnostics:
        errors.append("mutation diagnostics are over-reused: " + ", ".join(f"{key} ({value})" for key, value in sorted(repeated_diagnostics.items())))
    generic_diagnostics = {"required signal", "generic evidence", "pattern chosen before evidence"}
    generic_found = sorted(generic_diagnostics.intersection(mutation_diagnostics))
    if generic_found:
        errors.append("generic mutation diagnostics are not allowed: " + ", ".join(generic_found))
    for label, groups in (("metamorphic", metamorphic), ("stability", stability)):
        for group, members in groups.items():
            if len(set(members)) < 2:
                errors.append(f"{label} group {group} has fewer than two scenarios")
        declared = relations.get(label, {}) if isinstance(relations.get(label, {}), dict) else {}
        missing_relations = sorted(set(groups) - set(declared))
        if missing_relations:
            errors.append(f"{label} groups missing explicit relations: {', '.join(missing_relations)}")
        for group in sorted(groups):
            relation = declared.get(group)
            if not isinstance(relation, dict) or not all(
                isinstance(relation.get(field), str) and relation[field].strip()
                for field in ("axis", "relation", "expected_behavior")
            ):
                errors.append(f"{label} relation {group} must define axis, relation, and expected_behavior")
    if len(metamorphic) < 1 or sum(len(set(values)) >= 2 for values in metamorphic.values()) < int(minimums.get("metamorphic_pairs", 1)):
        errors.append("not enough metamorphic pairs")
    if len(stability) < 1 or sum(len(set(values)) >= 2 for values in stability.values()) < int(minimums.get("stability_pairs", 1)):
        errors.append("not enough stability pairs")

    dimensions = rubric.get("dimensions", {})
    for number in range(1, 24):
        # The published rubric uses the human-facing D1..D23 identifiers.
        # Accept zero-padded aliases as well so machine consumers can remain
        # explicit without making the corpus schema ambiguous.
        key = f"D{number}"
        item = dimensions.get(key) or dimensions.get(f"D{number:02d}")
        if not isinstance(item, dict) or set(map(str, item.get("anchors", {}).keys())) != {"0", "1", "2", "3", "4"}:
            errors.append(f"rubric dimension {key} must have anchors 0..4")
    if not rubric.get("hard_fail_conditions"):
        errors.append("rubric hard_fail_conditions is empty")
    if thresholds.get("hard_safety_failures") != 0:
        errors.append("hard_safety_failures threshold must be zero")

    labels = [item.get("label") for item in final_cases if isinstance(item, dict)]
    expected_labels = list(rubric.get("required_final_case_labels", []))
    if len(final_cases) != int(minimums.get("final_gauntlet_cases", 20)):
        errors.append(f"final gauntlet has {len(final_cases)} cases, expected 20")
    if labels != expected_labels:
        errors.append("final gauntlet labels/order do not match rubric")
    unresolved = [item.get("scenario_id") for item in final_cases if item.get("scenario_id") not in ids]
    if unresolved:
        errors.append("final gauntlet has unresolved scenario IDs: " + ", ".join(str(item) for item in unresolved))
    if len(set(labels)) != len(labels):
        errors.append("final gauntlet labels are not unique")

    return {
        "scope": "BENCHMARK_CORPUS",
        "status": "PASS" if not errors else "FAIL",
        "scenario_count": len(scenarios),
        "family_counts": dict(sorted(family_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "domain_count": len(domains),
        "tag_count": len(tags),
        "duplicate_decision_count": duplicate_decisions,
        "duplicate_decision_rate": round(duplicate_decision_rate, 4),
        "decision_component_max_frequency": max(
            [*preferred_components.values(), *rejected_components.values()], default=0
        ),
        "decision_component_reuse_count": sum(
            max(count - 1, 0) for count in [*preferred_components.values(), *rejected_components.values()]
        ),
        "mutation_diagnostic_count": len(mutation_diagnostics),
        "mutation_diagnostic_max_frequency": max(mutation_diagnostics.values(), default=0),
        "metamorphic_groups": {key: sorted(set(value)) for key, value in sorted(metamorphic.items())},
        "stability_groups": {key: sorted(set(value)) for key, value in sorted(stability.items())},
        "metamorphic_relations": relations.get("metamorphic", {}),
        "stability_relations": relations.get("stability", {}),
        "final_gauntlet_count": len(final_cases),
        "errors": errors,
        "warnings": warnings,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="write the JSON evidence artifact to this path")
    args = parser.parse_args()
    result = validate()
    encoded = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    raise SystemExit(0 if result["status"] == "PASS" else 1)
