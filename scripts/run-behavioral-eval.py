#!/usr/bin/env python3
"""Run or ingest a control/treatment consumer-model evaluation.

The repository does not assume a model SDK. A host adapter may be supplied via
--adapter-command or BACKEND_PATTERNS_MODEL_ADAPTER. Without one the runner
returns BLOCKED with the exact missing capability instead of fabricating a
behavioral result.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "tests" / "benchmark" / "scenarios.json"
RUBRIC = ROOT / "tests" / "benchmark" / "rubric.json"
SCORE = ROOT / "scripts" / "score-responses.py"
STATUS = ("PASS", "FAIL", "NOT_RUN", "BLOCKED", "STALE", "NOT_APPLICABLE")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_fingerprint() -> str:
    digest = hashlib.sha256()
    paths = [ROOT / "SKILL.md", ROOT / "README.md", ROOT / "composition-contract.json"]
    paths.extend((ROOT / name).rglob("*") for name in ("references", "scripts", "tests"))
    flattened = []
    for group in paths:
        if isinstance(group, Path):
            flattened.append(group)
        else:
            flattened.extend(group)
    for path in sorted(path for path in flattened if path.is_file() and ".pyc" not in path.name and "__pycache__" not in path.parts):
        relative = path.relative_to(ROOT).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


PUBLIC_SCENARIO_FIELDS = ("prompt", "current_facts", "unknowns", "invariants", "forces")
GOLD_SCENARIO_FIELDS = (
    "id",
    "family",
    "title",
    "split",
    "expected_decision",
    "required_signals",
    "hard_fail_tags",
    "domains",
    "recommended_references",
    "metamorphic_group",
    "stability_group",
    "known_bad_mutations",
    "simpler_baseline",
)


def request_payload(split: str | None, limit: int | None) -> tuple[dict, dict[str, str]]:
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    if split:
        scenarios = [item for item in scenarios if item.get("split") == split]
    if limit is not None:
        scenarios = scenarios[:limit]
    public_scenarios = []
    public_to_internal: dict[str, str] = {}
    for index, scenario in enumerate(scenarios, start=1):
        public_id = f"case-{index:03d}"
        public_to_internal[public_id] = str(scenario["id"])
        public_scenarios.append(
            {
                "scenario_id": public_id,
                **{field: scenario.get(field, []) for field in PUBLIC_SCENARIO_FIELDS},
            }
        )
    return {
        "protocol": "backend-patterns-behavioral-eval-v1",
        "instruction": "Return one JSON response record for each opaque scenario_id in both control and treatment lanes. Control must not read backend-patterns; treatment may read the supplied package. Do not edit files. The supplied task projection intentionally excludes the answer key and benchmark metadata.",
        "package_root": str(ROOT),
        "scenarios": public_scenarios,
        "public_fields": list(PUBLIC_SCENARIO_FIELDS),
        "redacted_gold_fields": list(GOLD_SCENARIO_FIELDS),
        "lanes": ["control", "treatment"],
        "same_model_required": True,
    }, public_to_internal


def normalize_adapter_response(raw: str, public_to_internal: dict[str, str]) -> str:
    """Translate opaque adapter IDs back to the private scoring corpus IDs."""
    response = json.loads(raw)
    if not isinstance(response, list) or not all(isinstance(item, dict) for item in response):
        raise ValueError("adapter output must be a JSON array of response records")
    normalized = []
    for index, record in enumerate(response):
        item = dict(record)
        supplied_id = str(item.get("scenario_id", ""))
        if supplied_id in public_to_internal:
            item["scenario_id"] = public_to_internal[supplied_id]
        else:
            raise ValueError(f"adapter record {index} contains unknown or non-opaque scenario_id: {supplied_id}")
        normalized.append(item)
    return json.dumps(normalized, ensure_ascii=False)


def run_adapter(command: str, payload: dict) -> tuple[str, str]:
    try:
        completed = subprocess.run(
            shlex.split(command),
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            cwd=ROOT,
            check=False,
        )
    except OSError as exc:
        return "BLOCKED", f"adapter could not start: {exc}"
    if completed.returncode != 0:
        return "FAIL", f"adapter exited {completed.returncode}: {(completed.stderr or completed.stdout).strip()[-1000:]}"
    return "EXECUTED", completed.stdout


def score(response_file: Path) -> dict:
    if not SCORE.is_file():
        return {"status": "FAIL", "errors": [f"missing scorer: {SCORE.relative_to(ROOT)}"]}
    result = subprocess.run(
        [sys.executable, "-B", str(SCORE), "--response-file", str(response_file), "--scenario-file", str(SCENARIOS), "--rubric-file", str(RUBRIC)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "FAIL", "errors": ["scorer returned non-JSON", result.stdout[-1000:], result.stderr[-1000:]]}
    parsed["scorer_exit_status"] = result.returncode
    return parsed


def run(args: argparse.Namespace) -> dict:
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8")) if SCENARIOS.is_file() else []
    payload, public_to_internal = request_payload(args.split, args.limit)
    response_file = Path(args.response_file).resolve() if args.response_file else None
    adapter_status = "NOT_RUN"
    adapter_note = ""
    if response_file is None:
        command = args.adapter_command or __import__("os").environ.get("BACKEND_PATTERNS_MODEL_ADAPTER")
        if not command:
            return {
                "scope": "BEHAVIORAL_MODEL_EVAL",
                "status": "BLOCKED",
                "model_execution": "BLOCKED",
                "reason": "No consumer-model adapter was supplied.",
                "required_host_capability": "An adapter that invokes the same model in control and treatment lanes and returns JSON response records.",
                "evidence_unavailable": "control/treatment responses, scores, pairwise judgments and causal delta",
                "impact_on_verdict": "TRIPLE_A_PROVEN is ineligible; use TRIPLE_A_CONDITIONAL at most.",
                "scenario_count": len(payload["scenarios"]),
                "split": args.split,
                "package_fingerprint": package_fingerprint(),
                "benchmark_fingerprint": sha256(SCENARIOS) if SCENARIOS.is_file() else None,
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "errors": [],
            }
        adapter_status, adapter_output = run_adapter(command, payload)
        adapter_note = adapter_output
        if adapter_status == "BLOCKED":
            return {
                "scope": "BEHAVIORAL_MODEL_EVAL", "status": "BLOCKED", "model_execution": "BLOCKED",
                "reason": adapter_output, "required_host_capability": "working consumer-model adapter",
                "impact_on_verdict": "TRIPLE_A_PROVEN is ineligible", "errors": [],
            }
        if adapter_status != "EXECUTED":
            return {"scope": "BEHAVIORAL_MODEL_EVAL", "status": "FAIL", "model_execution": "FAIL", "reason": adapter_output, "errors": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as capture:
            capture.write(normalize_adapter_response(adapter_note, public_to_internal))
            capture.flush()
            scored = score(Path(capture.name))
    else:
        scored = score(response_file)
    score_status = scored.get("status")
    result_status = score_status if score_status in {"PASS", "FAIL", "BLOCKED", "NOT_RUN", "STALE", "NOT_APPLICABLE"} else "FAIL"
    return {
        "scope": "BEHAVIORAL_MODEL_EVAL",
        "status": result_status,
        "model_execution": "PASS" if adapter_status in {"EXECUTED", "NOT_RUN"} and result_status == "PASS" else adapter_status,
        "scenario_count": len(payload["scenarios"]),
        "split": args.split,
        "package_fingerprint": package_fingerprint(),
        "benchmark_fingerprint": sha256(SCENARIOS),
        "rubric_fingerprint": sha256(RUBRIC),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "scoring": scored,
        "errors": scored.get("errors", []),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter-command")
    parser.add_argument("--response-file")
    parser.add_argument("--split", choices=["development", "adversarial", "holdout"])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", help="write the JSON evidence artifact to this path")
    args = parser.parse_args()
    try:
        result = run(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"scope": "BEHAVIORAL_MODEL_EVAL", "status": "FAIL", "model_execution": "FAIL", "errors": [str(exc)]}
    encoded = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    raise SystemExit(0 if result.get("status") in {"PASS", "BLOCKED", "NOT_RUN"} else 1)
