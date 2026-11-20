"""Postapproval P0 content accounting: local files versus qualified run claims."""
import hashlib
import json
import unittest
from scripts.validate_reference_seed import ROOT, validate


class ApprovedEvidenceInventoryTests(unittest.TestCase):
    def test_approved_identity_exact_transfer(self):
        inventory=json.loads((ROOT/"governance/publication_reviews/IDENTITY_SOURCE_TRIAGE_20261120.json").read_text(encoding="utf-8"))
        self.assertEqual(len(inventory["records"]),8)
        self.assertEqual(sum(x["source_byte_count"] for x in inventory["records"]),138849)
        for row in inventory["records"]:
            local=ROOT/row["destination_path"]
            self.assertEqual(local.stat().st_size,row["source_byte_count"])
            self.assertEqual(hashlib.sha256(local.read_bytes()).hexdigest(),row["source_sha256"])
            self.assertEqual(row["transfer_status"],"LOCAL_EXACT_TRANSFER_VERIFIED")

    def test_curated_reports_are_local_but_not_exact_originals(self):
        paths=[
            "reports/reference/v1",
            "reports/reference/v1_5",
            "reports/reference/corpus",
            "reports/reference/structural",
            "research/structural",
        ]
        for rel in paths:
            with self.subTest(directory=rel):
                directory=ROOT/rel
                self.assertTrue(directory.is_dir())
                self.assertFalse((directory/".gitkeep").exists())
                provenance=json.loads((directory/"PROVENANCE.json").read_text(encoding="utf-8"))
                self.assertEqual(provenance["artifact_class"],"LOCAL_CURATED_REPORT_SUMMARY")
                self.assertEqual(provenance["transfer_status"],"CURATED_NOT_EXACT_TRANSFER")
                self.assertIsNone(provenance["source_sha256"])
                self.assertFalse(provenance["original_run_bundle_local"])
                self.assertTrue((ROOT/provenance["destination_path"]).is_file())

    def test_reference_still_not_fully_qualified(self):
        self.assertFalse((ROOT/"source_reference/identity/.gitkeep").exists())
        status=validate()
        self.assertEqual(status["errors"],0)
        self.assertGreater(status["blockers"],0)
        self.assertFalse(status["completion_ready"])


if __name__=="__main__":
    unittest.main()
