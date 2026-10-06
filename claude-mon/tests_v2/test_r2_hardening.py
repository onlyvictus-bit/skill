#!/usr/bin/env python3
"""R2 companion regressions: dispatch facts must be bound before any adapter call."""
import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import artifacts, ledger, partition, providers, results, runner  # noqa: E402
import claude_mon_v2 as cli  # noqa: E402


def profile(**change):
    out = {"schema_version": 2, "provider": "fake", "model": "fake-1",
           "encoding": "synthetic", "encoding_version": "v1", "context_limit": 2000,
           "output_limit": 50, "counting_method": "injected-counter",
           "endpoint": "test-only-transport", "purpose": "offline-test"}
    out.update(change)
    return out


def memory_store(store):
    def save(_root, data):
        digest = hashlib.sha256(data).hexdigest()
        store[digest] = data
        return digest
    return save


def prepared(db, store):
    ledger.create_work_item(db, "W", "task-A", "SRC")
    source = b"alpha"
    manifest = partition.build_manifest("SRC", source)
    return runner.prepare(db, "art", "W", "task-A", {"U000001": "alpha"},
                          "read", {"type": "object"}, {}, "spec-A", profile(),
                          counter=list, manifest=manifest, source_bytes=source)


class R2Dispatch(unittest.TestCase):
    def test_final_payload_measurement_is_external_and_exact(self):
        raw, digest, measurement = providers.build_complete_request(
            "W", "task-A", {"U1": "alpha"}, "read", {"type": "object"}, {},
            "spec-A", profile(), counter=list)
        self.assertEqual(measurement["final_payload_sha256"], digest)
        self.assertEqual(measurement["final_payload_bytes"], len(raw))
        body = json.loads(raw)
        self.assertNotIn("final_payload_bytes", body["measurement"])
        self.assertNotIn("final_payload_sha256", body["measurement"])

    def test_context_one_with_output_reserve_rejects_before_adapter_boundary(self):
        raw, _digest, _measurement = providers.build_complete_request(
            "W", "task-A", {"U1": "alpha"}, "read", {"type": "object"}, {},
            "spec-A", profile(context_limit=2000), counter=list)
        called = []
        class Spy:
            def dispatch(self, _raw):
                called.append(True)
        with self.assertRaisesRegex(providers.AdapterError, "FINAL_PAYLOAD_BUDGET"):
            providers.final_payload_measurement(raw, profile(context_limit=1), counter=list)
        self.assertEqual(called, [])

    def test_dispatch_rejects_profile_approval_mismatch_before_adapter(self):
        store = {}
        with patch.object(artifacts, "store_bytes", side_effect=memory_store(store)), \
             patch.object(artifacts, "open_verified", side_effect=lambda _r, d: store[d]):
            db = ledger.connect(":memory:")
            attempt, digest = prepared(db, store)
            runner.approve(db, attempt, "human-ref")
            approval = ledger.issue_approval(db, attempt, digest, "wrong", "fake-1",
                                             "test-only-transport", "offline-test", 50)
            called = []
            class Spy:
                def dispatch(self, _raw):
                    called.append(True)
                    return {}
            with self.assertRaisesRegex(ledger.LedgerError, "APPROVAL_PROVIDER"):
                runner.dispatch_via_adapter(db, "art", Spy(), attempt, approval)
            self.assertEqual(called, [])
            self.assertEqual(db.execute("SELECT consumed FROM approvals WHERE id=?", (approval,)).fetchone()[0], 0)
            db.close()

    def test_unknown_delivery_cannot_be_bypassed_by_prepare(self):
        store = {}
        with patch.object(artifacts, "store_bytes", side_effect=memory_store(store)), \
             patch.object(artifacts, "open_verified", side_effect=lambda _r, d: store[d]):
            db = ledger.connect(":memory:")
            attempt, _digest = prepared(db, store)
            runner.approve(db, attempt, "human-ref")
            ledger.transition(db, attempt, "DISPATCHING")
            ledger.transition(db, attempt, "DELIVERY_UNKNOWN", error="lost")
            with self.assertRaisesRegex(ledger.LedgerError, "RECOVERY_UNKNOWN"):
                runner.prepare(db, "art", "W", "task-A", {"U000001": "alpha"},
                               "read", {"type": "object"}, {}, "spec-A", profile(), counter=list)
            runner.record_retry_decision(db, "W", attempt, "verified no execution")
            runner.prepare(db, "art", "W", "task-A", {"U000001": "alpha"},
                           "read", {"type": "object"}, {}, "spec-A", profile(), counter=list)
            db.close()

    def test_live_adapter_is_rejected_before_approval_consumption(self):
        store = {}
        with patch.object(artifacts, "store_bytes", side_effect=memory_store(store)), \
             patch.object(artifacts, "open_verified", side_effect=lambda _r, d: store[d]):
            db = ledger.connect(":memory:")
            attempt, digest = prepared(db, store)
            runner.approve(db, attempt, "human-ref")
            approval = ledger.issue_approval(db, attempt, digest, "fake", "fake-1",
                                             "test-only-transport", "offline-test", 50,
                                             {"max_spend": 0})
            class LiveSpy(providers.ProviderAdapter):
                live = True
                evidence_class = "TRANSPORT_OBSERVED"
                def __init__(self): self.calls = 0
                def dispatch(self, _raw): self.calls += 1
            spy = LiveSpy()
            with self.assertRaisesRegex(ledger.LedgerError, "TEST_ONLY"):
                runner.dispatch_via_adapter(db, "art", spy, attempt, approval)
            self.assertEqual(spy.calls, 0)
            self.assertEqual(db.execute("SELECT consumed FROM approvals WHERE id=?", (approval,)).fetchone()[0], 0)
            db.close()


class R2Durability(unittest.TestCase):
    def test_invalid_cas_address_rejects_before_filesystem_read(self):
        for address in ("../outside", "g"*64, "", None):
            with patch.object(Path, "read_bytes") as read:
                with self.assertRaisesRegex(artifacts.ArtifactError, "ADDRESS"):
                    artifacts.open_verified("artifacts", address)
                read.assert_not_called()
    def test_generic_meta_database_is_refused_without_mutation(self):
        db = sqlite3.connect(":memory:", isolation_level=None)
        db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        db.execute("INSERT INTO meta VALUES('unrelated', 'x')")
        db.execute("CREATE TABLE foreign_data(x TEXT)")
        before = list(db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        with patch.object(ledger.sqlite3, "connect", return_value=db):
            with self.assertRaisesRegex(ledger.LedgerError, "FOREIGN"):
                ledger.connect("foreign.db")
        after = [tuple(row) for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        self.assertEqual(before, after)
        self.assertEqual(db.execute("SELECT value FROM meta WHERE key='unrelated'").fetchone()[0], "x")
        db.close()

    def test_strict_result_requires_actual_task_and_attempt(self):
        source = b"alpha"
        manifest = partition.build_manifest("SRC", source)
        record = results.make_result(source, manifest, "U000001", "task-A", "ATT-A", "ok")
        self.assertEqual(results.validate_result(record, source, manifest,
                                                 expect_task_digest="task-A", expect_attempt_id="ATT-A"), [])
        self.assertTrue(results.validate_result(record, source, manifest,
                                                expect_task_digest="task-B", expect_attempt_id="ATT-A"))
        self.assertTrue(results.validate_result(record, source, manifest,
                                                expect_task_digest="task-A", expect_attempt_id="ATT-B"))

    def test_empty_result_list_is_never_a_rich_result(self):
        self.assertFalse(results.validate_rich_results([], b"x", partition.build_manifest("SRC", b"x"),
                                                       "task-A", "ATT-A")[0])


class R2SourceAndRead(unittest.TestCase):
    def test_manifest_rejects_utf8_split_and_reversed_primary(self):
        data = "é\nB\n".encode("utf-8")
        manifest = partition.build_manifest("SRC", data, max_unit_bytes=3, max_primary_bytes=3)
        bad = json.loads(json.dumps(manifest))
        bad["units"][0]["range"] = [0, 1]
        bad["units"][0]["sha256"] = hashlib.sha256(data[:1]).hexdigest()
        bad["units"][1]["range"] = [1, 3]
        bad["units"][1]["sha256"] = hashlib.sha256(data[1:3]).hexdigest()
        bad["manifest_digest"] = partition.manifest_digest(bad)
        self.assertTrue(partition.validate_manifest(data, bad))
        normal = partition.build_manifest("SRC", b"A\nB\nC\n", max_primary_bytes=4)
        reversed_chunk = json.loads(json.dumps(normal))
        reversed_chunk["chunks"][0]["primary"].reverse()
        reversed_chunk["chunks"][0]["payload_sha256"] = hashlib.sha256(
            partition.payload_bytes(b"A\nB\nC\n", reversed_chunk, reversed_chunk["chunks"][0])).hexdigest()
        reversed_chunk["manifest_digest"] = partition.manifest_digest(reversed_chunk)
        self.assertTrue(partition.validate_manifest(b"A\nB\nC\n", reversed_chunk))

    def test_query_rejects_stale_manifest_before_returning_old_hit(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.txt"
            source.write_text("old needle\n", encoding="utf-8")
            manifest = partition.build_manifest("SRC", source.read_bytes())
            manifest_path = Path(temp) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            source.write_text("new data\n", encoding="utf-8")
            result = cli.main(["query", "--manifest-file", str(manifest_path), "--source-file", str(source),
                               "--text", "needle"])
            self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
