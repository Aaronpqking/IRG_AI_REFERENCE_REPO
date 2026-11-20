#!/usr/bin/env python3
"""Offline read-only validation of the IRG AI reference seed.

No network, imports from production, corpus writes or index mutation.
Run: python scripts/validate_reference_seed.py [--strict]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path = ROOT) -> dict:
    findings = []
    ledger_path = root / "evaluation" / "FROZEN_TRANSFER_LEDGER.json"
    if not ledger_path.is_file():
        return {"status": "FAIL", "findings": [{"severity": "ERROR", "code": "LEDGER_MISSING"}]}
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    checked = 0
    for record in ledger["records"]:
        path_name = record.get("repo_path")
        if record["status"] == "VERIFIED_DRIVE_PRIVATE_WITHHELD":
            findings.append({"severity": "BLOCKER", "code": "PRIVATE_SOURCE_NOT_IN_REPO", "artifact": record["name"]})
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
                findings.append({"severity": "ERROR", "code": "INVALID_JSON", "artifact": path_name, "error": str(exc)})
                continue
        checked += 1

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
            findings.append({"severity": "BLOCKER", "code": "MASTER_MANIFEST_REVISION_CONFLICT",
                             "expected": evaluator["authority"]["master_manifest_sha256"],
                             "observed": digest(frozen / "V2_MASTER_REGRESSION_MANIFEST_v1.json")})
        if evaluator.get("qualification_status") != "NOT_EXECUTED":
            findings.append({"severity": "BLOCKER", "code": "EVALUATOR_QUALIFICATION_STATUS_CHANGED_REVIEW"})
    except (KeyError, ValueError, OSError) as exc:
        findings.append({"severity": "ERROR", "code": "BINDING_CHECK_ERROR", "error": str(exc)})

    errors = sum(f["severity"] == "ERROR" for f in findings)
    blockers = sum(f["severity"] == "BLOCKER" for f in findings)
    return {"status": "FAIL" if errors else ("PASS_WITH_BLOCKERS" if blockers else "PASS"),
            "transferred_verified": checked, "errors": errors, "blockers": blockers, "findings": findings}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--strict", action="store_true", help="Require no pending qualification blockers")
    p.add_argument("--root", type=Path, default=ROOT)
    args = p.parse_args()
    result = validate(args.root)
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] or (args.strict and result["blockers"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
