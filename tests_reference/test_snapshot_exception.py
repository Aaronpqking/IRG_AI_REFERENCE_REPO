"""A snapshot exception must be substantive and explicitly non-executable."""
import unittest
from scripts.validate_reference_seed import ROOT, validate

class SnapshotExceptionTests(unittest.TestCase):
    def test_explicit_unavailability(self):
        doc=ROOT/"source_snapshot/SNAPSHOT_MANIFEST.md"
        content=doc.read_text(encoding="utf-8")
        self.assertIn("BLOCKED_COHERENT_CHECKOUT_UNAVAILABLE",content)
        self.assertIn("original_git_revision: UNKNOWN",content)
        self.assertIn("NOT_A_RUNTIME_SOURCE_OF_TRUTH",content)
        self.assertFalse((doc.parent/".gitkeep").exists())
        self.assertGreater(len(content),1000)

    def test_unavailability_cannot_qualify_p0(self):
        self.assertFalse(validate()["completion_ready"])

if __name__=="__main__":
    unittest.main()
