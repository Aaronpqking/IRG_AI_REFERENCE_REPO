#!/usr/bin/env python3
"""Read-only reference completion census and strict-gate diagnostic."""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.validate_reference_seed import ROOT, REQUIRED_POPULATED_DIRS, substantive_files, validate

def audit(root: Path=ROOT)->dict:
    paths=[p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]
    substantive=[p for p in paths if p.stat().st_size>0]
    placeholders=[p.relative_to(root).as_posix() for p in paths if p.name==".gitkeep"]
    manifests=list((root/"source_reference").rglob("TRANSFER_MANIFEST.json"))
    manifests+=list((root/"tests_reference/historical").rglob("TRANSFER_MANIFEST.json"))
    transfers=[]
    for m in manifests:
        obj=json.loads(m.read_text(encoding="utf-8"))
        for rec in obj["records"]:
            p=root/rec["destination_path"]
            raw=p.read_bytes()
            if len(raw)!=rec["source_byte_count"] or hashlib.sha256(raw).hexdigest()!=rec["source_sha256"]:
                raise RuntimeError("EXACT_TRANSFER_INTEGRITY_FAILURE "+rec["destination_path"])
            transfers.append(rec)
    identity=json.loads((root/"governance/publication_reviews/IDENTITY_SOURCE_TRIAGE_20261120.json").read_text(encoding="utf-8"))
    for rec in identity["records"]:
        p=root/rec["destination_path"]
        raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=rec["source_sha256"] or len(raw)!=rec["source_byte_count"]:
            raise RuntimeError("IDENTITY_TRANSFER_FAILURE "+rec["destination_path"])
        transfers.append(rec)
    v=validate(root)
    return {
        "substantive_file_count":len(substantive),
        "zero_byte_file_count":len(paths)-len(substantive),
        "placeholder_count":len(placeholders),
        "placeholders":placeholders,
        "required_area_counts":{x:len(substantive_files(root/x)) for x in REQUIRED_POPULATED_DIRS},
        "exact_source_test_count":len(transfers),
        "exact_source_test_bytes":sum(r["source_byte_count"] for r in transfers),
        "exact_source_modules":sum(r["artifact_class"] in ("HISTORICAL_IMPLEMENTATION","HISTORICAL_STRUCTURAL_MILESTONE","HISTORICAL_IMPLEMENTATION_SOURCE") for r in transfers),
        "exact_historical_tests":sum(r["artifact_class"] in ("HISTORICAL_BEHAVIOR_TEST","BEHAVIOR_DEFINING_TEST") for r in transfers),
        "validator":{k:v[k] for k in ("status","errors","blockers","completion_ready")},
        "blocker_codes":[x["code"] for x in v["findings"] if x["severity"]=="BLOCKER"],
    }

if __name__=="__main__":
    x=audit()
    run=subprocess.run([sys.executable,str(ROOT/"scripts/validate_reference_seed.py"),"--strict"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    x["strict_return_code"]=run.returncode
    x["strict_passed"]=run.returncode==0
    print(json.dumps(x,indent=2,sort_keys=True))
