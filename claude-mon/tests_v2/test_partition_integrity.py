#!/usr/bin/env python3
"""M1: partitions are exact; every reproduced mismatch blocks."""
import copy
import sys
import unittest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import partition  # noqa: E402

CORPUS = ("first line\nsecond — ünïcödé line\nCRLF line\r\nlast without newline"
          ).encode("utf-8")


def manifest(data=CORPUS, **kwargs):
    return partition.build_manifest("SRC-1", data, **kwargs)


class PartitionTests(unittest.TestCase):
    def test_valid_corpus_reassembles_exactly(self):
        man = manifest()
        self.assertEqual(partition.validate_manifest(CORPUS, man), [])
        self.assertEqual(partition.reassemble(CORPUS, man), CORPUS)

    def test_swapped_manifest_binding_mismatch(self):
        other = manifest(b"different bytes\n")
        errors = partition.validate_manifest(CORPUS, other)
        self.assertTrue(any("E_SOURCE_BINDING_MISMATCH" in e for e in errors), errors)

    def test_duplicate_chunk_id_blocked(self):
        man = manifest()
        man["chunks"].append(dict(man["chunks"][0]))
        errors = partition.validate_manifest(CORPUS, man)
        self.assertTrue(any("E_ID_DUPLICATE" in e for e in errors), errors)

    def test_wrong_payload_hash_blocked(self):
        man = manifest()
        man["chunks"][0]["payload_sha256"] = "0" * 64
        errors = partition.validate_manifest(CORPUS, man)
        self.assertTrue(any("E_PAYLOAD_MISMATCH" in e for e in errors), errors)

    def test_gap_blocked(self):
        man = manifest()
        victim = man["units"][1]
        man["units"] = [u for u in man["units"] if u["id"] != victim["id"]]
        for chunk in man["chunks"]:
            chunk["primary"] = [p for p in chunk["primary"] if p != victim["id"]]
        errors = partition.validate_manifest(CORPUS, man)
        self.assertTrue(any("GAP" in e for e in errors), errors)

    def test_overlap_blocked(self):
        man = manifest()
        man["units"][1]["range"][0] = man["units"][0]["range"][0]
        errors = partition.validate_manifest(CORPUS, man)
        self.assertTrue(any("OVERLAP" in e or "ORDER" in e or "HASH" in e for e in errors), errors)

    def test_reordered_units_blocked(self):
        man = manifest()
        man["units"] = list(reversed(man["units"]))
        errors = partition.validate_manifest(CORPUS, man)
        self.assertTrue(errors, "reversed units must not validate")

    def test_oversized_line_subdivided_with_lineage(self):
        data = b"short\n" + b"x" * 300 + b"\nend\n"
        man = manifest(data, max_unit_bytes=100)
        self.assertEqual(partition.validate_manifest(data, man), [])
        self.assertEqual(partition.reassemble(data, man), data)
        children = [u for u in man["units"] if u["parent"] is not None]
        self.assertTrue(children, "oversized line must subdivide")
        for child in children:
            self.assertLessEqual(child["range"][1] - child["range"][0], 100)

    def test_context_never_counts_as_primary(self):
        man = manifest()
        primaries = [p for c in man["chunks"] for p in c["primary"]]
        self.assertEqual(sorted(primaries), sorted(u["id"] for u in man["units"]))
        for chunk in man["chunks"]:
            for ctx in chunk["context_before"] + chunk["context_after"]:
                self.assertIn(ctx, primaries, "context must also exist as primary elsewhere")

    def test_invalid_utf8_rejected(self):
        with self.assertRaises(partition.ContractError):
            partition.unitize(b"\xff\xfe invalid \x80")

    def test_empty_source_valid_empty_manifest(self):
        man = manifest(b"")
        self.assertEqual(man["units"], [])
        self.assertEqual(partition.validate_manifest(b"", man), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
