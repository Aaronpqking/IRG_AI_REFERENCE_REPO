"""Repository-local curated structural report checks; no historical qualification claim."""
import json
import unittest
from scripts.validate_reference_seed import ROOT, validate

class CuratedStructuralReport(unittest.TestCase):
    def test_scoped_local_curated_report(self):
        base=ROOT/"reports/reference/structural"
        doc=base/"STRUCTURAL_GATE3_LOSS_BOUNDARIES_20260813.md"
        registry=json.loads((base/"PROVENANCE.json").read_text(encoding="utf-8"))
        self.assertTrue(doc.is_file())
        txt=doc.read_text(encoding="utf-8")
        self.assertGreater(len(txt),1000)
        self.assertIn("LOCAL_CURATED_REPORT_SUMMARY",txt)
        self.assertFalse("https://drive.google.com/" in txt)
        self.assertEqual(registry["artifact_class"],"LOCAL_CURATED_REPORT_SUMMARY")
        self.assertEqual(registry["transfer_status"],"CURATED_NOT_EXACT_TRANSFER")
        self.assertFalse(registry["original_run_bundle_local"])
        self.assertIsNone(registry["source_sha256"])
        self.assertEqual(registry["destination_path"],"reports/reference/structural/STRUCTURAL_GATE3_LOSS_BOUNDARIES_20260813.md")
        self.assertFalse(validate()["completion_ready"])

if __name__ == "__main__":
    unittest.main()
