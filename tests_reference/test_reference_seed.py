"""Offline structural and integrity smoke tests for the public reference seed."""
import json
import unittest

from scripts.validate_reference_seed import ROOT, validate


class ReferenceSeedTests(unittest.TestCase):
    def test_reference_contracts_are_hash_clean(self):
        report = validate(ROOT)
        self.assertEqual(report["errors"], 0, report)
        self.assertGreaterEqual(report["transferred_verified"], 10)

    def test_unresolved_private_evidence_is_not_silently_qualified(self):
        report = validate(ROOT)
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("PRIVATE_SOURCE_NOT_IN_REPO", codes)
        self.assertIn("MASTER_MANIFEST_REVISION_CONFLICT", codes)
        self.assertEqual(report["status"], "PASS_WITH_BLOCKERS")

    def test_claims_unique_and_valid_jsonl(self):
        rows = [json.loads(line) for line in (ROOT / "CLAIM_REGISTER.jsonl").read_text().splitlines() if line.strip()]
        ids = [r["claim_id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 8)
        self.assertTrue(all(r["status"] and r["supporting_artifact"] for r in rows))


if __name__ == "__main__":
    unittest.main()
