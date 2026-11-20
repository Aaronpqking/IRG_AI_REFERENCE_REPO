"""Report-seeding integrity does not imply original-run reproducibility."""
import json
import unittest
from scripts.validate_reference_seed import ROOT, validate


class CuratedHistoricalReportTests(unittest.TestCase):
    def test_five_reports_are_substantive_and_classified(self):
        ledger=json.loads((ROOT/"reports/reference/CURATED_REPORT_TRANSFER_REGISTER.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["classification"],"LOCAL_CURATED_REPORT_SUMMARY")
        self.assertFalse(ledger["original_transfer_claim"])
        self.assertEqual(ledger["publication_approval_status"],"REVIEW_REQUIRED")
        self.assertEqual(len(ledger["records"]),5)
        for record in ledger["records"]:
            with self.subTest(record=record["path"]):
                p=ROOT/record["path"]
                self.assertTrue(p.is_file())
                text=p.read_text(encoding="utf-8")
                self.assertGreater(len(text),500)
                self.assertIn("LOCAL_CURATED_REPORT_SUMMARY",text)
                self.assertEqual(record["sha256_original"],None)
                self.assertEqual(record["empirical_run_status"],"HISTORICAL_REPORT_NOT_REEXECUTED")
                self.assertNotIn("https://drive.google.com/",text)
                self.assertNotIn("https://docs.google.com/",text)

    def test_strict_completion_still_blocked(self):
        result=validate()
        self.assertFalse(result["completion_ready"])
        self.assertGreater(result["blockers"],0)
        self.assertIn(result["status"],("PASS_WITH_BLOCKERS","FAIL"))


if __name__=="__main__":
    unittest.main()
