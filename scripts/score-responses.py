#!/usr/bin/env python3
"""Score captured backend-architecture responses deterministically.

This evaluator intentionally contains no model invocation.  It scores supplied
response records against a scenario corpus and a machine-readable rubric.  The
signal checks are conservative lexical checks with explicit scenario evidence;
they are useful as a hard-rule and regression oracle, not as a substitute for
an independent architectural judge.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import unicodedata
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent.parent

STATUSES = {
    "PASS",
    "FAIL",
    "NOT_RUN",
    "BLOCKED",
    "STALE",
    "NOT_APPLICABLE",
}
EXECUTED_STATUSES = {"PASS", "FAIL", "EXECUTED", "COMPLETED", "DONE", "SUCCESS"}


# These are the frozen rubric dimension names from master-prompt sections 11
# and 44.  A benchmark rubric may add prose, anchors, or signal metadata, but
# the deterministic checks below remain stable across corpus revisions.
DIMENSION_DEFINITIONS: dict[str, dict[str, Any]] = {
    "D1": {"name": "Trigger correctness", "sources": ["prompt", "expected_decision"]},
    "D2": {"name": "Problem classification", "sources": ["family", "domains", "prompt"]},
    "D3": {"name": "Current facts identified", "sources": ["current_facts"]},
    "D4": {"name": "Unknowns preserved", "sources": ["unknowns"]},
    "D5": {"name": "Invariants identified", "sources": ["invariants"]},
    "D6": {"name": "Forces identified", "sources": ["forces"]},
    "D7": {"name": "Simpler baseline included", "sources": ["simpler_baseline"]},
    "D8": {"name": "Candidate quality", "sources": ["required_signals", "expected_decision"]},
    "D9": {"name": "Pattern rejection quality", "sources": ["simpler_baseline", "required_signals"]},
    "D10": {"name": "Selected design proportionality", "sources": ["expected_decision", "simpler_baseline"]},
    "D11": {"name": "Failure semantics", "sources": ["forces", "unknowns", "required_signals"]},
    "D12": {"name": "Transaction semantics", "sources": ["current_facts", "invariants", "required_signals"]},
    "D13": {"name": "Concurrency semantics", "sources": ["current_facts", "forces", "required_signals"]},
    "D14": {"name": "Consistency semantics", "sources": ["invariants", "forces", "required_signals"]},
    "D15": {"name": "Security constraints", "sources": ["current_facts", "forces", "required_signals", "domains"]},
    "D16": {"name": "Operability", "sources": ["forces", "required_signals"]},
    "D17": {"name": "Observability", "sources": ["forces", "required_signals"]},
    "D18": {"name": "Migration/compatibility", "sources": ["unknowns", "forces", "required_signals"]},
    "D19": {"name": "Verification requirements", "sources": ["required_signals", "invariants"]},
    "D20": {"name": "Residual risk", "sources": ["unknowns", "forces", "required_signals"]},
    "D21": {"name": "No cargo-cult reasoning", "sources": ["simpler_baseline", "forces", "required_signals"]},
    "D22": {"name": "No invented requirements", "sources": ["unknowns", "current_facts"]},
    "D23": {"name": "Context efficiency", "sources": ["required_signals", "simpler_baseline"]},
}


DIMENSION_MARKERS: dict[str, list[str]] = {
    "D1": ["decision", "trigger", "because", "therefore", "scope"],
    "D2": ["classify", "problem", "boundary", "domain", "failure boundary"],
    "D3": ["current", "fact", "observed", "existing", "today"],
    "D4": ["unknown", "unclear", "not known", "assumption", "confirm", "open question"],
    "D5": ["invariant", "guarantee", "must not", "at most", "never", "constraint"],
    "D6": ["force", "trade-off", "tradeoff", "latency", "availability", "ownership", "complexity"],
    "D7": ["simpler", "baseline", "minimum", "modular monolith", "local alternative"],
    "D8": ["candidate", "option", "alternative", "select", "design", "mechanism"],
    "D9": ["reject", "avoid", "not use", "without a driver", "unnecessary", "when not"],
    "D10": ["proportional", "minimum sufficient", "smallest", "right-sized", "selected"],
    "D11": ["failure", "crash", "timeout", "partial", "recovery", "repair", "outage"],
    "D12": ["transaction", "atomic", "commit", "rollback", "after commit", "outbox"],
    "D13": ["concurrent", "concurrency", "race", "compare-and-swap", "cas", "lock", "version", "conflict"],
    "D14": ["consistency", "eventual", "stale", "ordering", "duplicate", "idempotent", "source of truth"],
    "D15": ["authorization", "authz", "authentication", "tenant", "trust boundary", "default deny", "signature"],
    "D16": ["operate", "operability", "runbook", "operator", "dead letter", "replay", "alert", "ownership"],
    "D17": ["observability", "logs", "metrics", "traces", "telemetry", "correlation", "slo", "sli"],
    "D18": ["migration", "compatibility", "mixed version", "backward compatible", "rollout", "backfill", "rollback"],
    "D19": ["verify", "verification", "evidence", "test", "assert", "observe", "public boundary"],
    "D20": ["risk", "residual", "limitation", "revalidate", "unknown", "confidence"],
    "D21": ["evidence", "driver", "complexity", "cargo", "slogan", "only if", "not because"],
    "D22": ["unknown", "assumption", "do not invent", "not specified", "requirement", "confirm"],
    "D23": ["concise", "relevant", "scope", "minimum", "only what matters", "focused"],
}


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "for",
    "from",
    "has",
    "have",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "may",
    "must",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "their",
    "this",
    "to",
    "under",
    "use",
    "using",
    "we",
    "when",
    "with",
    "without",
}


ALIAS_GROUPS = [
    {"authorization", "authorize", "authorized", "authz", "permission", "access control"},
    {"authentication", "authenticate", "authenticated", "signature", "signed", "verify signature"},
    {"idempotency", "idempotent", "dedup", "dedupe", "deduplicate", "inbox", "replay safe", "request key"},
    {"duplicate", "duplicates", "duplication", "replay", "repeated", "at least once"},
    {"recovery", "recover", "reconcile", "reconciliation", "repair", "resume", "restart"},
    {"failure", "failures", "crash", "outage", "partial failure", "error"},
    {"transaction", "transactions", "atomic", "atomically", "commit", "committed", "rollback", "roll back"},
    {"concurrency", "concurrent", "race", "racing", "cas", "compare and swap", "lock", "locking", "version"},
    {"consistency", "consistent", "stale", "eventual", "ordering", "order", "source of truth"},
    {"migration", "migrate", "backfill", "schema change", "expand contract", "rollout"},
    {"compatibility", "compatible", "mixed version", "version skew", "tolerant reader", "backward compatible"},
    {"observability", "observable", "telemetry", "logs", "metrics", "traces", "correlation"},
    {"operability", "operate", "runbook", "operator", "dead letter", "dead-letter"},
    {"retry", "retries", "backoff", "jitter", "attempt budget", "retry budget"},
    {"cache", "caching", "cached", "invalidation", "stale reads", "stampede"},
    {"security", "secure", "trust", "tenant", "privilege", "default deny"},
]


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("_", " ").replace("-", " ")
    text = re.sub(r"[^a-z0-9.%]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokens(value: Any, *, meaningful: bool = False) -> list[str]:
    result = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", normalize_text(value))
    if meaningful:
        return [token for token in result if token not in STOPWORDS and len(token) > 1]
    return result


def canonical_tag(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("tag") or value.get("id") or value.get("name") or value.get("label") or ""
    normalized = normalize_text(value).replace(" ", "")
    if not normalized:
        return "unknown_tag"
    if "unknown" in normalized and "outcome" in normalized:
        return "unknown_outcome"
    if "unsafe" in normalized and "retry" in normalized or "retry" in normalized and "amplif" in normalized:
        return "unsafe_retry"
    if "exactly" in normalized and "once" in normalized:
        return "exactly_once"
    if "authz" in normalized or "authoriz" in normalized or "objectid" in normalized and "access" in normalized:
        return "missing_authz"
    if "dual" in normalized and "write" in normalized:
        return "direct_dual_write"
    if "invent" in normalized or "fabricat" in normalized or "unknownhid" in normalized:
        return "invented_requirement"
    if "unknown" in normalized and ("hide" in normalized or "fact" in normalized or "preserv" in normalized):
        return "unknown_hiding"
    if "invariant" in normalized:
        return "missing_invariant"
    if "recover" in normalized or "reconcil" in normalized or "repair" in normalized:
        return "missing_recovery"
    if "migration" in normalized or "compatib" in normalized or "versionskew" in normalized:
        return "removed_migration_compatibility"
    if "duplicate" in normalized or "idempot" in normalized or "replay" in normalized:
        return "missing_duplicate_safety"
    if "microservice" in normalized:
        return "cargo_cult_microservices"
    if "eventsourc" in normalized:
        return "cargo_cult_event_sourcing"
    if "runtime" in normalized or "unexecut" in normalized or "evidence" in normalized and "claim" in normalized:
        return "unexecuted_runtime_claim"
    if "readiness" in normalized or "production" in normalized or "certif" in normalized:
        return "unproven_readiness"
    if "cache" in normalized and ("invalid" in normalized or "stale" in normalized):
        return "missing_cache_invalidation"
    if "concurr" in normalized or "race" in normalized:
        return "missing_concurrency_control"
    return normalized


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, list):
        scenarios = payload
    elif isinstance(payload, dict) and isinstance(payload.get("scenarios"), list):
        scenarios = payload["scenarios"]
    elif isinstance(payload, dict) and isinstance(payload.get("items"), list):
        scenarios = payload["items"]
    else:
        raise ValueError("scenario file must be an array or an object with a scenarios array")
    if not all(isinstance(item, dict) for item in scenarios):
        raise ValueError("every scenario must be an object")
    return scenarios


def locate_rubric(scenario_path: Path, requested: str | None) -> Path:
    if requested:
        return Path(requested).resolve()
    candidates = [
        scenario_path.parent / "rubric.json",
        ROOT / "tests" / "benchmark" / "rubric.json",
        ROOT / "tests" / "fixtures" / "rubric.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise ValueError("could not locate rubric.json; pass --rubric-file")


def normalize_status(value: Any) -> str:
    status = normalize_text(value).upper().replace(" ", "_")
    if status == "NOTRUN":
        status = "NOT_RUN"
    if status == "NOTAPPLICABLE":
        status = "NOT_APPLICABLE"
    if status not in STATUSES and status not in EXECUTED_STATUSES:
        raise ValueError(f"unsupported response status: {value!r}")
    return status


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def field_items(scenario: dict[str, Any], source: str) -> list[Any]:
    value = scenario.get(source)
    if isinstance(value, dict):
        # A rubric-like dimension map is useful for required_signals; preserve
        # its keys as labels instead of treating the mapping as one opaque item.
        result: list[Any] = []
        for key, nested in value.items():
            for item in as_list(nested):
                if isinstance(item, dict):
                    item = {**item, "dimension": item.get("dimension", key)}
                else:
                    item = {"label": str(item), "dimension": key}
                result.append(item)
        return result
    return as_list(value)


def spec_label(spec: dict[str, Any]) -> str:
    for key in ("label", "text", "signal", "description", "id", "name"):
        if spec.get(key):
            return str(spec[key])
    return ""


def spec_terms(spec: dict[str, Any]) -> list[Any]:
    result: list[Any] = []
    for key in ("terms", "keywords", "patterns", "aliases", "signals"):
        value = spec.get(key)
        if isinstance(value, list):
            result.extend(value)
        elif value:
            result.append(value)
    label = spec_label(spec)
    if label:
        result.append(label)
    return result


def normalize_specs(value: Any, source: str) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for dimension, nested in value.items():
            for index, item in enumerate(as_list(nested)):
                if isinstance(item, dict):
                    spec = dict(item)
                else:
                    spec = {"label": str(item)}
                spec.setdefault("dimension", dimension if str(dimension).upper() in DIMENSION_DEFINITIONS else None)
                spec.setdefault("id", f"{source}-{index + 1}")
                specs.append(spec)
        return specs
    for index, item in enumerate(as_list(value)):
        if isinstance(item, dict):
            spec = dict(item)
        else:
            spec = {"label": str(item)}
        spec.setdefault("id", f"{source}-{index + 1}")
        specs.append(spec)
    return specs


def alias_group_for(token_or_phrase: str) -> set[str] | None:
    normalized = normalize_text(token_or_phrase)
    for group in ALIAS_GROUPS:
        if normalized in group:
            return group
    return None


def phrase_match(text_normalized: str, phrase: str) -> bool:
    phrase_normalized = normalize_text(phrase)
    if not phrase_normalized:
        return False
    if phrase_normalized in text_normalized:
        return True
    phrase_tokens = tokens(phrase_normalized, meaningful=True)
    if not phrase_tokens:
        return False
    text_tokens = set(tokens(text_normalized))
    expanded_hits = 0
    for token in phrase_tokens:
        group = alias_group_for(token)
        if group and any(alias in text_normalized for alias in group):
            expanded_hits += 1
        elif token in text_tokens:
            expanded_hits += 1
    # Long source facts are intentionally fuzzy enough to survive paraphrase,
    # while short signals still require all meaningful terms.
    required = len(phrase_tokens) if len(phrase_tokens) <= 3 else max(2, math.ceil(len(phrase_tokens) * 0.6))
    return expanded_hits >= required


def concept_matches(text: str, concept: Any) -> bool:
    if isinstance(concept, dict):
        candidates = spec_terms(concept)
    else:
        candidates = [concept]
    normalized = normalize_text(text)
    for candidate in candidates:
        if isinstance(candidate, dict):
            candidate = spec_label(candidate)
        if candidate and phrase_match(normalized, str(candidate)):
            return True
    return False


def evidence_for(text: str, concepts: Iterable[Any]) -> str | None:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    for sentence in sentences:
        if any(concept_matches(sentence, concept) for concept in concepts):
            return sentence.strip()[:240]
    return None


def coverage(text: str, items: list[Any]) -> tuple[int, int, list[str], list[str], list[str]]:
    matched = 0
    matched_labels: list[str] = []
    missing_labels: list[str] = []
    evidence: list[str] = []
    for item in items:
        label = spec_label(item) if isinstance(item, dict) else str(item)
        if concept_matches(text, item):
            matched += 1
            matched_labels.append(label)
            snippet = evidence_for(text, spec_terms(item) if isinstance(item, dict) else [item])
            if snippet and snippet not in evidence:
                evidence.append(snippet)
        else:
            missing_labels.append(label)
    return matched, len(items), matched_labels, missing_labels, evidence


def ratio_score(matched: int, total: int) -> int | None:
    if total == 0:
        return None
    ratio = matched / total
    if ratio <= 0:
        return 0
    if ratio <= 0.25:
        return 1
    if ratio <= 0.5:
        return 2
    if ratio < 1:
        return 3
    return 4


def score_average(values: list[int]) -> int:
    if not values:
        return 4
    return max(0, min(4, math.floor(sum(values) / len(values) + 0.5)))


def classify_signal(text: str) -> str | None:
    normalized = normalize_text(text)
    # More specific dimensions must win before broad words such as "failure"
    # and "design" are considered.
    ordered = [
        "D12",
        "D13",
        "D15",
        "D18",
        "D17",
        "D16",
        "D19",
        "D20",
        "D22",
        "D21",
        "D14",
        "D11",
        "D7",
        "D9",
        "D10",
        "D8",
        "D6",
        "D5",
        "D4",
    ]
    for dimension in ordered:
        if any(phrase_match(normalized, marker) for marker in DIMENSION_MARKERS[dimension]):
            return dimension
    return None


def rubric_dimension_metadata(rubric: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metadata = {key: dict(value) for key, value in DIMENSION_DEFINITIONS.items()}
    raw = rubric.get("dimensions") or rubric.get("decision_dimensions") or rubric.get("rubric")
    entries: list[Any] = []
    if isinstance(raw, dict):
        for key, value in raw.items():
            if str(key).upper() in DIMENSION_DEFINITIONS:
                entry = dict(value) if isinstance(value, dict) else {"name": value}
                entry["id"] = str(key).upper()
                entries.append(entry)
    elif isinstance(raw, list):
        entries = raw
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        identifier = str(entry.get("id") or entry.get("key") or "").upper()
        if identifier in metadata:
            merged = dict(metadata[identifier])
            merged.update(entry)
            metadata[identifier] = merged
    return metadata


def relevant_required_specs(scenario: dict[str, Any], dimension: str) -> list[dict[str, Any]]:
    specs = normalize_specs(scenario.get("required_signals", []), "required_signal")
    relevant: list[dict[str, Any]] = []
    for spec in specs:
        explicit = str(spec.get("dimension") or spec.get("dimension_id") or "").upper()
        if explicit:
            if explicit == dimension:
                relevant.append(spec)
            continue
        label = spec_label(spec)
        inferred = classify_signal(label)
        if inferred == dimension:
            relevant.append(spec)
    return relevant


def dimension_items(scenario: dict[str, Any], dimension: str) -> list[Any]:
    sources = DIMENSION_DEFINITIONS[dimension]["sources"]
    result: list[Any] = []
    for source in sources:
        items = field_items(scenario, source)
        # Required signals are scored separately.  Including them here would
        # double-count a signal and make a concise response look verbose.
        if source == "required_signals":
            continue
        result.extend(items)
    return result


def dimension_score(
    scenario: dict[str, Any],
    text: str,
    dimension: str,
    metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    items = dimension_items(scenario, dimension)
    required = relevant_required_specs(scenario, dimension)
    marker_items = DIMENSION_MARKERS[dimension]
    components: list[int] = []
    checks: list[dict[str, Any]] = []
    matched_signals: list[str] = []
    missing_signals: list[str] = []
    evidence: list[str] = []

    if items:
        matched, total, labels, missing, snippets = coverage(text, items)
        item_score = ratio_score(matched, total)
        assert item_score is not None
        components.append(item_score)
        matched_signals.extend(labels)
        missing_signals.extend(missing)
        evidence.extend(snippets)
        checks.append({
            "check": "scenario_context_coverage",
            "source_fields": DIMENSION_DEFINITIONS[dimension]["sources"],
            "matched": matched,
            "total": total,
            "score": item_score,
        })

    if required:
        matched, total, labels, missing, snippets = coverage(text, required)
        signal_score = ratio_score(matched, total)
        assert signal_score is not None
        components.append(signal_score)
        matched_signals.extend(labels)
        missing_signals.extend(missing)
        evidence.extend(snippets)
        checks.append({
            "check": "required_signal_coverage",
            "source_fields": ["required_signals"],
            "matched": matched,
            "total": total,
            "score": signal_score,
        })

    marker_matched, marker_total, marker_labels, marker_missing, marker_evidence = coverage(text, marker_items)
    # Markers are a supporting check, not a demand to repeat every rubric word.
    marker_score = 4 if marker_matched >= 2 else (3 if marker_matched == 1 else 0)
    if dimension in {"D4", "D5", "D7", "D9", "D11", "D15", "D18", "D19", "D20", "D21", "D22"}:
        components.append(marker_score)
        checks.append({
            "check": "explicit_reasoning_marker",
            "source_fields": ["rubric_markers"],
            "matched": marker_matched,
            "total": marker_total,
            "score": marker_score,
        })
    matched_signals.extend(marker_labels)
    evidence.extend(marker_evidence)

    # D23 has a bounded length component so verbosity never creates a score
    # advantage.  Relevance still comes from the scenario signal checks.
    if dimension == "D23":
        word_count = len(tokens(text))
        length_score = 4 if 20 <= word_count <= 260 else 3 if word_count <= 420 else 2 if word_count <= 700 else 1
        components.append(length_score)
        checks.append({"check": "bounded_context_length", "word_count": word_count, "score": length_score})

    if not components:
        score = 4
        applicability = "NOT_APPLICABLE"
    else:
        score = score_average(components)
        applicability = "APPLICABLE"

    definition = metadata[dimension]
    return {
        "id": dimension,
        "name": definition.get("name", DIMENSION_DEFINITIONS[dimension]["name"]),
        "score": score,
        "applicability": applicability,
        "checks": checks,
        "matched_signals": sorted(set(matched_signals)),
        "missing_signals": sorted(set(missing_signals)),
        "evidence": evidence[:8],
        "anchor": (definition.get("anchors") or definition.get("scoring") or None),
    }


def sentence_containing(text: str, pattern: str) -> str | None:
    try:
        match = re.search(pattern, text, re.IGNORECASE)
    except re.error:
        return None
    if not match:
        return None
    start = max(text.rfind(".", 0, match.start()), text.rfind("\n", 0, match.start())) + 1
    end_candidates = [position for position in (text.find(".", match.end()), text.find("\n", match.end())) if position >= 0]
    end = min(end_candidates) if end_candidates else len(text)
    return text[start:end].strip()[:240]


def negated_near(text: str, start: int, window: int = 70) -> bool:
    # Do not let a negation in a preceding sentence suppress a positive
    # mutation in the current sentence (for example, "no retry" followed by
    # "retry the charge without a key").
    sentence_start = max(text.rfind(".", 0, start), text.rfind(";", 0, start), text.rfind("\n", 0, start)) + 1
    prefix = normalize_text(text[max(sentence_start, start - window):start])
    return bool(re.search(r"\b(?:no|not|never|avoid|reject|without|do not|dont|cannot|cant|should not|shouldnt|must not|only if|unless)\b", prefix))


def affirmative_phrase(text: str, patterns: Iterable[str]) -> tuple[bool, str | None]:
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            if negated_near(text, match.start()):
                continue
            matched_normalized = normalize_text(match.group(0))
            if re.search(r"\b(?:not|never|cannot|cant|does not|doesnt|will not|wont|should not|shouldnt|must not)\b", matched_normalized):
                continue
            suffix = normalize_text(text[match.end():match.end() + 70])
            if re.match(r"^(?:is|was|will be|would be|remains)?\s*(?:not|never|unsupported|unproven|cannot|cant|does not|doesnt|will not|wont|should not|shouldnt|must not)\b", suffix):
                continue
            return True, text[max(0, text.rfind(".", 0, match.start()) + 1):text.find(".", match.end()) if text.find(".", match.end()) >= 0 else len(text)].strip()[:240]
    return False, None


def scenario_has_security_signal(scenario: dict[str, Any]) -> bool:
    values = []
    for key in ("prompt", "title", "current_facts", "invariants", "forces", "domains", "required_signals"):
        values.extend(field_items(scenario, key))
    combined = " ".join(spec_label(item) if isinstance(item, dict) else str(item) for item in values)
    return bool(re.search(r"auth|tenant|permission|security|webhook|privileg|trust|signature|payment", normalize_text(combined)))


def contains_unknown_marker(text: str) -> bool:
    return bool(re.search(r"\b(?:unknown|unclear|unspecified|not specified|not known|unconfirmed|assumption|assume|confirm|open question|need evidence|needs verification|to be determined|not yet established)\b", normalize_text(text)))


def has_recovery_marker(text: str) -> bool:
    return bool(re.search(r"\b(?:recover|recovery|reconcile|reconciliation|repair|resume|restart|replay|dead letter|dead letter queue|roll back|rollback|roll forward|operator)\b", normalize_text(text)))


def has_authz_marker(text: str) -> bool:
    normalized = normalize_text(text)
    return bool(re.search(r"\b(?:authorization|authz|authorize|permission|access control|default deny|tenant|actor|principal|trust boundary|signature)\b", normalized))


def has_compatibility_marker(text: str) -> bool:
    normalized = normalize_text(text)
    return bool(re.search(r"\b(?:compatib|mixed version|version skew|tolerant reader|backward|migration|migrate|backfill|expand contract|rollout|rollback|roll forward)\w*\b", normalized))


def add_failure(failures: list[dict[str, Any]], tag: str, reason: str, evidence: str | None) -> None:
    if any(item["canonical_tag"] == tag for item in failures):
        return
    failures.append({
        "tag": tag,
        "canonical_tag": tag,
        "reason": reason,
        "evidence": evidence,
    })


def detect_hard_failures(
    scenario: dict[str, Any],
    text: str,
    dimensions: dict[str, dict[str, Any]],
    rubric: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    raw_tags = scenario.get("hard_fail_tags", [])
    tags = []
    for raw in as_list(raw_tags):
        label = raw.get("tag") if isinstance(raw, dict) else raw
        if label:
            tags.append(str(label))
    canonical_tags = {canonical_tag(tag) for tag in tags}
    # A scenario without an explicit list still receives the global positive
    # safety checks.  A listed tag additionally enables absence checks such as
    # missing invariant or missing recovery.
    active = canonical_tags | {
        "unsafe_retry",
        "exactly_once",
        "direct_dual_write",
        "unknown_outcome",
        "unexecuted_runtime_claim",
        "unproven_readiness",
    }
    failures: list[dict[str, Any]] = []
    normalized = normalize_text(text)

    unsafe, evidence = affirmative_phrase(
        text,
        [
            r"\bretr(?:y|ies|ied|ying)\b[^.;]{0,120}\b(?:payment|charge|capture|non\s+idempotent|write|create|side effect|mutation)\b",
            r"\b(?:payment|charge|capture|non\s+idempotent|side effect|mutation)\b[^.;]{0,120}\bretr(?:y|ies|ied|ying)\b",
            r"\bthree\s+retries\b",
            r"\bunlimited\s+retries\b",
        ],
    )
    if unsafe:
        # A nearby protection clause makes this a bounded-safe retry rather
        # than the hard-fail behavior the tag names.
        protection, _ = affirmative_phrase(
            evidence or "",
            [r"\bidempotenc\w*\b", r"\bdedup\w*\b", r"\breplay safe\b", r"\brequest key\b", r"\bonly after\b", r"\bunless\b", r"\bbounded\b", r"\bdeadline\b", r"\bbackoff\b", r"\bjitter\b", r"\breconcil\w*\b"],
        )
        if not protection:
            add_failure(failures, "unsafe_retry", "retries are recommended around a non-idempotent or side-effecting operation without a local safety boundary", evidence)

    exactly_once, evidence = affirmative_phrase(text, [r"\bexactly\s+once\b"])
    # A local version counter may legitimately increment exactly once; that is
    # not the unsupported end-to-end delivery/effect promise this detector is
    # meant to catch.
    local_counter = bool(re.search(r"\b(?:version|counter|sequence|increment|increments|updated?)\b", normalize_text(evidence or "")))
    if exactly_once and not local_counter:
        add_failure(failures, "exactly_once", "the response promises exactly-once behavior without defensible end-to-end semantics", evidence)

    client_id, evidence = affirmative_phrase(
        text,
        [
            r"\b(?:client|object|resource)\s+(?:id|identifier)\b[^.]{0,80}\b(?:proves?|is|grants?|means?)\b[^.]{0,50}\b(?:access|authorization|ownership|permission)\b",
            r"\btrust\b[^.]{0,40}\b(?:client|object|resource)\s+(?:id|identifier)\b",
        ],
    )
    if client_id:
        add_failure(failures, "missing_authz", "a client-provided identifier is treated as authorization", evidence)

    dual_write, evidence = affirmative_phrase(
        text,
        [
            r"\bdual\s+writ(?:e|es|ing)\b",
            r"\b(?:save|write|commit)\b[^.]{0,100}\b(?:then|and)\b[^.]{0,30}\b(?:publish|send|emit)\b",
            r"\b(?:publish|send|emit)\b[^.]{0,100}\b(?:then|and)\b[^.]{0,30}\b(?:save|write|commit)\b",
        ],
    )
    if dual_write and not re.search(r"\b(?:avoid|reject|do not|dont|instead of|outbox|transactional outbox|reconciliation|pending state)\b", normalize_text(evidence or "")):
        add_failure(failures, "direct_dual_write", "database state and an external publication are written directly without a failure boundary", evidence)

    if "missing_authz" in active and scenario_has_security_signal(scenario) and not has_authz_marker(text):
        add_failure(failures, "missing_authz", "the security-sensitive scenario has no server-side authorization signal", None)

    if "missing_duplicate_safety" in active:
        unsafe_duplicate, evidence = affirmative_phrase(
            text,
            [
                r"\b(?:process|handle|accept)\b[^.]{0,60}\b(?:every|each)\b[^.]{0,40}\b(?:delivery|webhook|event|request)\b",
                r"\bduplicate\s+delivery\b[^.]{0,60}\b(?:normally|ordinary|again|without)\b",
            ],
        )
        if unsafe_duplicate:
            add_failure(failures, "missing_duplicate_safety", "duplicate-capable delivery is not made safe", evidence)

    if "unknown_outcome" in active:
        unsafe_outcome, evidence = affirmative_phrase(
            text,
            [
                r"\b(?:timeout|timed out|network failure)\b[^.]{0,80}\b(?:means?|is|was)\b[^.]{0,40}\b(?:failed|failure|not committed|did not commit)\b",
                r"\bassume\b[^.]{0,60}\b(?:failed|failure|not committed|did not commit)\b",
                r"\b(?:retry|create|submit)\b[^.]{0,100}\b(?:label|charge|side effect|request)\b[^.]{0,60}\b(?:directly|immediately|again)\b",
                r"\b(?:retry|create|submit)\b[^.]{0,100}\b(?:without|before)\b[^.]{0,40}\b(?:query|reconcile|status|reference)\b",
            ],
        )
        evidence_normalized = normalize_text(evidence or "")
        explicitly_safe = bool(re.search(r"\b(?:not|never|do not|dont)\b[^.]{0,60}\b(?:failed|failure|retry|create|submit)\b", evidence_normalized))
        if unsafe_outcome and not explicitly_safe and re.search(r"\b(?:timeout|timed out|unknown outcome|remote|provider|network)\b", normalized):
            if not re.search(r"\b(?:query|reconcil|pending|indeterminate|status|reference)\b", evidence_normalized):
                add_failure(failures, "unknown_outcome", "a remote timeout is treated as a known failure or retried without reconciliation", evidence)

    if "missing_invariant" in active:
        invariant_items = field_items(scenario, "invariants")
        invariant_coverage = coverage(text, invariant_items)[0] if invariant_items else 0
        if invariant_items and invariant_coverage == 0:
            add_failure(failures, "missing_invariant", "the response does not state or preserve the scenario invariant", None)

    if "missing_recovery" in active:
        explicit_missing_recovery, evidence = affirmative_phrase(
            text,
            [
                r"\b(?:no|without)\b[^.]{0,40}\b(?:recovery|repair|reconciliation|next[- ]step|runbook)\b",
                r"\b(?:recovery|repair|reconciliation)\b[^.]{0,30}\b(?:is|are)\b[^.]{0,20}\b(?:not|undefined|missing)\b",
                r"\b(?:recovery|repair)\b[^.]{0,30}\b(?:includes|has)\b[^.]{0,20}\b(?:no|only)\b",
            ],
        )
        if explicit_missing_recovery or not has_recovery_marker(text):
            add_failure(failures, "missing_recovery", "failure handling has no recovery, repair, reconciliation, or operator path", evidence)

    if "removed_migration_compatibility" in active and (has_compatibility_marker(" ".join(str(value) for key in ("prompt", "unknowns", "forces", "current_facts") for value in field_items(scenario, key))) or "migration" in normalized or "version" in normalized):
        incompatible, evidence = affirmative_phrase(
            text,
            [
                r"\b(?:old|legacy|mixed[- ]version)\b[^.]{0,80}\b(?:broken|incompatible|cannot read|invalid|removed)\b",
                r"\b(?:drop|remove|replace)\b[^.]{0,60}\b(?:old|legacy)\b",
            ],
        )
        if incompatible or not has_compatibility_marker(text):
            add_failure(failures, "removed_migration_compatibility", "the response omits or explicitly breaks mixed-version, migration, compatibility, or rollback handling", evidence)

    if "unknown_hiding" in active and field_items(scenario, "unknowns") and not contains_unknown_marker(text):
        add_failure(failures, "unknown_hiding", "known unknowns are presented as settled facts", None)

    if "invented_requirement" in active:
        explicit_invention, evidence = affirmative_phrase(
            text,
            [
                r"\b(?:the|this)\s+requirement\s+is\b",
                r"\bmust\s+(?:use|adopt|run|guarantee|support)\s+(?:kafka|redis|kubernetes|microservices|exactly\s+once|99(?:\.\d+)?%|[0-9]+\s*ms)",
                r"\b(?:required|must)\s+(?:be|provide)\b[^.]{0,80}\b(?:99(?:\.\d+)?%|exactly\s+once|zero\s+downtime|unlimited)\b",
            ],
        )
        if explicit_invention:
            add_failure(failures, "invented_requirement", "an unsupported requirement is asserted as if it came from the scenario", evidence)

    if "cargo_cult_microservices" in active:
        microservices, evidence = affirmative_phrase(text, [r"\bmicroservices?\b"])
        evidence_normalized = normalize_text(evidence or "")
        if microservices and not re.search(r"\b(?:independent deployment|independent scaling|fault isolation|bounded context|ownership|technology isolation|driver)\b", evidence_normalized):
            add_failure(failures, "cargo_cult_microservices", "microservices are selected without an independent driver", evidence)

    if "cargo_cult_event_sourcing" in active:
        sourcing, evidence = affirmative_phrase(text, [r"\bevent sourcing\b"])
        evidence_normalized = normalize_text(evidence or "")
        if sourcing and not re.search(r"\b(?:temporal reconstruction|immutable history|replay|event native|privacy|schema evolution)\b", evidence_normalized):
            add_failure(failures, "cargo_cult_event_sourcing", "event sourcing is selected without an event-native or temporal requirement", evidence)

    if "missing_cache_invalidation" in active:
        cache_design = re.search(r"\b(?:add|use|introduce|put)\b[^.]{0,50}\b(?:redis|cache|caching)\b", normalized)
        if cache_design:
            window_end = normalized.find(".", cache_design.end())
            if window_end < 0:
                window_end = len(normalized)
            next_end = normalized.find(".", window_end + 1)
            if next_end < 0:
                next_end = len(normalized)
            design_window = normalized[cache_design.start():next_end]
            if not re.search(r"invalidation|stale|source of truth|stampede|expiry|ttl", design_window):
                add_failure(failures, "missing_cache_invalidation", "a cache is introduced without source-of-truth or invalidation semantics", design_window[:240])

    if "missing_concurrency_control" in active and re.search(r"concurr|simult|race|double booking|multiple clients", normalized) and not re.search(r"unique|constraint|cas|compare and swap|lock|version|serializ|conflict", normalized):
        add_failure(failures, "missing_concurrency_control", "a concurrent write has no atomic conflict control", None)

    runtime_claim, evidence = affirmative_phrase(
        text,
        [
            r"\b(?:verified|proven|passed|confirmed|tested)\b[^.]{0,80}\b(?:runtime|production|security|recovery|concurrency|migration|boundary|ready|claim)\b",
            r"\b(?:production|security|release)\s+ready\b",
            r"\b(?:cannot|will not|never)\s+fail\b",
        ],
    )
    if runtime_claim and not re.search(r"\b(?:not run|not executed|not yet run|needs? (?:test|evidence|verification)|blocked|stale|plan to)\b", normalized):
        tag = "unproven_readiness" if re.search(r"ready|production|security", normalized) else "unexecuted_runtime_claim"
        add_failure(failures, tag, "runtime or readiness evidence is claimed without an executed observation", evidence)

    # A rubric may add a condition with a literal trigger.  This extension is
    # deliberately additive; it cannot remove a built-in safety rule.
    rubric_conditions = rubric.get("hard_fail_conditions", [])
    if isinstance(rubric_conditions, dict):
        rubric_conditions = [{"tag": key, **(value if isinstance(value, dict) else {"description": value})} for key, value in rubric_conditions.items()]
    for condition in as_list(rubric_conditions):
        if not isinstance(condition, dict):
            continue
        tag = canonical_tag(condition.get("tag") or condition.get("id") or condition.get("name"))
        patterns = condition.get("patterns") or condition.get("signals") or condition.get("terms")
        if not patterns:
            continue
        if any(phrase_match(normalized, str(pattern)) for pattern in as_list(patterns)):
            negated = any(negated_near(text, match.start()) for pattern in as_list(patterns) for match in re.finditer(re.escape(normalize_text(pattern)), normalized))
            if not negated:
                add_failure(failures, tag, str(condition.get("description") or "rubric hard-fail condition matched"), sentence_containing(text, re.escape(normalize_text(as_list(patterns)[0]))))

    # Only report tags the scenario declared, except for global detectors that
    # are independently unsafe.  This keeps hard-fail evidence scenario-local.
    declared = {canonical_tag(tag) for tag in tags}
    global_tags = {"unsafe_retry", "exactly_once", "direct_dual_write", "unknown_outcome", "unexecuted_runtime_claim", "unproven_readiness"}
    filtered = [item for item in failures if item["canonical_tag"] in declared or item["canonical_tag"] in global_tags]
    filtered.sort(key=lambda item: (item["canonical_tag"], item.get("reason", "")))
    return filtered, tags


def pass_threshold(rubric: dict[str, Any]) -> float:
    raw = rubric.get("pass_threshold")
    if raw is None:
        thresholds = rubric.get("thresholds")
        if isinstance(thresholds, dict):
            raw = thresholds.get("response_average") or thresholds.get("minimum_average") or thresholds.get("score")
    if raw is None:
        return 2.5
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 2.5
    return value / 25 if value > 4 else value


def calibration(status: str, average: float | None, hard_failures: list[dict[str, Any]]) -> str:
    if status in {"BLOCKED", "STALE", "NOT_RUN", "NOT_APPLICABLE"}:
        return "BLOCKED" if status == "BLOCKED" else status
    if hard_failures:
        return "HIGH RISK"
    if average is None:
        return "UNKNOWN"
    if average >= 3.5:
        return "SAFE"
    if average >= 2.75:
        return "LIKELY SAFE"
    if average >= 1.75:
        return "UNKNOWN"
    return "HIGH RISK"


def score_record(
    record: dict[str, Any],
    scenarios_by_id: dict[str, dict[str, Any]],
    rubric: dict[str, Any],
    metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    scenario_id = str(record.get("scenario_id", ""))
    input_status = normalize_status(record.get("status"))
    lane = str(record.get("lane", ""))
    base: dict[str, Any] = {
        "scenario_id": scenario_id,
        "lane": lane,
        "model": record.get("model"),
        "captured_at": record.get("captured_at"),
        "input_status": input_status,
        "executed": False,
        "score": None,
        "score_percent": None,
        "average_0_4": None,
        "dimensions": {},
        "hard_failures": [],
        "hard_fail_tags_checked": [],
        "calibration": calibration(input_status if input_status in STATUSES else "PASS", None, []),
    }
    if scenario_id not in scenarios_by_id:
        base["status"] = "FAIL" if input_status in EXECUTED_STATUSES else input_status
        base["extra"] = True
        base["validation_errors"] = ["scenario_id is not present in the scenario corpus"]
        return base
    if input_status not in EXECUTED_STATUSES:
        base["status"] = input_status
        base["calibration"] = calibration(input_status, None, [])
        return base

    scenario = scenarios_by_id[scenario_id]
    text = record.get("text")
    scoring_context = record.get("scoring_context", "")
    validation_errors: list[str] = []
    if not isinstance(text, str) or not text.strip():
        validation_errors.append("executed response has no non-empty text")
        text = ""
    if not isinstance(scoring_context, str):
        validation_errors.append("scoring_context must be text when supplied")
        scoring_context = ""
    # A task context is a fixed covariate shared by control and mutation lanes.
    # It may inform dimension applicability, but hard-fail detectors inspect
    # only the captured response text so a mutation cannot be masked by the
    # scenario contract.
    dimension_text = f"{text}\nTask context (shared across lanes):\n{scoring_context}" if scoring_context.strip() else text
    dimensions = {dimension: dimension_score(scenario, dimension_text, dimension, metadata) for dimension in DIMENSION_DEFINITIONS}
    hard_failures, checked_tags = detect_hard_failures(scenario, text, dimensions, rubric)
    scores = [item["score"] for item in dimensions.values() if isinstance(item.get("score"), int)]
    average = sum(scores) / len(scores) if scores else None
    threshold = pass_threshold(rubric)
    result_status = "PASS" if not validation_errors and not hard_failures and average is not None and average >= threshold else "FAIL"
    base.update(
        {
            "status": result_status,
            "executed": True,
            "score": round((average / 4) * 100, 2) if average is not None else None,
            "score_percent": round((average / 4) * 100, 2) if average is not None else None,
            "average_0_4": round(average, 4) if average is not None else None,
            "dimensions": dimensions,
            "hard_failures": hard_failures,
            "hard_fail_tags_checked": sorted(set(checked_tags)),
            "calibration": calibration(result_status, average, hard_failures),
        }
    )
    if validation_errors:
        base["validation_errors"] = validation_errors
    return base


def parse_timestamp(value: Any) -> tuple[bool, str | None]:
    if value in (None, ""):
        return False, None
    raw = str(value)
    candidate = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return False, raw
    return True, parsed.isoformat()


def freshness_metadata(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    timestamps: list[str] = []
    invalid: list[int] = []
    stale: list[int] = []
    for index, record in enumerate(records):
        status = str(record.get("status", "")).upper().replace("-", "_")
        counts[status] += 1
        valid, normalized = parse_timestamp(record.get("captured_at"))
        if valid and normalized:
            timestamps.append(normalized)
        elif record.get("captured_at") not in (None, ""):
            invalid.append(index)
        if status == "STALE":
            stale.append(index)
    return {
        "policy": "explicit status only; this scorer does not infer age or execution from a fixture/model label",
        "status_counts": dict(sorted(counts.items())),
        "captured_at_min": min(timestamps) if timestamps else None,
        "captured_at_max": max(timestamps) if timestamps else None,
        "invalid_timestamp_record_indices": invalid,
        "stale_record_indices": stale,
        "status": "STALE" if stale else "UNVERIFIED_CURRENTNESS",
    }


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    executed = [result for result in results if result.get("executed") and result.get("average_0_4") is not None]
    hard_failure_count = sum(len(result.get("hard_failures", [])) for result in executed)
    scores = [float(result["average_0_4"]) for result in executed]
    overall_average = sum(scores) / len(scores) if scores else None
    by_lane: dict[str, Any] = {}
    for lane in sorted({str(result.get("lane", "")) for result in executed}):
        lane_results = [result for result in executed if str(result.get("lane", "")) == lane]
        lane_average = sum(float(result["average_0_4"]) for result in lane_results) / len(lane_results)
        by_lane[lane] = {
            "executed_records": len(lane_results),
            "average_0_4": round(lane_average, 4),
            "score": round(lane_average / 4 * 100, 2),
            "hard_failures": sum(len(result.get("hard_failures", [])) for result in lane_results),
        }
    return {
        "executed_records": len(executed),
        "scored_dimension_values": len(executed) * len(DIMENSION_DEFINITIONS),
        "average_0_4": round(overall_average, 4) if overall_average is not None else None,
        "score": round(overall_average / 4 * 100, 2) if overall_average is not None else None,
        "hard_failures": hard_failure_count,
        "by_lane": by_lane,
    }


def build_report(scenario_path: Path, response_path: Path, rubric_path: Path) -> dict[str, Any]:
    scenarios = load_scenarios(scenario_path)
    rubric = load_json(rubric_path)
    if not isinstance(rubric, dict):
        raise ValueError("rubric file must contain an object")
    response_payload = load_json(response_path)
    if not isinstance(response_payload, list):
        raise ValueError("response file must contain an array of response records")
    if not all(isinstance(item, dict) for item in response_payload):
        raise ValueError("every response record must be an object")

    scenarios_by_id: dict[str, dict[str, Any]] = {}
    corpus_errors: list[str] = []
    for index, scenario in enumerate(scenarios):
        identifier = str(scenario.get("id", ""))
        if not identifier:
            corpus_errors.append(f"scenario[{index}] is missing id")
            continue
        if identifier in scenarios_by_id:
            corpus_errors.append(f"duplicate scenario id: {identifier}")
        scenarios_by_id[identifier] = scenario

    metadata = rubric_dimension_metadata(rubric)
    results = [score_record(record, scenarios_by_id, rubric, metadata) for record in response_payload]
    present_ids = {str(record.get("scenario_id", "")) for record in response_payload if str(record.get("scenario_id", "")) in scenarios_by_id}
    missing_ids = sorted(set(scenarios_by_id) - present_ids)
    extra_records = [
        {"index": index, "scenario_id": str(record.get("scenario_id", "")), "lane": record.get("lane"), "reason": "unknown scenario_id"}
        for index, record in enumerate(response_payload)
        if str(record.get("scenario_id", "")) not in scenarios_by_id
    ]
    seen_keys: set[tuple[str, str]] = set()
    duplicate_records: list[dict[str, Any]] = []
    for index, record in enumerate(response_payload):
        key = (str(record.get("scenario_id", "")), str(record.get("lane", "")))
        if key in seen_keys:
            duplicate_records.append({"index": index, "scenario_id": key[0], "lane": key[1], "reason": "duplicate scenario/lane record"})
        seen_keys.add(key)

    response_path_resolved = response_path.resolve()
    corpus_fingerprint = sha256_bytes(canonical_json({"scenarios": scenarios, "rubric": rubric}))
    report = {
        "schema_version": "BP-RESPONSE-SCORE-1",
        "scope": "DETERMINISTIC_CAPTURED_RESPONSE_SCORING",
        "model_execution": "NOT_INFERRED",
        "model_execution_note": "A supplied response record, model name, or evaluator fixture is not evidence that a consumer model ran.",
        "scenario_count": len(scenarios_by_id),
        "response_record_count": len(response_payload),
        "status_taxonomy": sorted(STATUSES),
        "pass_threshold_0_4": pass_threshold(rubric),
        "corpus_errors": corpus_errors,
        "missing_records": [{"scenario_id": identifier, "reason": "no response record"} for identifier in missing_ids],
        "extra_records": extra_records,
        "duplicate_records": duplicate_records,
        "missing_scenario_ids": missing_ids,
        "extra_scenario_ids": sorted({item["scenario_id"] for item in extra_records}),
        "freshness": freshness_metadata(response_payload),
        "fingerprints": {
            "scenario_file": {"path": str(scenario_path.resolve()), "sha256": sha256_file(scenario_path)},
            "rubric_file": {"path": str(rubric_path.resolve()), "sha256": sha256_file(rubric_path)},
            "response_file": {"path": str(response_path_resolved), "sha256": sha256_file(response_path)},
            "corpus_sha256": corpus_fingerprint,
        },
        "results": results,
        "overall": aggregate(results),
    }
    # `overall_score` is a deliberately explicit nullable alias.  It never
    # receives a value from NOT_RUN/BLOCKED/STALE/NOT_APPLICABLE records.
    report["overall_score"] = report["overall"]["score"]
    report["overall_score_0_4"] = report["overall"]["average_0_4"]
    result_statuses = {str(item.get("status", "")) for item in results}
    structural_error = bool(corpus_errors or missing_ids or extra_records or duplicate_records)
    if structural_error:
        report_status = "FAIL"
    elif not results:
        report_status = "NOT_RUN"
    elif "FAIL" in result_statuses:
        report_status = "FAIL"
    elif "STALE" in result_statuses:
        report_status = "STALE"
    elif "BLOCKED" in result_statuses:
        report_status = "BLOCKED"
    elif result_statuses and result_statuses <= {"NOT_APPLICABLE"}:
        report_status = "NOT_APPLICABLE"
    else:
        report_status = "PASS"
    report["status"] = report_status
    report["errors"] = ([] if not structural_error else [
        "response capture is incomplete or structurally invalid; see missing/extra/duplicate fields"
    ])
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario-file", required=True, help="JSON array (or object with scenarios) of benchmark scenarios")
    parser.add_argument("--response-file", required=True, help="JSON array of captured response records")
    parser.add_argument("--rubric-file", help="optional rubric JSON; defaults to a sibling rubric.json or the package fixture")
    args = parser.parse_args(argv)
    try:
        scenario_path = Path(args.scenario_file).resolve()
        response_path = Path(args.response_file).resolve()
        rubric_path = locate_rubric(scenario_path, args.rubric_file)
        report = build_report(scenario_path, response_path, rubric_path)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
