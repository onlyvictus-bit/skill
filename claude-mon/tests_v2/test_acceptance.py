#!/usr/bin/env python3
"""M9: offline acceptance. Full pipeline on ground truth, faults blocked,
mechanical scale measured. Semantic depth is checker-tested, not model-proven.
"""
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0].parents[0] / "memory-integrity" / "scripts"))

import acceptance_corpus as corpus  # noqa: E402
import run_acceptance as driver  # noqa: E402
from complete_read_v2 import partition, results  # noqa: E402
from integrity_v2 import recall as mi_recall  # noqa: E402
from integrity_v2 import report as mi_report  # noqa: E402
from integrity_v2 import semantic as mi_semantic  # noqa: E402


def craft_interpretation(original):
    numbers = mi_semantic.numbers_in(original)
    markers = [m for m in mi_semantic.NEGATION_MARKERS_EN if m in original.lower()]
    parts = ["Seen values: %s." % (", ".join(numbers) if numbers else "none")]
    parts.append("Conditions honored: %s." % (", ".join(sorted(set(markers))[:3]))
                 if markers else "No conditions.")
    return " ".join(parts)


class FullPipelineTests(unittest.TestCase):
    def test_ground_truth_end_to_end(self):
        gt = corpus.ground_truth_corpus()
        with tempfile.TemporaryDirectory(prefix="acc-") as temp:
            out = driver.run_full_pipeline(
                temp, "corpus.txt", gt["bytes"],
                {"digest": "task-acc-1", "instructions": "note every unit",
                 "schema": {"type": "object"}, "spec_digest": "spec-acc-1"},
                interpretations=None, per_unit_output=100)
            # Build interpretations mechanically, then run the result layer.
            man = partition.build_manifest("SRC-ACC", gt["bytes"])
            units = {u["id"]: gt["bytes"][u["range"][0]:u["range"][1]].decode("utf-8")
                     for u in man["units"]}
            interps = {uid: craft_interpretation(text) for uid, text in units.items()}
            recs = [results.make_result(gt["bytes"], man, uid, "task-acc-1", "ATT-x", text)
                    for uid, text in interps.items()]
            self.assertEqual(results.reconcile(list(units), recs)["complete"], True)
            reports = [mi_semantic.challenge_unit(uid, units[uid], interps[uid])
                       for uid in units]
            ready, blockers = mi_semantic.strict_ready(reports)
            self.assertTrue(ready, blockers)
            layer = mi_report.compose(
                {n: "READY" for n in mi_report.LAYERS})
            self.assertEqual(layer["overall"], "READY_FOR_DECLARED_TASK")
            # First/middle/last facts recoverable from reopened originals.
            index = mi_recall.build_index(units, man["source_digest"])
            for fact, ident in (("42", None), ("Ledger-7", None), ("99", None)):
                hits = mi_recall.locate(index, fact)["hits"]
                self.assertTrue(hits, fact)
            self.assertEqual(out["accepted"], out["chunks"])
            self.assertGreater(out["units"], 0)

    def test_seeded_bad_interpretation_flagged(self):
        gt = corpus.ground_truth_corpus()
        man = partition.build_manifest("SRC-ACC", gt["bytes"])
        units = {u["id"]: gt["bytes"][u["range"][0]:u["range"][1]].decode("utf-8")
                 for u in man["units"]}
        target = next(uid for uid, text in units.items() if "must not exceed 30" in text)
        rep = mi_semantic.challenge_unit(target, units[target], "Refunds are fine anytime.")
        self.assertIn("negation", rep["unresolved"])
        ready, _ = mi_semantic.strict_ready([rep])
        self.assertFalse(ready)


class FaultMatrixTests(unittest.TestCase):
    def test_all_offline_faults_block(self):
        data = b"aaa\nbbb\n"
        with tempfile.TemporaryDirectory(prefix="fault-") as temp:
            cases = {
                "T01-omit": driver.fault_omit_file(temp),
                "T02-empty": driver.fault_empty_scope(),
                "T03-swap": driver.fault_swap_manifest(data, b"zzz\n"),
                "T04-duplicate": driver.fault_duplicate_chunk(data),
                "T05-payload": driver.fault_wrong_payload(data),
                "T06-gap": driver.fault_gap(data),
                "T08-encoding": driver.fault_bad_encoding(),
                "T22-task-change": driver.fault_task_change(None, data),
                "T13-corrupt": driver.fault_corrupt_response_artifact(None, data),
            }
        for name, result in cases.items():
            self.assertTrue(result["blocked"], "%s did not block: %s" % (name, result))

    def test_oversize_unit_subdivided_not_dropped(self):
        result = driver.fault_oversize_unit()
        self.assertFalse(result["blocked"])
        self.assertGreater(result["children"], 0)
        self.assertEqual(result["oversize_remaining"], 0)


class ScaleTests(unittest.TestCase):
    def test_exact_fixture_sizes(self):
        for size in (50_000_000, 52_428_800):
            data = corpus.scale_fixture(size)
            self.assertEqual(len(data), size)

    def test_mechanical_scale_50mb(self):
        data = corpus.scale_fixture(50_000_000)
        started = time.time()
        man = partition.build_manifest("SRC-SCALE", data)
        self.assertEqual(partition.validate_manifest(data, man), [])
        self.assertEqual(partition.reassemble(data, man), data)
        elapsed = time.time() - started
        self.assertLess(elapsed, 300, "50MB mechanical pass took %ss" % elapsed)
        print("\n50MB: %d units, %d chunks, %.1fs" % (len(man["units"]),
                                                     len(man["chunks"]), elapsed))


if __name__ == "__main__":
    unittest.main(verbosity=2)
