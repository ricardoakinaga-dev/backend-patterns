#!/usr/bin/env python3
"""Run causal mutation checks against the public-input reference router."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
ROUTER = ROOT / "scripts" / "run-context-efficiency.py"


def load_router():
    spec = importlib.util.spec_from_file_location("backend_patterns_context_router", ROUTER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load router: {ROUTER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run() -> dict:
    router = load_router()
    scenarios = router.load_scenarios()
    package_refs = {path.name for path in (ROOT / "references").glob("*.md")}
    checks: list[dict] = []

    def record(name: str, passed: bool, details: dict) -> None:
        checks.append({"name": name, "status": "PASS" if passed else "FAIL", **details})

    baseline_routes = {
        str(scenario["id"]): tuple(router.route(scenario)) for scenario in scenarios
    }
    route_refs_valid = all(set(route).issubset(package_refs) for route in baseline_routes.values())
    record(
        "references-stay-inside-package",
        route_refs_valid,
        {"invalid_references": sorted({ref for route in baseline_routes.values() for ref in set(route) - package_refs})},
    )

    # A router must not change when evaluator-only/gold fields are added to the
    # same public task. This is a direct anti-leakage mutation test.
    gold_fields = {
        "family": "mutated-family",
        "split": "mutated-split",
        "expected_decision": "mutated-decision",
        "recommended_references": ["references/security-boundaries.md"],
        "known_bad_mutations": ["mutated-oracle"],
        "routing_relevance": {"mutated": "gold"},
    }
    leakage_failures = []
    for scenario in scenarios:
        mutated = copy.deepcopy(scenario)
        mutated.update(gold_fields)
        original = baseline_routes[str(scenario["id"])]
        changed = tuple(router.route(mutated))
        if changed != original:
            leakage_failures.append(str(scenario["id"]))
    record("gold-fields-do-not-change-route", not leakage_failures, {"changed_scenarios": leakage_failures})

    mutation_specs = (
        ("disable-legacy-text", {"legacy-text"}),
        ("disable-effect-safety-bundle", {"effect-safety"}),
        ("disable-atomic-effect-bundle", {"atomic-effect-boundary"}),
        ("disable-migration-bundle", {"migration-compatibility"}),
    )
    for name, disabled in mutation_specs:
        changed = []
        for scenario in scenarios:
            scenario_id = str(scenario["id"])
            mutated_route = tuple(router.route_with_trace(scenario, disabled)["references"])
            if mutated_route != baseline_routes[scenario_id]:
                changed.append(scenario_id)
        record(
            name,
            bool(changed),
            {"changed_scenarios": changed, "disabled_bundles": sorted(disabled)},
        )

    # The prohibited load-all mutant must be observably different from the
    # bounded route for at least one scenario and must be rejected as a policy.
    all_references = tuple(sorted(package_refs))
    load_all_changed = [
        scenario_id
        for scenario_id, route in baseline_routes.items()
        if tuple(route) != all_references
    ]
    record(
        "load-all-mutant-is-not-the-router",
        bool(load_all_changed),
        {"bounded_scenarios": load_all_changed[:10], "package_reference_count": len(all_references)},
    )

    router_globals = router.run.__globals__
    original_context_bytes = router_globals["_context_bytes"]
    router_globals["_context_bytes"] = lambda _loaded: 10_000_000
    try:
        oversized_report = router.run()
    finally:
        router_globals["_context_bytes"] = original_context_bytes
    record(
        "context-growth-bound-rejects-mutant",
        oversized_report.get("status") == "FAIL" and oversized_report.get("context_growth_within_bound") is False,
        {
            "mutated_context_bytes": 10_000_000,
            "observed_status": oversized_report.get("status"),
            "context_growth_within_bound": oversized_report.get("context_growth_within_bound"),
        },
    )

    failed = [item["name"] for item in checks if item["status"] != "PASS"]
    return {
        "scope": "ROUTING_CAUSAL_MUTATIONS",
        "status": "PASS" if not failed else "FAIL",
        "mutation_count": len(checks),
        "passed": len(checks) - len(failed),
        "failed": len(failed),
        "checks": checks,
        "router_version": getattr(router, "ROUTER_VERSION", "unknown"),
        "errors": failed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="write JSON evidence to this path")
    args = parser.parse_args()
    try:
        report = run()
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        report = {"scope": "ROUTING_CAUSAL_MUTATIONS", "status": "FAIL", "errors": [str(exc)]}
    encoded = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    raise SystemExit(0 if report.get("status") == "PASS" else 1)
