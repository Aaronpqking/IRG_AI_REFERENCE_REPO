"""Independent SHA-256 checks for approved, exact historical identity transfers."""
import hashlib
import json
import unittest
from scripts.validate_reference_seed import ROOT, validate


class IdentitySourceTransferTests(unittest.TestCase):
    def test_eight_exact_original_sources_and_tests(self):
        doc=json.loads((ROOT/"governance/publication_reviews/IDENTITY_SOURCE_TRIAGE_20261120.json").read_text(encoding="utf-8"))
        records=doc["records"]
        self.assertEqual(len(records),8)
        self.assertEqual(doc["hash_matches"],8)
        self.assertEqual(doc["hash_comparisons_performed"],8)
        self.assertEqual(doc["hashes_computed_from_original_bytes"],8)
        self.assertEqual(doc["hash_mismatches"],0)
        self.assertEqual(doc["ast_parse_pass"],8)
        self.assertEqual(doc["tests_defined_not_executed"],24)
        self.assertTrue(doc["public_source_bytes_copied"])
        self.assertFalse(doc["explicit_p0_completion_credit"])
        self.assertTrue(doc["all_records_are_local"])
        self.assertEqual(len({r["original_relative_path"] for r in records}),8)
        self.assertEqual(sum(r["source_byte_count"] for r in records),138849)
        for r in records:
            with self.subTest(path=r["original_relative_path"]):
                local=ROOT/r["destination_path"]
                self.assertTrue(local.is_file())
                data=local.read_bytes()
                self.assertEqual(len(data),r["source_byte_count"])
                self.assertEqual(hashlib.sha256(data).hexdigest(),r["source_sha256"])
                self.assertEqual(r["local_sha256"],r["source_sha256"])
                self.assertEqual(r["local_byte_count"],r["source_byte_count"])
                self.assertEqual(r["transfer_status"],"LOCAL_EXACT_TRANSFER_VERIFIED")
                self.assertEqual(r["publication_review"],"USER_APPROVED_2026_11_20_SECURITY_SCREENED")
                self.assertEqual(r["redaction_status"],"NONE")

    def test_other_p0_gates_still_blocked(self):
        result=validate()
        self.assertFalse(result["completion_ready"])
        self.assertGreater(result["blockers"],0)


if __name__=="__main__":
    unittest.main()
