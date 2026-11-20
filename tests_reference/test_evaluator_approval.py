"""Reconcile owner-approved evaluator byte identities; no private source disclosure."""
import hashlib
import json
import unittest
from scripts.validate_reference_seed import ROOT


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha256_file(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


class EvaluatorApprovalBindingTests(unittest.TestCase):
    def test_owner_approval_is_explicit_and_does_not_authorize_qualification(self):
        approval = read_json("evaluation/frozen/V2_EVALUATOR_APPROVAL_v1.json")
        manifest = read_json("evaluation/frozen/V2_EVALUATOR_MANIFEST_v1.json")
        self.assertEqual(approval["approval"]["approval_status"], "AUTHORITATIVE_FROZEN")
        self.assertEqual(approval["approved_artifact"]["manifest_sha256"],
                         sha256_file("evaluation/frozen/V2_EVALUATOR_MANIFEST_v1.json"))
        self.assertEqual(approval["approved_artifact"]["manifest_sha256"], manifest["file_sha256"] if "file_sha256" in manifest else sha256_file("evaluation/frozen/V2_EVALUATOR_MANIFEST_v1.json"))
        self.assertFalse(approval["authorization_limits"]["qualification_execution_authorized"])
        self.assertEqual(approval["post_approval_state"]["qualification"], "NOT_EXECUTED")

    def test_transferred_frozen_metadata_and_private_hash_boundaries(self):
        ledger = read_json("evaluation/EVALUATOR_PROVENANCE_LEDGER.json")
        manifest = read_json("evaluation/frozen/V2_EVALUATOR_MANIFEST_v1.json")
        self.assertEqual(ledger["source_code_status"], "10_OF_10_MATCH_FROZEN_MANIFEST")
        expected_sources = dict(manifest["source_hashes"])
        expected_sources.update(manifest["test_source_hashes"])
        self.assertEqual(len(expected_sources), 10)
        self.assertEqual({r["path"]: r["sha256"] for r in ledger["source_and_test_files"]}, expected_sources)
        self.assertTrue(all(r["visibility"] == "PRIVATE_DRIVE_NOT_COPIED_TO_PUBLIC_REPO"
                            for r in ledger["source_and_test_files"]))
        for artifact in ledger["frozen_metadata_files"]:
            with self.subTest(path=artifact["path"]):
                self.assertEqual(sha256_file(artifact["path"]), artifact["sha256"])
        self.assertEqual(ledger["withheld_artifact"]["sha256"],
                         manifest["derived_population_manifest"]["file_sha256"])
        self.assertEqual(ledger["approval"]["qualification"], "NOT_EXECUTED")
        self.assertFalse(ledger["approval"]["qualification_execution_authorized"])
        self.assertEqual(ledger["open_exception"], "IRG-X001_MASTER_MANIFEST_HASH_UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
