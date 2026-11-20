"""P0 exception accounting; preserves hard blockers rather than lowering the gate."""
import unittest
from scripts.validate_reference_seed import validate, ROOT, REQUIRED_POPULATED_DIRS, substantive_files

ALLOWED_OPEN_CODES={"PRIVATE_SOURCE_NOT_IN_REPO","MASTER_MANIFEST_REVISION_CONFLICT"}

class FinalReferenceEvidenceAccounting(unittest.TestCase):
    def test_required_areas_nonempty(self):
        for rel in REQUIRED_POPULATED_DIRS:
            with self.subTest(rel=rel):
                self.assertTrue(substantive_files(ROOT/rel),rel)

    def test_all_remaining_blockers_are_explicit(self):
        r=validate()
        self.assertEqual(r["errors"],0)
        self.assertEqual(r["status"],"PASS_WITH_BLOCKERS")
        self.assertFalse(r["completion_ready"])
        findings=[x for x in r["findings"] if x["severity"]=="BLOCKER"]
        self.assertEqual(len(findings),3)
        self.assertEqual(sum(x["code"]=="PRIVATE_SOURCE_NOT_IN_REPO" for x in findings),2)
        self.assertEqual(sum(x["code"]=="MASTER_MANIFEST_REVISION_CONFLICT" for x in findings),1)
        self.assertEqual({x["code"] for x in findings},ALLOWED_OPEN_CODES)

if __name__=="__main__":
    unittest.main()
