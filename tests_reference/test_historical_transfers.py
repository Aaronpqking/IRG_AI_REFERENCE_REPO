"""Verify historical ADR/lessons transfers remain identical to source snapshots."""
import hashlib
import json
import unittest

from scripts.validate_reference_seed import ROOT


class HistoricalTransferTests(unittest.TestCase):
    def test_original_adr_and_lessons_hashes(self):
        ledger = json.loads((ROOT / "decisions/HISTORICAL_TRANSFER_LEDGER.json").read_text())
        records = ledger["records"]
        self.assertEqual(len(records), 21)
        self.assertEqual(sum("/ADR-" in r["path"] for r in records), 19)
        for record in records:
            with self.subTest(path=record["path"]):
                path = ROOT / record["path"]
                self.assertTrue(path.is_file())
                data = path.read_bytes()
                self.assertEqual(len(data), record["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])


if __name__ == "__main__":
    unittest.main()
