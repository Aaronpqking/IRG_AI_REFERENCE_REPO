"""Original archived behavior tests: verify syntax and immutable byte identities.

These archived test modules are NOT run against a reconstructed historical
runtime by this suite. They are source/evidence transfers only.
"""
import ast
import hashlib
import json
import unittest
from scripts.validate_reference_seed import ROOT


class HistoricalBehaviorArchiveTests(unittest.TestCase):
    def test_exact_archival_transfers(self):
        manifest=ROOT/"tests_reference/historical/behavior/TRANSFER_MANIFEST.json"
        payload=json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(payload["execution_status"],"NOT_EXECUTED_IN_THIS_PASS")
        self.assertEqual(len(payload["records"]),10)
        self.assertEqual(sum(x["source_byte_count"] for x in payload["records"]),121917)
        for x in payload["records"]:
            with self.subTest(test=x["artifact_name"]):
                p=ROOT/x["destination_path"]
                b=p.read_bytes()
                self.assertEqual(len(b),x["source_byte_count"])
                self.assertEqual(hashlib.sha256(b).hexdigest(),x["source_sha256"])
                self.assertEqual(x["source_sha256"],x["local_sha256"])
                self.assertEqual(x["transfer_status"],"LOCAL_EXACT_TRANSFER_VERIFIED")
                ast.parse(b.decode("utf-8"),filename=str(p))


if __name__=="__main__":
    unittest.main()
