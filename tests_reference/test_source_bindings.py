"""Validate public source-binding metadata without requiring private source bytes."""
import json
import re
import unittest

from scripts.validate_reference_seed import ROOT


class DriveSourceBindingTests(unittest.TestCase):
    def test_selected_files_are_real_hash_references_not_promoted_git_commits(self):
        path = ROOT / "source_reference" / "SOURCE_BINDINGS_20261120.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["source_status"], "SELECTED_DIRECT_FILES_HASHED_UNBOUND_TO_GIT_REVISION")
        self.assertEqual(len(payload["records"]), 11)
        paths, ids = set(), set()
        for record in payload["records"]:
            with self.subTest(record=record["path"]):
                self.assertNotIn(record["path"], paths)
                self.assertNotIn(record["drive_file_id"], ids)
                paths.add(record["path"])
                ids.add(record["drive_file_id"])
                self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(record["bytes"], 0)
                self.assertIsNone(record["git_commit_binding"])
                self.assertEqual(record["sensitive_class"], "INTERNAL_IMPLEMENTATION")
                self.assertTrue(record["path"].startswith(("src/", "tests/")))
        self.assertEqual(sum(s.startswith("src/") for s in paths), 7)
        self.assertEqual(sum(s.startswith("tests/") for s in paths), 4)

    def test_manifest_lineage_exception_remains_explicit(self):
        findings = (ROOT / "evaluation" / "IRG_X001_MANIFEST_LINEAGE_20261120.md").read_text()
        data = json.loads((ROOT / "evaluation" / "FROZEN_TRANSFER_LEDGER.json").read_text())
        x = data["integrity_exception"]
        self.assertEqual(x["id"], "IRG-X001")
        self.assertEqual(x["resolution"], "UNRESOLVED_REQUIRES_VERSION_RECONCILIATION")
        self.assertIn(x["actual_master_manifest_sha256"], findings)
        self.assertIn(x["master_manifest_sha256_bound_in_evaluator"], findings)


if __name__ == "__main__":
    unittest.main()
