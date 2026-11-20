#!/usr/bin/env python3
"""Offline read-only validation of the IRG AI reference seed.

This validator distinguishes:
- integrity: copied artifacts are intact and internally consistent;
- completion: required reference areas are actually populated and portable.

No network, production imports, corpus writes, database calls or index mutation.
Run:
  python scripts/validate_reference_seed.py
  python scripts/validate_reference_seed.py --strict
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_POPULATED_DIRS = (
    "source_reference/identity",
    "source_reference/retrieval",
    "source_reference/context",
    "source_reference/contracts",
    "source_reference/structural",
    "source_snapshot",
    "research/structural",
    "reports/reference/v1",
    "reports/reference/v1_5",
    "reports/reference/corpus",
    "reports/reference/structural",
)

# Exact historical transfers may contain their own original references. Current
# synthesis must never require an external storage service to be understood.
PORTABLE_CURRENT_FILES = (
    "README.md",
    "REFERENCE_POLICY.md",
    "REFERENCE_INDEX.md",
    "SOURCE_MANIFEST.md",
    "CURRENT_REFERENCE_STATE.md",
    "P0_COVERAGE_MATRIX.md",
    "P0_SEED_LEDGER.md",
    "CLAIM_REGISTER.jsonl",
    "architecture/ARCHITECTURE_EVOLUTION.md",
    "architecture/DURABLE_ARCHITECTURE_PRINCIPLES.md",
    "architecture/TARGET_REFERENCE_PIPELINE.md",
    "architecture/ARCHITECTURAL_DEBT_AND_FAILURES.md",
    "evaluation/EMPIRICAL_FINDINGS.md",
    "evaluation/EVALUATION_EVOLUTION.md",
    "evaluation/EXPERIMENT_ADDENDUM_20261120.md",
    "evaluation/EXPERIMENT_REGISTER.md",
    "evaluation/FAILURE_REGISTER.md",
    "evaluation/INTEGRITY_FINDINGS_20261120.md",
    "evaluation/METRIC_DEFINITIONS.md",
    "evaluation/REJECTED_MECHANISMS.md",
    "governance/AUTONOMY_BOUNDARIES.md",
    "governance/EVALUATION_INTEGRITY.md",
    "governance/EXPERIMENT_PROMOTION_POLICY.md",
    "governance/GOVERNANCE_PRINCIPLES.md",
    "governance/SOURCE_AUTHORITY.md",
    "lessons/CLEAN_LAB_CARRY_FORWARD.md",
    "reports/reference/ablations/STANDARD_VS_FULL_VIEW_P2_ABLATION.md",
    "reports/reference/audits/CLEAN_LAB_AUDIT_SYNTHESIS.md",
    "reports/reference/evaluation/EVALUATION_RESULTS_CROSSWALK.md",
    "reports/reference/scale/CORPUS_SCALE_EVOLUTION.md",
    "reports/reference/scale/EXPANDED_CORPUS_SCALE_TEST.md",
    "timeline/BUILD_TIMELINE.md",
)

EXTERNAL_STORAGE_URL = re.compile(r"https?://(?:drive|docs)\.google\.com/", re.I)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def substantive_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return [
        p for p in path.rglob("*")
        if p.is_file() and p.name != ".gitkeep" and p.stat().st_size > 0
    ]


def validate(root: Path = ROOT) -> dict:
    findings: list[dict] = []

    ledger_path = root / "evaluation" / "FROZEN_TRANSFER_LEDGER.json"
    if not ledger_path.is_file():
        return {"status": "FAIL", "findings": [{"severity": "ERROR", "code": "LEDGER_MISSING"}]}

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    checked = 0
    withheld_statuses = {"VERIFIED_PRIVATE_WITHHELD", "VERIFIED_DRIVE_PRIVATE_WITHHELD"}

    for record in ledger["records"]:
        path_name = record.get("repo_path")
        if record["status"] in withheld_statuses:
            findings.append({
                "severity": "BLOCKER",
                "code": "PRIVATE_SOURCE_NOT_IN_REPO",
                "artifact": record["name"],
            })
            continue
        if not path_name:
            findings.append({"severity": "ERROR", "code": "MISSING_REPO_PATH", "artifact": record["name"]})
            continue
        path = root / path_name
        if not path.is_file():
            findings.append({"severity": "ERROR", "code": "TRANSFER_MISSING", "artifact": path_name})
            continue
        if path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]:
            findings.append({"severity": "ERROR", "code": "TRANSFER_HASH_MISMATCH", "artifact": path_name})
            continue
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, UnicodeError) as exc:
                findings.append({
                    "severity": "ERROR",
                    "code": "INVALID_JSON",
                    "artifact": path_name,
                    "error": str(exc),
                })
                continue
        checked += 1

    # Frozen binding checks.
    frozen = root / "evaluation" / "frozen"
    try:
        benchmark = json.loads((frozen / "benchmark_population_registry_v1.json").read_text())
        metric = json.loads((frozen / "e2e_metric_registry_v1.json").read_text())
        gate = json.loads((frozen / "V2_GATE_MANIFEST.json").read_text())
        master = json.loads((frozen / "V2_MASTER_REGRESSION_MANIFEST_v1.json").read_text())
        evaluator = json.loads((frozen / "V2_EVALUATOR_MANIFEST_v1.json").read_text())
        if benchmark.get("population_count") != len(benchmark.get("populations", [])):
            findings.append({"severity": "ERROR", "code": "BENCHMARK_COUNT_MISMATCH"})
        if metric.get("metric_count") != len(metric.get("metrics", [])):
            findings.append({"severity": "ERROR", "code": "METRIC_COUNT_MISMATCH"})
        if gate["master_population_authority"]["population_sha256"] != master["artifact_sha256"]["population"]:
            findings.append({"severity": "ERROR", "code": "POPULATION_BINDING_MISMATCH"})
        if evaluator["authority"]["gate_manifest_sha256"] != digest(frozen / "V2_GATE_MANIFEST.json"):
            findings.append({"severity": "ERROR", "code": "GATE_BINDING_MISMATCH"})
        if evaluator["authority"]["master_manifest_sha256"] != digest(frozen / "V2_MASTER_REGRESSION_MANIFEST_v1.json"):
            findings.append({
                "severity": "BLOCKER",
                "code": "MASTER_MANIFEST_REVISION_CONFLICT",
                "expected": evaluator["authority"]["master_manifest_sha256"],
                "observed": digest(frozen / "V2_MASTER_REGRESSION_MANIFEST_v1.json"),
            })
        if evaluator.get("qualification_status") != "NOT_EXECUTED":
            findings.append({
                "severity": "BLOCKER",
                "code": "EVALUATOR_QUALIFICATION_STATUS_CHANGED_REVIEW",
            })
    except (KeyError, ValueError, OSError) as exc:
        findings.append({"severity": "ERROR", "code": "BINDING_CHECK_ERROR", "error": str(exc)})

    # No substantive file may be empty. Empty .gitkeep files are explicitly
    # visible as completion blockers; they cannot masquerade as seeded content.
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        if path.stat().st_size == 0:
            findings.append({
                "severity": "BLOCKER" if path.name == ".gitkeep" else "ERROR",
                "code": "EMPTY_PLACEHOLDER" if path.name == ".gitkeep" else "EMPTY_SUBSTANTIVE_FILE",
                "artifact": rel,
            })

    # Required reference areas must contain actual non-empty evidence.
    for rel in REQUIRED_POPULATED_DIRS:
        files = substantive_files(root / rel)
        if not files:
            findings.append({
                "severity": "BLOCKER",
                "code": "REQUIRED_REFERENCE_AREA_EMPTY",
                "artifact": rel,
            })

    # Current/synthesized reference documents must be self-contained for Codex.
    for rel in PORTABLE_CURRENT_FILES:
        path = root / rel
        if not path.is_file():
            findings.append({"severity": "BLOCKER", "code": "CURRENT_REFERENCE_FILE_MISSING", "artifact": rel})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if EXTERNAL_STORAGE_URL.search(text):
            findings.append({
                "severity": "ERROR",
                "code": "EXTERNAL_STORAGE_DEPENDENCY",
                "artifact": rel,
            })

    errors = sum(f["severity"] == "ERROR" for f in findings)
    blockers = sum(f["severity"] == "BLOCKER" for f in findings)
    status = "FAIL" if errors else ("PASS_WITH_BLOCKERS" if blockers else "PASS")
    return {
        "status": status,
        "transferred_verified": checked,
        "errors": errors,
        "blockers": blockers,
        "completion_ready": errors == 0 and blockers == 0,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="Require zero integrity errors and zero completion blockers")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = validate(args.root)
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] or (args.strict and result["blockers"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
