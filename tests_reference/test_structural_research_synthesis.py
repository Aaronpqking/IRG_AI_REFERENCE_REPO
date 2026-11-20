"""Check structural synthesis provenance and strict authority boundaries."""
import unittest
from scripts.validate_reference_seed import ROOT, validate

class StructuralResearchSynthesisTests(unittest.TestCase):
    def test_synthesis_has_source_and_negative_research_boundaries(self):
        p = ROOT / "research/structural/STRUCTURAL_RESEARCH_SUMMARY.md"
        text = p.read_text(encoding="utf-8")
        self.assertIn("HYBRID / SYNTHESIS", text)
        self.assertNotIn("https://drive.google.com/", text)
        for phrase in [
            "V1 / V1.5", "Docling", "parent/child", "procedure",
            "canonical", "RRF", "cross-encoder", "TABLE",
            "17 valid unseen", "10,868", "3/17", "5/17",
            "16/40", "13/40", "3/10", "0/10",
            "HISTORY_REPORTED_UNVERIFIED", "INVALID",
            "UNKNOWN", "IRG-X001", "NOT_EXECUTED",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertIn("source_reference/structural/TRANSFER_MANIFEST.json", text)
        self.assertIn("V1_9_33_INVALID_ABLATION_REPORT.md", text)
        self.assertIn("V1_9_35_SINGLE_RETRIEVAL_FORKED_PATH_ABLATION_REPORT.md", text)

    def test_synthesis_preserves_strict_blockers(self):
        result = validate()
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["blockers"], 3)
        self.assertFalse(result["completion_ready"])
        self.assertEqual(
            sorted(f["code"] for f in result["findings"] if f["severity"] == "BLOCKER"),
            sorted(["PRIVATE_SOURCE_NOT_IN_REPO", "PRIVATE_SOURCE_NOT_IN_REPO",
                    "MASTER_MANIFEST_REVISION_CONFLICT"]),
        )

if __name__ == "__main__":
    unittest.main()
