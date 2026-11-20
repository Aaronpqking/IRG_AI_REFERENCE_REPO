"""Verify exact historical source copies without importing runtime dependencies."""
import hashlib
import json
from pathlib import Path
import unittest
from scripts.validate_reference_seed import ROOT, validate

class OriginalReferenceTransfers(unittest.TestCase):
    def test_all_present_transfer_manifests(self):
        total=0
        for manifest in sorted((ROOT/"source_reference").rglob("TRANSFER_MANIFEST.json")):
            payload=json.loads(manifest.read_text(encoding="utf-8"))
            for record in payload["records"]:
                with self.subTest(file=record["destination_path"]):
                    original=ROOT/record["destination_path"]
                    self.assertTrue(original.is_file(),original)
                    raw=original.read_bytes()
                    self.assertEqual(len(raw),record["source_byte_count"])
                    self.assertEqual(hashlib.sha256(raw).hexdigest(),record["source_sha256"])
                    self.assertEqual(record["local_sha256"],record["source_sha256"])
                    self.assertEqual(record["transfer_status"],"LOCAL_EXACT_TRANSFER_VERIFIED")
                    self.assertIn(record["original_git_revision"],("UNKNOWN","UNBOUND"))
                    total+=1
        self.assertGreaterEqual(total,6)

    def test_still_not_full_p0(self):
        result=validate()
        self.assertEqual(result["errors"],0)
        self.assertFalse(result["completion_ready"])

if __name__=="__main__":
    unittest.main()
