#!/usr/bin/env python3
"""Run or ingest a control/treatment consumer-model evaluation.

The repository does not assume a model SDK. A host adapter may be supplied via
``--adapter-command`` or ``BACKEND_PATTERNS_MODEL_ADAPTER``. The adapter
protocol is strict: it receives opaque scenario IDs, must return one record per
requested scenario and lane, and must identify the executed consumer/model/
adapter capture. Raw adapter stdout is persisted before any private scenario
join or scoring occurs.

The small ``normalize_adapter_response`` helper retains its historical
array-in/array-out compatibility for tests and local callers. The executable
runner uses ``validate_adapter_capture`` and therefore requires the versioned
capture envelope and all integrity metadata.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "tests" / "benchmark" / "scenarios.json"
RUBRIC = ROOT / "tests" / "benchmark" / "rubric.json"
SCORE = ROOT / "scripts" / "score-responses.py"
ADAPTER_PROTOCOL = "backend-patterns-behavioral-eval-v2"
LANES = ("control", "treatment")
STATUS = ("PASS", "FAIL", "NOT_RUN", "BLOCKED", "STALE", "NOT_APPLICABLE", "INVALID")
EXECUTED_STATUSES = {"PASS", "FAIL", "EXECUTED", "COMPLETED", "DONE", "SUCCESS"}
RECORD_STATUSES = set(STATUS) | EXECUTED_STATUSES


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def package_fingerprint() -> str:
    digest = hashlib.sha256()
    paths = [ROOT / "SKILL.md", ROOT / "README.md", ROOT / "composition-contract.json"]
    paths.extend((ROOT / name).rglob("*") for name in ("references", "scripts", "tests"))
    flattened: list[Path] = []
    for group in paths:
        if isinstance(group, Path):
            flattened.append(group)
        else:
            flattened.extend(group)
    for path in sorted(
        path
        for path in flattened
        if path.is_file() and ".pyc" not in path.name and "__pycache__" not in path.parts
    ):
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

# Gold fields and evaluator artifacts are forbidden in model output. This is
# intentionally stricter than the scorer, which is a private consumer.
GOLD_OUTPUT_FIELDS = frozenset(
    {
        *GOLD_SCENARIO_FIELDS,
        "gold",
        "answer_key",
        "rubric",
        "rubric_answer",
        "expected",
        "oracle",
        "mutation",
        "mutation_diagnostic",
        "diagnostic",
        "score",
        "score_percent",
        "average_0_4",
        "dimensions",
        "hard_failures",
        "hard_fail_tags_checked",
        "control_score",
        "treatment_score",
        "control_treatment_delta",
    }
)
ALLOWED_RECORD_FIELDS = frozenset(
    {
        "scenario_id",
        "lane",
        "status",
        "text",
        "response",  # historical adapter alias; canonicalized to text
        "scoring_context",
        "captured_at",
        "model",
        "decision",  # model-emitted observation for generalization
        "response_id",
        "variant",
        "comparison_group",
    }
)
PLACEHOLDER_IDENTITIES = {"", "unknown", "unavailable", "fixture", "test", "mock", "fake", "none", "n/a"}


class AdapterValidationError(ValueError):
    """A fail-closed adapter/capture contract error."""

    def __init__(self, errors: list[str] | str):
        self.errors = [errors] if isinstance(errors, str) else list(errors)
        super().__init__("; ".join(self.errors))


def _non_empty_text(value: Any, label: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")
        return None
    normalized = value.strip()
    if normalized.casefold() in PLACEHOLDER_IDENTITIES:
        errors.append(f"{label} must identify an executed consumer, not a placeholder")
        return None
    return normalized


def _parse_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdapterValidationError(f"adapter output is not valid JSON: {exc.msg}") from exc


def _fingerprints() -> dict[str, str]:
    return {
        "corpus_sha256": sha256(SCENARIOS) if SCENARIOS.is_file() else "",
        "package_sha256": package_fingerprint(),
    }


def _metadata_fingerprints(metadata: dict[str, Any]) -> dict[str, Any]:
    nested = metadata.get("fingerprints")
    nested = nested if isinstance(nested, dict) else {}
    return {
        "corpus_sha256": metadata.get("corpus_fingerprint", nested.get("corpus_sha256")),
        "package_sha256": metadata.get("package_fingerprint", nested.get("package_sha256")),
    }


def _validate_metadata(
    metadata: Any,
    expected_fingerprints: dict[str, str] | None = None,
    require_holdout_first_result: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(metadata, dict):
        raise AdapterValidationError("capture metadata must be an object")

    status = str(metadata.get("capture_status", metadata.get("status", ""))).upper().replace("-", "_")
    if status not in EXECUTED_STATUSES:
        errors.append("capture metadata status must be EXECUTED/COMPLETED/DONE/SUCCESS")

    canonical: dict[str, Any] = {"capture_status": status}
    for field in (
        "consumer_identity",
        "consumer_version",
        "adapter_identity",
        "adapter_version",
        "model_identity",
        "model_version",
    ):
        value = _non_empty_text(metadata.get(field), f"metadata.{field}", errors)
        if value is not None:
            canonical[field] = value

    captured_at = metadata.get("captured_at")
    if not isinstance(captured_at, str) or not captured_at.strip():
        errors.append("metadata.captured_at must be a non-empty ISO timestamp")
    else:
        try:
            datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append("metadata.captured_at must be an ISO timestamp")
        canonical["captured_at"] = captured_at

    actual_fingerprints = _metadata_fingerprints(metadata)
    canonical["fingerprints"] = actual_fingerprints
    for field in ("corpus_sha256", "package_sha256"):
        if not isinstance(actual_fingerprints[field], str) or not actual_fingerprints[field].strip():
            errors.append(f"metadata.{field} is required")
        elif expected_fingerprints and actual_fingerprints[field] != expected_fingerprints.get(field):
            errors.append(f"metadata.{field} does not match the current evaluator input")

    if "evidence_kind" in metadata:
        evidence_kind = metadata.get("evidence_kind")
        if not isinstance(evidence_kind, str) or evidence_kind.strip().casefold() in {"fixture", "synthetic", "oracle"}:
            errors.append("metadata.evidence_kind cannot identify a fixture/oracle capture")
        else:
            canonical["evidence_kind"] = evidence_kind.strip()

    if "holdout_first_result_only" in metadata:
        if metadata.get("holdout_first_result_only") is not True:
            errors.append("metadata.holdout_first_result_only must be true")
        canonical["holdout_first_result_only"] = metadata.get("holdout_first_result_only")
    elif require_holdout_first_result:
        errors.append("metadata.holdout_first_result_only is required for generalization capture")

    if "requested_split" in metadata:
        if metadata.get("requested_split") is not None and not isinstance(metadata.get("requested_split"), str):
            errors.append("metadata.requested_split must be text or null")
        else:
            canonical["requested_split"] = metadata.get("requested_split")
    if "requested_limit" in metadata:
        requested_limit = metadata.get("requested_limit")
        if requested_limit is not None and (isinstance(requested_limit, bool) or not isinstance(requested_limit, int) or requested_limit < 1):
            errors.append("metadata.requested_limit must be a positive integer or null")
        else:
            canonical["requested_limit"] = requested_limit
    if "execution_id" in metadata:
        execution_id = _non_empty_text(metadata.get("execution_id"), "metadata.execution_id", errors)
        if execution_id is not None:
            canonical["execution_id"] = execution_id

    if "judge" in metadata:
        judge = metadata.get("judge")
        if not isinstance(judge, dict):
            errors.append("metadata.judge must be an object when supplied")
        else:
            judge_status = str(judge.get("status", "NOT_RUN")).upper().replace("-", "_")
            if judge_status not in EXECUTED_STATUSES | {"NOT_RUN", "BLOCKED"}:
                errors.append("metadata.judge.status is unsupported")
            judge_identity = _non_empty_text(judge.get("identity"), "judge.identity", errors)
            judge_version = _non_empty_text(judge.get("version"), "judge.version", errors)
            judge_metadata: dict[str, Any] = {"status": judge_status}
            if judge_identity is not None:
                judge_metadata["identity"] = judge_identity
            if judge_version is not None:
                judge_metadata["version"] = judge_version
            if "command" in judge:
                if not isinstance(judge.get("command"), str) or not judge["command"].strip():
                    errors.append("metadata.judge.command must be non-empty text when supplied")
                else:
                    # The command is never executed or emitted; its digest is
                    # useful for identity without leaking arguments/secrets.
                    judge_metadata["command_sha256"] = sha256_bytes(judge["command"].encode("utf-8"))
            canonical["judge"] = judge_metadata

    if errors:
        raise AdapterValidationError(errors)
    return canonical


def _access_value(value: Any, label: str, errors: list[str]) -> str | None:
    if isinstance(value, bool):
        return "supplied" if value else "withheld"
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} package access is required")
        return None
    normalized = value.strip().casefold()
    if normalized in {"none", "withheld", "not_supplied", "not-supplied", "absent"}:
        return "withheld"
    if normalized in {"supplied", "available", "allowed", "present"}:
        return "supplied"
    errors.append(f"{label} package access must be withheld or supplied")
    return None


def _validate_fairness(fairness: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(fairness, dict):
        raise AdapterValidationError("capture fairness metadata must be an object")

    canonical: dict[str, Any] = {}
    aliases = {
        "paired_scenarios": ("paired_scenarios", "paired_by_scenario"),
        "same_model": ("same_model",),
        "same_prompt": ("same_prompt", "same_public_prompt"),
        "same_generation_parameters": ("same_generation_parameters", "same_parameters"),
    }
    for field, candidates in aliases.items():
        value = next((fairness[candidate] for candidate in candidates if candidate in fairness), None)
        if value is not True:
            errors.append(f"fairness.{field} must be true")
        canonical[field] = value

    control = fairness.get("control") if isinstance(fairness.get("control"), dict) else {}
    treatment = fairness.get("treatment") if isinstance(fairness.get("treatment"), dict) else {}
    control_access = control.get("package_access", fairness.get("control_package_access"))
    treatment_access = treatment.get("package_access", fairness.get("treatment_package_access"))
    canonical["control"] = {"package_access": _access_value(control_access, "fairness.control", errors)}
    canonical["treatment"] = {"package_access": _access_value(treatment_access, "fairness.treatment", errors)}
    if canonical["control"]["package_access"] != "withheld":
        errors.append("fairness.control package access must be withheld")
    if canonical["treatment"]["package_access"] != "supplied":
        errors.append("fairness.treatment package access must be supplied")

    if errors:
        raise AdapterValidationError(errors)
    return canonical


def _extract_capture(raw: str, require_envelope: bool = True) -> tuple[dict[str, Any] | None, list[dict[str, Any]], dict[str, Any]]:
    parsed = _parse_json(raw)
    if isinstance(parsed, list):
        if require_envelope:
            raise AdapterValidationError(
                "adapter output must be a versioned capture object; an unwrapped response array is not execution evidence"
            )
        return None, parsed, {}
    if not isinstance(parsed, dict):
        raise AdapterValidationError("adapter output must be a capture object")

    errors: list[str] = []
    forbidden_envelope_fields = sorted(set(parsed) & GOLD_OUTPUT_FIELDS)
    if forbidden_envelope_fields:
        errors.append("capture contains gold/rubric fields: " + ", ".join(forbidden_envelope_fields))
    if parsed.get("protocol") != ADAPTER_PROTOCOL:
        errors.append(f"capture protocol must be {ADAPTER_PROTOCOL}")
    if "responses" not in parsed or not isinstance(parsed.get("responses"), list):
        errors.append("capture.responses must be an array of response records")
    if "metadata" not in parsed:
        errors.append("capture.metadata is required")
    if "fairness" not in parsed:
        errors.append("capture.fairness is required")
    if errors:
        raise AdapterValidationError(errors)
    return parsed, parsed["responses"], parsed


def _validate_records(
    records: Any,
    public_to_internal: dict[str, str],
    expected_public_ids: set[str] | None = None,
    require_complete: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    if not isinstance(records, list):
        raise AdapterValidationError("adapter responses must be an array")

    seen: set[tuple[str, str]] = set()
    normalized: list[dict[str, Any]] = []
    expected = expected_public_ids if expected_public_ids is not None else set(public_to_internal)
    for index, record in enumerate(records):
        prefix = f"response record {index}"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        forbidden = sorted(set(record) & GOLD_OUTPUT_FIELDS)
        if forbidden:
            errors.append(f"{prefix} contains gold/rubric fields: {', '.join(forbidden)}")
        unknown_fields = sorted(set(record) - ALLOWED_RECORD_FIELDS - GOLD_OUTPUT_FIELDS)
        if unknown_fields:
            errors.append(f"{prefix} contains unsupported fields: {', '.join(unknown_fields)}")

        supplied_id = record.get("scenario_id")
        if not isinstance(supplied_id, str) or not supplied_id.strip():
            errors.append(f"{prefix} is missing opaque scenario_id")
            supplied_id = ""
        supplied_id = str(supplied_id)
        if supplied_id not in public_to_internal:
            errors.append(f"{prefix} contains unknown or non-opaque scenario_id: {supplied_id}")
            internal_id = supplied_id
        else:
            internal_id = public_to_internal[supplied_id]

        lane = record.get("lane")
        if not isinstance(lane, str) or not lane.strip():
            errors.append(f"{prefix} is missing lane")
            lane = ""
        lane = str(lane)
        if lane not in LANES:
            errors.append(f"{prefix} has unsupported lane: {lane}")

        key = (supplied_id, lane)
        if key in seen:
            errors.append(f"{prefix} duplicates scenario/lane record: {supplied_id}/{lane}")
        seen.add(key)

        status = record.get("status", "EXECUTED")
        normalized_status = str(status).upper().replace("-", "_")
        if normalized_status not in RECORD_STATUSES:
            errors.append(f"{prefix} has unsupported status: {status}")

        has_text = "text" in record
        has_response = "response" in record
        if has_text and has_response:
            errors.append(f"{prefix} must provide only one of text or response")
        response_text = record.get("text", record.get("response"))
        if normalized_status in EXECUTED_STATUSES and (not isinstance(response_text, str) or not response_text.strip()):
            errors.append(f"{prefix} executed response has no non-empty text/response")
        elif response_text is not None and not isinstance(response_text, str):
            errors.append(f"{prefix} text/response must be text")
        if "scoring_context" in record and not isinstance(record.get("scoring_context"), str):
            errors.append(f"{prefix} scoring_context must be text")
        if "decision" in record and (not isinstance(record.get("decision"), str) or not record["decision"].strip()):
            errors.append(f"{prefix} decision must be non-empty text when supplied")
        if "captured_at" in record and not isinstance(record.get("captured_at"), str):
            errors.append(f"{prefix} captured_at must be text when supplied")
        if "model" in record and not isinstance(record.get("model"), str):
            errors.append(f"{prefix} model must be text when supplied")

        item = dict(record)
        item["scenario_id"] = internal_id
        item["lane"] = lane
        item["status"] = normalized_status
        if has_response and not has_text:
            item["text"] = item.pop("response")
        elif has_response:
            item.pop("response", None)
        normalized.append(item)

    supplied_ids = {key[0] for key in seen}
    if require_complete or expected_public_ids is not None:
        expected_keys = {(identifier, lane) for identifier in expected for lane in LANES}
        missing = sorted(expected_keys - seen)
        extra = sorted(seen - expected_keys)
        if missing:
            errors.append(
                "missing scenario/lane records: " + ", ".join(f"{identifier}/{lane}" for identifier, lane in missing)
            )
        if extra:
            errors.append(
                "unexpected scenario/lane records: " + ", ".join(f"{identifier}/{lane}" for identifier, lane in extra)
            )
    if expected_public_ids is not None:
        missing_ids = sorted(expected_public_ids - supplied_ids)
        if missing_ids:
            errors.append("missing scenario IDs: " + ", ".join(missing_ids))

    return normalized, errors


def _validate_comparison_records(comparisons: Any, public_to_internal: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    """Validate optional non-scoring generalization comparison captures."""
    if comparisons is None:
        return {}
    if not isinstance(comparisons, dict):
        raise AdapterValidationError("capture.comparisons must be an object when supplied")
    output: dict[str, list[dict[str, Any]]] = {}
    allowed = {"comparison_id", "scenario_id", "lane", "variant", "status", "text", "response", "decision"}
    for label, values in comparisons.items():
        if not isinstance(values, list):
            raise AdapterValidationError(f"capture.comparisons.{label} must be an array")
        seen: set[tuple[str, str]] = set()
        checked: list[dict[str, Any]] = []
        for index, item in enumerate(values):
            if not isinstance(item, dict):
                raise AdapterValidationError(f"comparison {label}[{index}] must be an object")
            forbidden = sorted(set(item) & GOLD_OUTPUT_FIELDS)
            if forbidden:
                raise AdapterValidationError(f"comparison {label}[{index}] contains gold/rubric fields: {', '.join(forbidden)}")
            unsupported = sorted(set(item) - allowed)
            if unsupported:
                raise AdapterValidationError(f"comparison {label}[{index}] contains unsupported fields: {', '.join(unsupported)}")
            comparison_id = item.get("comparison_id")
            variant = item.get("variant")
            if not isinstance(comparison_id, str) or not comparison_id.strip():
                raise AdapterValidationError(f"comparison {label}[{index}] is missing comparison_id")
            if not isinstance(variant, str) or not variant.strip():
                raise AdapterValidationError(f"comparison {label}[{index}] is missing variant")
            key = (comparison_id, variant)
            if key in seen:
                raise AdapterValidationError(f"comparison {label} duplicates comparison_id/variant: {comparison_id}/{variant}")
            seen.add(key)
            scenario_id = item.get("scenario_id")
            if scenario_id is not None and scenario_id not in public_to_internal:
                raise AdapterValidationError(f"comparison {label}[{index}] contains unknown or non-opaque scenario_id: {scenario_id}")
            text_value = item.get("text", item.get("response"))
            if not isinstance(text_value, str) or not text_value.strip():
                raise AdapterValidationError(f"comparison {label}[{index}] requires non-empty text/response")
            if "decision" in item and (not isinstance(item["decision"], str) or not item["decision"].strip()):
                raise AdapterValidationError(f"comparison {label}[{index}] decision must be non-empty text")
            checked_item = dict(item)
            if "response" in checked_item and "text" not in checked_item:
                checked_item["text"] = checked_item.pop("response")
            if scenario_id is not None:
                checked_item["scenario_id"] = public_to_internal[scenario_id]
            checked.append(checked_item)
        output[str(label)] = checked
    return output


def validate_adapter_capture(
    raw: str,
    public_to_internal: dict[str, str],
    expected_public_ids: set[str] | None = None,
    expected_fingerprints: dict[str, str] | None = None,
    require_complete: bool = False,
    require_holdout_first_result: bool = False,
) -> dict[str, Any]:
    """Validate and privately normalize a v2 adapter capture.

    No scenario corpus values are joined into the adapter output. The caller
    must persist ``raw`` before calling this function.
    """
    envelope, records, parsed = _extract_capture(raw, require_envelope=True)
    assert envelope is not None
    metadata_input = dict(envelope.get("metadata", {}))
    if "judge" in envelope:
        if "judge" in metadata_input:
            raise AdapterValidationError("judge metadata must appear in one location only")
        metadata_input["judge"] = envelope["judge"]
    metadata = _validate_metadata(
        metadata_input,
        expected_fingerprints=expected_fingerprints,
        require_holdout_first_result=require_holdout_first_result,
    )
    fairness = _validate_fairness(envelope.get("fairness"))
    normalized, record_errors = _validate_records(
        records,
        public_to_internal,
        expected_public_ids=expected_public_ids,
        require_complete=require_complete,
    )
    comparison_records = _validate_comparison_records(envelope.get("comparisons"), public_to_internal)
    if record_errors:
        raise AdapterValidationError(record_errors)

    model_identity = metadata.get("model_identity")
    model_mismatches = [
        str(index)
        for index, record in enumerate(records)
        if isinstance(record, dict) and record.get("model") not in (None, model_identity)
    ]
    if model_mismatches:
        raise AdapterValidationError("response model identity differs from capture metadata at records: " + ", ".join(model_mismatches))

    return {
        "protocol": envelope.get("protocol"),
        "metadata": metadata,
        "fairness": fairness,
        "records": normalized,
        "raw_records": records,
        "comparisons": comparison_records,
        "record_order": [
            {"scenario_id": record.get("scenario_id"), "lane": record.get("lane")}
            for record in records
            if isinstance(record, dict)
        ],
        # Preserve only the non-sensitive capture shape, not arbitrary unknown
        # envelope fields or raw response text.
        "has_comparisons": bool(comparison_records),
        "top_level_keys": sorted(key for key in parsed if key not in {"responses", "comparisons"}),
    }


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
    current_fingerprints = _fingerprints()
    fairness = {
        "paired_scenarios": True,
        "same_model": True,
        "same_prompt": True,
        "same_generation_parameters": True,
        "control": {"package_access": "withheld"},
        "treatment": {"package_access": "supplied"},
    }
    return {
        "protocol": ADAPTER_PROTOCOL,
        "instruction": "Return one JSON response record for each opaque scenario_id in both control and treatment lanes. Control must not read backend-patterns; treatment may read the supplied package. Do not edit files. The supplied task projection intentionally excludes the answer key and benchmark metadata.",
        "package_root": str(ROOT),
        "scenarios": public_scenarios,
        "public_fields": list(PUBLIC_SCENARIO_FIELDS),
        "redacted_gold_fields": list(GOLD_SCENARIO_FIELDS),
        "lanes": list(LANES),
        "same_model_required": True,
        "request_selection": {"split": split, "limit": limit, "opaque_ids_are_request_local": True},
        "fairness": fairness,
        "fingerprints": current_fingerprints,
        "response_schema": {
            "metadata_required": [
                "capture_status",
                "consumer_identity",
                "consumer_version",
                "adapter_identity",
                "adapter_version",
                "model_identity",
                "model_version",
                "captured_at",
                "corpus_sha256",
                "package_sha256",
            ],
            "record_fields": sorted(ALLOWED_RECORD_FIELDS),
            "gold_fields_rejected": sorted(GOLD_OUTPUT_FIELDS),
        },
        "generalization_policy": {"holdout_first_result_only": True, "scores_not_inferred": True},
    }, public_to_internal


def normalize_adapter_response(raw: str, public_to_internal: dict[str, str]) -> str:
    """Translate opaque adapter IDs back to private scoring corpus IDs.

    This compatibility helper validates record shape, lanes, duplicates, and
    gold leakage. The executable runner additionally requires the v2 envelope
    and execution metadata through ``validate_adapter_capture``.
    """
    envelope, records, _ = _extract_capture(raw, require_envelope=False)
    if envelope is not None:
        normalized = validate_adapter_capture(raw, public_to_internal)["records"]
    else:
        normalized, errors = _validate_records(records, public_to_internal)
        if errors:
            raise AdapterValidationError(errors)
    return json.dumps(normalized, ensure_ascii=False)


def _raw_capture_path(output: str | None, requested: str | None, prefix: str) -> Path:
    if requested:
        return Path(requested).resolve()
    if output:
        output_path = Path(output).resolve()
        return output_path.with_name(output_path.name + ".raw.json")
    handle, name = tempfile.mkstemp(prefix=prefix, suffix=".raw.json")
    os.close(handle)
    return Path(name).resolve()


def persist_raw_capture(raw: str, path: Path, source: str) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = raw.encode("utf-8")
    path.write_bytes(data)
    return {
        "path": str(path.resolve()),
        "sha256": sha256_bytes(data),
        "bytes": len(data),
        "source": source,
    }


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
        # Do not echo adapter stderr: it can contain credentials, prompts, or
        # provider response content. The exit status is sufficient evidence.
        return "FAIL", f"adapter exited {completed.returncode}; adapter stderr was not captured into evidence"
    return "EXECUTED", completed.stdout


def score(response_file: Path) -> dict:
    if not SCORE.is_file():
        return {"status": "FAIL", "errors": [f"missing scorer: {SCORE.relative_to(ROOT)}"]}
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(SCORE),
            "--response-file",
            str(response_file),
            "--scenario-file",
            str(SCENARIOS),
            "--rubric-file",
            str(RUBRIC),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "FAIL", "errors": ["scorer returned non-JSON; scorer stdout/stderr omitted from evidence"]}
    parsed["scorer_exit_status"] = result.returncode
    return parsed


def _base_blocked(reason: str, payload: dict, fingerprints: dict[str, str]) -> dict[str, Any]:
    return {
        "scope": "BEHAVIORAL_MODEL_EVAL",
        "status": "BLOCKED",
        "model_execution": "BLOCKED",
        "reason": reason,
        "required_host_capability": "An adapter that invokes the same consumer model in control and treatment lanes and returns a versioned JSON capture with executed consumer identity, fairness metadata, and current corpus/package fingerprints.",
        "evidence_unavailable": "control/treatment responses, scores, pairwise judgments and causal delta",
        "impact_on_verdict": "TRIPLE_A_PROVEN is ineligible; use TRIPLE_A_CONDITIONAL at most.",
        "scenario_count": len(payload.get("scenarios", [])),
        "split": None,
        "package_fingerprint": fingerprints.get("package_sha256"),
        "benchmark_fingerprint": fingerprints.get("corpus_sha256"),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "raw_capture": None,
        "errors": [],
    }


def _invalid(reason: str, payload: dict, fingerprints: dict[str, str], raw_capture: dict[str, Any] | None = None) -> dict[str, Any]:
    result = _base_blocked(reason, payload, fingerprints)
    result.update({"status": "INVALID", "model_execution": "INVALID", "raw_capture": raw_capture, "errors": [reason]})
    return result


def run(args: argparse.Namespace) -> dict:
    payload, public_to_internal = request_payload(args.split, args.limit)
    expected_public_ids = set(public_to_internal)
    fingerprints = _fingerprints()
    response_file = Path(args.response_file).resolve() if args.response_file else None
    capture_info: dict[str, Any] | None = None
    raw: str
    source: str

    if response_file is None:
        command = args.adapter_command or os.environ.get("BACKEND_PATTERNS_MODEL_ADAPTER")
        if not command:
            result = _base_blocked("No consumer-model adapter was supplied.", payload, fingerprints)
            result["split"] = args.split
            return result
        adapter_status, adapter_output = run_adapter(command, payload)
        if adapter_status == "BLOCKED":
            result = _base_blocked(adapter_output, payload, fingerprints)
            result["split"] = args.split
            return result
        if adapter_status != "EXECUTED":
            return {
                "scope": "BEHAVIORAL_MODEL_EVAL",
                "status": "FAIL",
                "model_execution": "FAIL",
                "reason": adapter_output,
                "required_host_capability": "working consumer-model adapter",
                "scenario_count": len(payload["scenarios"]),
                "split": args.split,
                "package_fingerprint": fingerprints["package_sha256"],
                "benchmark_fingerprint": fingerprints["corpus_sha256"],
                "raw_capture": None,
                "errors": [adapter_output],
            }
        raw = adapter_output
        source = "adapter_stdout"
    else:
        if not response_file.is_file():
            return _invalid(f"supplied response file does not exist: {response_file}", payload, fingerprints)
        try:
            raw = response_file.read_text(encoding="utf-8")
        except OSError as exc:
            return _invalid(f"supplied response file could not be read: {exc}", payload, fingerprints)
        source = "supplied_response_file"

    if response_file is not None:
        capture_info = {
            "path": str(response_file),
            "sha256": sha256(response_file),
            "bytes": response_file.stat().st_size,
            "source": source,
        }
    else:
        capture_path = _raw_capture_path(args.output, args.raw_capture, "backend-patterns-behavioral-")
        try:
            # This write intentionally precedes JSON parsing, private ID joins,
            # normalization, and scoring.
            capture_info = persist_raw_capture(raw, capture_path, source)
        except OSError as exc:
            return _invalid(f"raw adapter capture could not be persisted: {exc}", payload, fingerprints)

    try:
        capture = validate_adapter_capture(
            raw,
            public_to_internal,
            expected_public_ids=expected_public_ids,
            expected_fingerprints=fingerprints,
            require_complete=True,
        )
    except AdapterValidationError as exc:
        return _invalid("invalid adapter capture: " + "; ".join(exc.errors), payload, fingerprints, capture_info)

    # A supplied response file is not evidence merely because it parses. The
    # strict envelope requires actual execution status and consumer/model
    # identity; fixtures and bare scorer arrays fail before this private join.
    normalized_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as normalized_file:
            normalized_file.write(json.dumps(capture["records"], ensure_ascii=False))
            normalized_path = Path(normalized_file.name)
        scored = score(normalized_path)
    finally:
        if normalized_path is not None:
            try:
                normalized_path.unlink()
            except OSError:
                pass

    score_status = scored.get("status")
    result_status = score_status if score_status in set(STATUS) else "FAIL"
    metadata = capture["metadata"]
    return {
        "scope": "BEHAVIORAL_MODEL_EVAL",
        "status": result_status,
        "model_execution": "EXECUTED",
        "scenario_count": len(payload["scenarios"]),
        "split": args.split,
        "package_fingerprint": fingerprints["package_sha256"],
        "benchmark_fingerprint": fingerprints["corpus_sha256"],
        "rubric_fingerprint": sha256(RUBRIC),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "capture_identity": {
            "consumer_identity": metadata["consumer_identity"],
            "consumer_version": metadata["consumer_version"],
            "adapter_identity": metadata["adapter_identity"],
            "adapter_version": metadata["adapter_version"],
            "model_identity": metadata["model_identity"],
            "model_version": metadata["model_version"],
            "capture_status": metadata["capture_status"],
            "captured_at": metadata["captured_at"],
            **({"judge": metadata["judge"]} if "judge" in metadata else {}),
        },
        "fairness": capture["fairness"],
        "raw_capture": capture_info,
        "scoring": scored,
        "errors": scored.get("errors", []),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter-command")
    parser.add_argument("--response-file")
    parser.add_argument("--split", choices=["development", "adversarial", "holdout"])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--raw-capture", help="persist raw adapter stdout to this path before validation/scoring")
    parser.add_argument("--output", help="write the JSON evidence artifact to this path")
    args = parser.parse_args()
    try:
        result = run(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"scope": "BEHAVIORAL_MODEL_EVAL", "status": "INVALID", "model_execution": "INVALID", "errors": [str(exc)]}
    encoded = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    raise SystemExit(0 if result.get("status") in {"PASS", "BLOCKED", "NOT_RUN"} else 1)
