"""P0 portability gates: external archives are optional origin metadata only."""
import unittest

from scripts.validate_reference_seed import (
    ROOT, PORTABLE_CURRENT_FILES, REQUIRED_POPULATED_DIRS, EXTERNAL_STORAGE_URL, validate
)


class ReferencePortabilityTests(unittest.TestCase):
    def test_extended_current_documents_have_no_drive_dependency(self):
        paths = {
            "governance/REFERENCE_PORTABILITY_POLICY.md",
            "reports/reference/audits/GOOGLE_DRIVE_SOURCE_BINDING_20261120.md",
            "evaluation/EVALUATOR_APPROVAL_RECONCILIATION_20261120.md",
            "evaluation/IRG_X001_MANIFEST_LINEAGE_20261120.md",
            "evaluation/EVALUATOR_ISOLATED_OFFLINE_REPLAY_20261120.md",
        }
        self.assertTrue(paths.issubset(set(PORTABLE_CURRENT_FILES)))
        for rel in paths:
            with self.subTest(path=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                self.assertNotRegex(text, EXTERNAL_STORAGE_URL)

    def test_private_source_hashes_do_not_complete_local_reference_seed(self):
        self.assertIn("source_reference/retrieval", REQUIRED_POPULATED_DIRS)
        self.assertIn("source_snapshot", REQUIRED_POPULATED_DIRS)
        result = validate()
        self.assertGreater(result["blockers"], 0)
        self.assertFalse(result["completion_ready"])
        self.assertTrue(any(f["code"] == "PRIVATE_SOURCE_NOT_IN_REPO"
                            for f in result["findings"]))
        self.assertTrue(any(f["code"] == "MASTER_MANIFEST_REVISION_CONFLICT"
                            for f in result["findings"]))


if __name__ == "__main__":
    unittest.main()
