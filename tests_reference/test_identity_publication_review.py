"""Bounded identity source publication checks; source bytes remain private."""
import json
import unittest
from scripts.validate_reference_seed import ROOT, validate


class IdentityPublicationReviewTests(unittest.TestCase):
    def test_identity_source_inventory_and_privacy_gate(self):
        doc=json.loads((ROOT/"governance/publication_reviews/IDENTITY_SOURCE_TRIAGE_20261120.json").read_text(encoding="utf-8"))
        records=doc["records"]
        self.assertEqual(len(records),8)
        self.assertEqual(doc["hash_matches"],8)
        self.assertEqual(doc["hash_mismatches"],0)
        self.assertEqual(doc["ast_parse_pass"],8)
        self.assertEqual(doc["tests_defined_not_executed"],24)
        self.assertFalse(doc["public_source_bytes_copied"])
        self.assertFalse(doc["explicit_p0_completion_credit"])
        self.assertFalse(doc["all_records_are_local"])
        self.assertEqual(len({r["original_relative_path"] for r in records}),8)
        self.assertEqual(sum(r["source_byte_count"] for r in records),138849)
        for r in records:
            with self.subTest(path=r["original_relative_path"]):
                self.assertEqual(len(r["source_sha256"]),64)
                int(r["source_sha256"],16)
                self.assertEqual(r["transfer_status"],"EXTERNALLY_VERIFIED_NOT_LOCAL")
                self.assertEqual(r["publication_review"],"BLOCKED_PENDING_HUMAN_AUTHORIZATION")
                self.assertIsNone(r["local_sha256"])
                self.assertIsNone(r["destination_path"])

    def test_identity_source_not_credited_as_local_completion(self):
        result=validate()
        self.assertFalse(result["completion_ready"])
        self.assertGreater(result["blockers"],0)
        self.assertFalse((ROOT/"source_reference/identity/query_identity.py").exists())


if __name__=="__main__":
    unittest.main()
