#!/usr/bin/env python3
"""Evaluate observed cross-skill composition traces without conflating schemas with execution."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "composition-contract.json"
BEHAVIORAL = ROOT / "scripts" / "run-behavioral-eval.py"
COMPOSITION_PROTOCOL = "backend-patterns-composition-eval-v2"
REQUIRED_STAGES = (
    "backend-engineering-vNext",
    "backend-patterns",
    "security-engineering-vNext",
    "verification-loop-vNext",
)
EXECUTED_STATUSES = {"PASS", "FAIL", "EXECUTED", "COMPLETED", "DONE", "SUCCESS"}


def fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_fingerprint() -> str:
    spec = importlib.util.spec_from_file_location("backend_patterns_behavioral_for_composition", BEHAVIORAL)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load package fingerprint implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.package_fingerprint()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def blocked(reason: str, scenario_count: int = 0) -> dict:
    return {
        "scope": "REAL_COMPOSITION",
        "status": "BLOCKED",
        "composition": "BLOCKED",
        "execution_status": "BLOCKED",
        "reason": reason,
        "required_host_capability": "An executable composition adapter or observed trace from the neighboring skills, with executed consumer identity, adapter version, and current package/contract fingerprints.",
        "evidence_unavailable": "actual backend → patterns → security → verification handoffs and repair-loop observations",
        "impact_on_verdict": "Composition proof is unavailable; Triple-A proven is ineligible.",
        "scenario_count": scenario_count,
        "contract_fingerprint": fingerprint(CONTRACT) if CONTRACT.is_file() else None,
        "package_fingerprint": package_fingerprint(),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "raw_capture": None,
        "errors": [],
    }


def validate_trace(trace: object) -> dict:
    """Validate the observable trace shape; metadata is checked by the strict envelope validator."""
    if not isinstance(trace, dict):
        return {"status": "FAIL", "errors": ["trace must be an object"]}
    events = trace.get("events")
    if not isinstance(events, list) or not events:
        return {"status": "FAIL", "errors": ["trace.events must be a non-empty array"]}
    names = [event.get("stage") for event in events if isinstance(event, dict)]
    missing = [stage for stage in REQUIRED_STAGES if stage not in names]
    repair = any(event.get("stage") == "repair" for event in events if isinstance(event, dict))
    reverification = any(event.get("stage") in {"re-verification", "verification-rerun"} for event in events if isinstance(event, dict))
    errors = []
    if missing:
        errors.append("missing observed stages: " + ", ".join(missing))
    if not repair:
        errors.append("missing observed repair stage")
    if not reverification:
        errors.append("missing observed re-verification stage")
    for index, event in enumerate(events):
        if not isinstance(event, dict) or not event.get("observed"):
            errors.append(f"event {index} is not marked observed")
        if isinstance(event, dict) and not event.get("output"):
            errors.append(f"event {index} has no output/evidence payload")
    return {
        "status": "PASS" if not errors else "FAIL",
        "events": len(events),
        "stages": names,
        "repair_loop_observed": repair and reverification,
        "errors": errors,
    }


def _metadata_fingerprints(metadata: dict[str, Any]) -> dict[str, Any]:
    nested = metadata.get("fingerprints")
    nested = nested if isinstance(nested, dict) else {}
    return {
        "package_sha256": metadata.get("package_fingerprint", nested.get("package_sha256")),
        "contract_sha256": metadata.get("contract_fingerprint", nested.get("contract_sha256")),
    }


def _non_empty(value: Any, label: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip() or value.strip().casefold() in {"unknown", "fixture", "mock", "test", "fake"}:
        errors.append(f"metadata.{label} must identify executed evidence")
        return None
    return value.strip()


def validate_composition_capture(raw: str) -> dict[str, Any]:
    """Validate a v2 composition capture and return only safe evidence metadata."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"composition adapter output is not valid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("composition adapter output must be a versioned capture object")
    errors: list[str] = []
    if parsed.get("protocol") != COMPOSITION_PROTOCOL:
        errors.append(f"capture protocol must be {COMPOSITION_PROTOCOL}")
    metadata = parsed.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("capture.metadata is required")
        metadata = {}
    trace = parsed.get("trace")
    if not isinstance(trace, dict):
        errors.append("capture.trace is required")
        trace = {}
    status = str(metadata.get("capture_status", metadata.get("status", ""))).upper().replace("-", "_")
    if status not in EXECUTED_STATUSES:
        errors.append("metadata status must be EXECUTED/COMPLETED/DONE/SUCCESS")
    identity: dict[str, str] = {"capture_status": status}
    for field in ("consumer_identity", "consumer_version", "adapter_identity", "adapter_version"):
        value = _non_empty(metadata.get(field), field, errors)
        if value is not None:
            identity[field] = value
    captured_at = metadata.get("captured_at")
    if not isinstance(captured_at, str) or not captured_at.strip():
        errors.append("metadata.captured_at is required")
    else:
        try:
            datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append("metadata.captured_at must be an ISO timestamp")
        identity["captured_at"] = captured_at

    actual = _metadata_fingerprints(metadata)
    expected = {"package_sha256": package_fingerprint(), "contract_sha256": fingerprint(CONTRACT)}
    for field in ("package_sha256", "contract_sha256"):
        if not isinstance(actual[field], str) or not actual[field].strip():
            errors.append(f"metadata.{field} is required")
        elif actual[field] != expected[field]:
            errors.append(f"metadata.{field} does not match current composition input")

    trace_report = validate_trace(trace)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "protocol": parsed["protocol"],
        "metadata": identity,
        "fingerprints": actual,
        "trace": trace,
        "trace_report": trace_report,
    }


def _raw_capture_path(output: str | None, requested: str | None) -> Path:
    if requested:
        return Path(requested).resolve()
    if output:
        output_path = Path(output).resolve()
        return output_path.with_name(output_path.name + ".raw.json")
    handle = tempfile.NamedTemporaryFile(prefix="backend-patterns-composition-", suffix=".raw.json", delete=False)
    path = Path(handle.name).resolve()
    handle.close()
    return path


def _persist_raw(raw: str, path: Path, source: str) -> dict[str, Any]:
    data = raw.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"path": str(path.resolve()), "sha256": _sha256_bytes(data), "bytes": len(data), "source": source}


def _invalid(reason: str, raw_capture: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "scope": "REAL_COMPOSITION",
        "status": "INVALID",
        "composition": "INVALID",
        "execution_status": "INVALID",
        "reason": reason,
        "required_host_capability": "A versioned observed composition capture with executed consumer identity and current package/contract fingerprints.",
        "contract_fingerprint": fingerprint(CONTRACT) if CONTRACT.is_file() else None,
        "package_fingerprint": package_fingerprint(),
        "raw_capture": raw_capture,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "errors": [reason],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-file")
    parser.add_argument("--adapter-command")
    parser.add_argument("--raw-capture", help="persist raw adapter stdout to this path before validation")
    parser.add_argument("--output", help="write the JSON evidence artifact to this path")
    args = parser.parse_args()
    trace_path = Path(args.trace_file).resolve() if args.trace_file else None
    raw_capture: dict[str, Any] | None = None
    source: str
    raw: str

    if trace_path is None and args.adapter_command:
        try:
            result = subprocess.run(shlex.split(args.adapter_command), cwd=ROOT, text=True, capture_output=True, check=False)
        except OSError as exc:
            report = blocked(f"composition adapter could not start: {exc}")
        else:
            if result.returncode != 0:
                report = {"scope": "REAL_COMPOSITION", "status": "FAIL", "composition": "FAIL", "execution_status": "FAIL", "errors": [f"adapter exited {result.returncode}; adapter stderr was not captured into evidence"]}
            else:
                raw = result.stdout
                path = _raw_capture_path(args.output, args.raw_capture)
                try:
                    # Persist before JSON parsing and trace validation.
                    raw_capture = _persist_raw(raw, path, "adapter_stdout")
                except OSError as exc:
                    report = _invalid(f"raw composition capture could not be persisted: {exc}")
                else:
                    try:
                        capture = validate_composition_capture(raw)
                    except (OSError, ValueError) as exc:
                        report = _invalid(str(exc), raw_capture)
                    else:
                        trace_report = capture["trace_report"]
                        report = {
                            "scope": "REAL_COMPOSITION",
                            "status": trace_report["status"],
                            "composition": trace_report["status"],
                            "execution_status": "EXECUTED",
                            "events": trace_report.get("events"),
                            "stages": trace_report.get("stages"),
                            "repair_loop_observed": trace_report.get("repair_loop_observed"),
                            "comparison": {"status": "OBSERVED", "handoff_trace_is_not_contract_only": True},
                            "contract_fingerprint": capture["fingerprints"]["contract_sha256"],
                            "package_fingerprint": capture["fingerprints"]["package_sha256"],
                            "capture_identity": capture["metadata"],
                            "raw_capture": raw_capture,
                            "captured_at": datetime.now(timezone.utc).isoformat(),
                            "errors": trace_report.get("errors", []),
                        }
    elif trace_path is not None:
        if not trace_path.is_file():
            report = _invalid(f"supplied trace file does not exist: {trace_path}")
        else:
            try:
                raw = trace_path.read_text(encoding="utf-8")
                raw_capture = {"path": str(trace_path), "sha256": fingerprint(trace_path), "bytes": trace_path.stat().st_size, "source": "supplied_trace_file"}
                capture = validate_composition_capture(raw)
            except (OSError, ValueError) as exc:
                report = _invalid(str(exc), raw_capture)
            else:
                trace_report = capture["trace_report"]
                report = {
                    "scope": "REAL_COMPOSITION",
                    "status": trace_report["status"],
                    "composition": trace_report["status"],
                    "execution_status": "EXECUTED",
                    "events": trace_report.get("events"),
                    "stages": trace_report.get("stages"),
                    "repair_loop_observed": trace_report.get("repair_loop_observed"),
                    "comparison": {"status": "OBSERVED", "handoff_trace_is_not_contract_only": True},
                    "contract_fingerprint": capture["fingerprints"]["contract_sha256"],
                    "package_fingerprint": capture["fingerprints"]["package_sha256"],
                    "capture_identity": capture["metadata"],
                    "raw_capture": raw_capture,
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "errors": trace_report.get("errors", []),
                }
    else:
        report = blocked("No composition adapter or observed trace was supplied.")

    report.setdefault("scope", "REAL_COMPOSITION")
    report.setdefault("captured_at", datetime.now(timezone.utc).isoformat())
    encoded = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report.get("status") in {"PASS", "BLOCKED", "NOT_RUN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
