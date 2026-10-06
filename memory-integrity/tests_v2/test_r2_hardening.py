#!/usr/bin/env python3
"""R2 negative gates: a label or digest string is never a proof artifact."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2 import extraction, recall, report, semantic, watchdog  # noqa: E402


class TestR2FalseProofs(unittest.TestCase):
    def test_mixed_malformed_watchdog_hits_are_blind(self):
        class Bad:
            deleted = False
            def remember(self, text): self.text = text; return {"id":"i", "text":text}
            def search(self, text): return {"hits":[{}] if self.deleted else [{"id":"i","text":text},{}]}
            def fetch(self, ident): return None if self.deleted else {"id":"i","text":self.text}
            def delete(self, ident): self.deleted=True; return {"deleted":True}
        self.assertEqual(watchdog.strict_roundtrip(Bad(), "s", "x")["verdict"], "BLIND")

    def test_service_restart_declarations_are_not_observation(self):
        self.assertEqual(watchdog.boundary_verdict("service_restart", {
            "generation_before":1,"generation_after":2,"same_data_identity":True}), "BOUNDARY_UNVERIFIED")
    def test_invented_digest_strings_do_not_authorize_ready(self):
        layers = {name: "READY" for name in report.LAYERS}
        out = report.compose_verified(layers, evidence={name: ["a" * 64]
                                                        for name in report.LAYERS})
        self.assertEqual(out["overall"], "BLOCKED")

    def test_empty_inventory_counts_are_not_ready(self):
        event = {"schema_version": 2, "source_digest": "a", "canonical_digest": "a",
                 "extractor": "fixture", "extractor_version": "1", "config_digest": "c",
                 "expected_inventory": {}, "produced_elements": {}, "diagnostics": [],
                 "state": "INVENTORY_CHECKED"}
        with self.assertRaises(extraction.ExtractionError):
            extraction.validate_event(event)

    def test_error_diagnostic_rejects_even_positive_counts(self):
        event = {"schema_version": 2, "source_digest": "a", "canonical_digest": "b",
                 "extractor": "fixture", "extractor_version": "1", "config_digest": "c",
                 "expected_inventory": {"pages": 1}, "produced_elements": {"pages": 1},
                 "diagnostics": ["ERROR: parser warning"], "state": "INVENTORY_CHECKED"}
        with self.assertRaises(extraction.ExtractionError):
            extraction.validate_event(event)

    def test_semantic_requires_exact_expected_set_and_bindings(self):
        reviews = [{"unit_id": "U1", "reviewer": "r", "findings": [], "unresolved": [],
                    "source_digest": "s", "task_digest": "t"}]
        ready, blockers = semantic.strict_ready(reviews, expected_ids=["U1", "U2"],
                                                source_digest="s", task_digest="t")
        self.assertFalse(ready)
        self.assertTrue(blockers)

    def test_empty_watchdog_hit_map_is_blind(self):
        class Bad:
            def remember(self, text): return {"id": "i", "text": text}
            def search(self, text): return {}
            def fetch(self, ident): return None
            def delete(self, ident): return {"deleted": True}
        self.assertEqual(watchdog.strict_roundtrip(Bad(), "s", "x")["verdict"], "BLIND")

    def test_mixed_malformed_search_hits_are_blind(self):
        class Mixed:
            def __init__(self): self.deleted = False
            def remember(self, text): return {"id": "i", "text": text}
            def search(self, text):
                return {"hits": [] if self.deleted else [{"id": "i", "text": text}, {}]}
            def fetch(self, ident): return None if self.deleted else {"id": "i", "text": "x"}
            def delete(self, ident): self.deleted = True; return {"deleted": True}
        self.assertEqual(watchdog.strict_roundtrip(Mixed(), "s", "x")["verdict"], "BLIND")

    def test_postdelete_mixed_malformed_hits_are_blind(self):
        class Mixed:
            def __init__(self): self.deleted = False
            def remember(self, text): return {"id": "i", "text": text}
            def search(self, text):
                return {"hits": [{"id": "i", "text": text}] if not self.deleted else [{}]}
            def fetch(self, ident): return None if self.deleted else {"id": "i", "text": "x"}
            def delete(self, ident): self.deleted = True; return {"deleted": True}
        self.assertEqual(watchdog.strict_roundtrip(Mixed(), "s", "x")["verdict"], "BLIND")

    def test_scalar_restart_claim_is_unverified(self):
        self.assertEqual(watchdog.boundary_verdict(
            "service_restart", {"generation_before": 1, "generation_after": 2,
                                "same_data_identity": True}), "BOUNDARY_UNVERIFIED")

    def test_run_map_rejects_missing_artifact_and_source_set_subset(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = b"alpha\n"
            (root / "source.bin").write_bytes(data)
            run = {"schema_version": 3, "run_dir": str(root), "generation": "g",
                   "source_digests": {"S": hashlib.sha256(data).hexdigest()},
                   "artifact_digests": {"source.bin": hashlib.sha256(data).hexdigest()},
                   "source_id": "S", "task_digest": "t", "profile_digest": "p"}
            p = root / "run-map.json"; p.write_text(json.dumps(run), encoding="utf-8")
            with self.assertRaises(recall.RecallError):
                recall.load_run_map(str(p), {"S": run["source_digests"]["S"], "OTHER": "x"})


class TestR2FreshVerifier(unittest.TestCase):
    def test_manual_accepted_without_dispatch_proof_is_rejected(self):
        """Valid-looking hashes/manual states are not dispatch measurement proof."""
        from integrity_v2 import report
        engine = Path(__file__).resolve().parents[2] / "claude-mon"
        sys.path.insert(0, str(engine / "scripts"))
        try:
            from complete_read_v2 import artifacts, ledger, partition, results
            with tempfile.TemporaryDirectory(prefix="r2-run-") as temp:
                root = Path(temp); cas = root / "artifacts"; cas.mkdir()
                source = b"alpha rule\n"; source_digest = hashlib.sha256(source).hexdigest()
                source_id = "SRC-" + source_digest[:16]
                manifest = partition.build_manifest(source_id, source)
                task0 = {"schema_version": 3, "instructions": "interpret faithfully"}
                task_digest = hashlib.sha256(json.dumps(task0, sort_keys=True,
                                                        separators=(",", ":")).encode()).hexdigest()
                task = dict(task0, task_digest=task_digest)
                profile0 = {"schema_version": 2, "provider": "fake", "model": "offline-fixture-1",
                            "encoding": "test-char", "encoding_version": "1",
                            "counting_method": "test", "context_limit": 1000000,
                            "output_limit": 100000}
                profile_digest = hashlib.sha256(json.dumps(profile0, sort_keys=True,
                                                           separators=(",", ":")).encode()).hexdigest()
                profile = dict(profile0, profile_digest=profile_digest)
                generation = "fixture-generation"
                unit = manifest["units"][0]
                db = ledger.connect(root / "ledger.sqlite")
                ledger.create_work_item(db, "C00000001", task_digest, source_id)
                request_object = {"schema_version": 2, "kind": "complete-request",
                                  "work_item_id": "C00000001", "task_digest": task_digest,
                                  "task_spec_digest": task_digest, "primary_unit_ids": [unit["id"]],
                                  "model": {"provider": "fake", "model": "offline-fixture-1",
                                            "endpoint": "offline://fixture", "purpose": "offline-audit",
                                            "output_limit": 100000, "max_spend": 0},
                                  "materials": {"source_" + unit["id"]: "alpha rule\n"}}
                request = json.dumps(request_object, sort_keys=True, separators=(",", ":")).encode()
                req_digest = artifacts.store_bytes(cas, request)
                attempt = ledger.begin_attempt(db, "C00000001")
                ledger.transition(db, attempt, "PREPARED", request_digest=req_digest)
                ledger.transition(db, attempt, "AWAITING_APPROVAL", approval_ref="offline")
                approval = ledger.issue_approval(db, attempt, req_digest, "fake", "offline-fixture-1",
                                                 "offline://fixture", "offline-audit", 100000,
                                                 limits={"max_calls": 1, "max_spend": 0})
                ledger.consume_approval(db, approval, attempt, req_digest)
                rich = results.make_result(source, manifest, unit["id"], task_digest, attempt,
                                           "alpha rule", findings=[])
                response = {"terminal_state": "ok", "evidence_class": "TEST_ONLY",
                            "results": {unit["id"]: rich}}
                raw_response = json.dumps(response, sort_keys=True, separators=(",", ":")).encode()
                response_digest = artifacts.store_bytes(cas, raw_response)
                ledger.transition(db, attempt, "DISPATCHING")
                ledger.transition(db, attempt, "RESPONSE_SAVED", response_digest=response_digest)
                ledger.transition(db, attempt, "VALIDATED")
                ledger.transition(db, attempt, "ACCEPTED")
                db.close()
                scope = {"schema_version": 3, "source_id": source_id, "source_digest": source_digest,
                         "task_digest": task_digest, "generation": generation,
                         "required_unit_ids": [unit["id"]]}
                extraction = {"schema_version": 3, "source_id": source_id, "source_digest": source_digest,
                              "task_digest": task_digest, "generation": generation,
                              "expected": {"units": 1}, "produced": {"units": 1}, "diagnostics": [],
                              "evidence_class": "TEST_ONLY", "format": "utf8-text"}
                semantic = {"schema_version": 3, "source_id": source_id, "source_digest": source_digest,
                            "task_digest": task_digest, "generation": generation,
                            "reviews": [{"unit_id": unit["id"], "reviewer": "fixture-reviewer",
                                         "findings": [], "unresolved": [], "source_digest": source_digest,
                                         "task_digest": task_digest}]}
                (root / "source.bin").write_bytes(source)
                for name, payload in (("manifest.json", manifest), ("task.json", task),
                                      ("profile.json", profile), ("scope.json", scope),
                                      ("extraction.json", extraction), ("semantic.json", semantic)):
                    (root / name).write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
                paths = ["source.bin", "manifest.json", "task.json", "profile.json", "scope.json",
                         "extraction.json", "semantic.json", "ledger.sqlite",
                         "artifacts/" + req_digest, "artifacts/" + response_digest]
                digest_map = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths}
                run = {"schema_version": 3, "run_dir": str(root), "generation": generation,
                       "source_digests": {source_id: source_digest}, "artifact_digests": digest_map,
                       "source_id": source_id, "task_digest": task_digest, "profile_digest": profile_digest}
                run_path = root / "run-map.json"; run_path.write_text(json.dumps(run), encoding="utf-8")
                passed = report.verify_run(str(run_path), {source_id: source_digest}, str(engine))
                self.assertFalse(passed["ok"], passed)
                self.assertTrue(any("PROOF" in item for item in passed["blockers"]), passed)
                (root / "semantic.json").write_text("{}", encoding="utf-8")
                failed = report.verify_run(str(run_path), {source_id: source_digest}, str(engine))
                self.assertFalse(failed["ok"])
        finally:
            sys.path.remove(str(engine / "scripts"))


if __name__ == "__main__":
    unittest.main()
