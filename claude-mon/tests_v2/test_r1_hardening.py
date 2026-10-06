#!/usr/bin/env python3
"""R1 hardening: every m8 audit probe must now fail closed (F03-F13).

Isolated repair copy only. Each test names its finding ID.
"""
import hashlib
import io
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import (artifacts, budget, inventory, ledger,  # noqa: E402
                              partition, providers, results, runner)
import claude_mon_v2 as cli  # noqa: E402


def _mem_store(art):
    def store(_root, data):
        digest = hashlib.sha256(data).hexdigest()
        art[digest] = data
        return digest
    return store


def _profile(**over):
    base = {"schema_version": 2, "provider": "p", "model": "m",
            "encoding": "synthetic", "encoding_version": "v1",
            "context_limit": 2000, "output_limit": 500,
            "counting_method": "injected-counter", "endpoint": "e",
            "purpose": "do", "max_spend": 0}
    base.update(over)
    return base


class TestF03PreflightContract(unittest.TestCase):
    def test_cli_preflight_runs(self):
        with tempfile.TemporaryDirectory(prefix="r1-") as temp:
            src = Path(temp) / "s.txt"
            src.write_bytes(b"A\n")
            man = partition.build_manifest("S", b"A\n")
            man_path = Path(temp) / "m.json"
            man_path.write_text(__import__("json").dumps(man))
            prof_path = Path(temp) / "p.json"
            prof_path.write_text(__import__("json").dumps(_profile()))
            import types
            args = types.SimpleNamespace(
                run_dir=str(Path(temp) / "run"), manifest_file=str(man_path),
                source_file=str(src), profile_file=str(prof_path),
                work_item="W", per_unit_output=10, task_spec_digest=None,
                counter_words=True, reasoning_reserve=0, safety_reserve=0)
            with patch.object(cli, "emit", side_effect=lambda p, code=0: (p, code)):
                payload, _code = cli.cmd_preflight(args)
            self.assertIn("notes", payload)


class TestF04DispatchIntent(unittest.TestCase):
    def test_state_dispatching_during_call(self):
        art = {}
        with patch.object(artifacts, "store_bytes", side_effect=_mem_store(art)), \
             patch.object(artifacts, "open_verified",
                          side_effect=lambda _r, d: art[d]):
            db = ledger.connect(":memory:")
            ledger.create_work_item(db, "W", "t", "S")
            source = b"A"
            man = partition.build_manifest("S", source)
            att, digest = runner.prepare(db, "m", "W", "t", {"U000001": "A"},
                                         "do", {"type": "object"}, {}, "s",
                                         _profile(), counter=list, manifest=man, source_bytes=source)
            runner.approve(db, att, "ref")
            approval = ledger.issue_approval(db, att, digest, "p", "m", "e",
                                             "do", 500, {"max_spend": 0})
            seen = []

            class Spy(providers.ProviderAdapter):
                evidence_class = "TEST_ONLY"
                def dispatch(self, _raw):
                    seen.append(db.execute("SELECT state FROM attempts WHERE id=?",
                                           (att,)).fetchone()[0])
                    return {"terminal_state": "ok", "evidence_class": "TEST_ONLY",
                            "results": {"U000001": "done"}, "unit_ids": ["U000001"]}

            runner.dispatch_via_adapter(db, "m", Spy(), att, approval)
            self.assertEqual(seen, ["DISPATCHING"])
            db.close()


class TestF05InvalidBasis(unittest.TestCase):
    def test_null_result_rejected(self):
        ok, reason = providers.validate_response(
            {"terminal_state": "ok", "evidence_class": "TEST_ONLY",
             "results": {"U1": None}}, ["U1"], "a" * 64)
        self.assertFalse(ok, reason)

    def test_wrong_task_prepare_rejected(self):
        db = ledger.connect(":memory:")
        ledger.create_work_item(db, "W", "original-task", "S")
        with self.assertRaises(ledger.LedgerError):
            runner.prepare(db, "m", "W", "WRONG-TASK", {"U1": "x"}, "do",
                           {"type": "object"}, {}, "s", _profile(), counter=list)
        db.close()

    def test_full_invalid_basis_cannot_accept(self):
        art = {}
        with patch.object(artifacts, "store_bytes", side_effect=_mem_store(art)), \
             patch.object(artifacts, "open_verified",
                          side_effect=lambda _r, d: art[d]):
            db = ledger.connect(":memory:")
            ledger.create_work_item(db, "W", "t", "S")
            man = partition.build_manifest("S", b"A\n")
            source = b"A\n"
            man = partition.build_manifest("S", source)
            att, digest = runner.prepare(db, "m", "W", "t", {"U000001": "A\n"},
                                         "do", {"type": "object"}, {}, "s",
                                         _profile(), counter=list, manifest=man, source_bytes=source)
            runner.approve(db, att, "ref")
            approval = ledger.issue_approval(db, att, digest, "p", "m", "e",
                                             "do", 500, {"max_spend": 0})
            runner.dispatch_via_adapter(
                db, "m", providers.TestOnlyAdapter([("ok", {"U000001": None})]),
                att, approval)
            row = db.execute("SELECT state FROM attempts WHERE id=?", (att,)).fetchone()
            self.assertEqual(row["state"], "INVALID_RESULT")
            with self.assertRaises(ledger.LedgerError):
                runner.accept(db, "m", att, "t", man, b"A\n",
                              {"provider": "p", "model": "m", "endpoint": "e",
                               "purpose": "do", "max_output_tokens": 500})
            db.close()


class TestF06ProfileBinding(unittest.TestCase):
    def test_profile_change_alters_digest(self):
        kw = dict(work_item_id="W", task_digest="t", units_text={"U1": "A"},
                  instructions="do XXXXXXXXXX", result_schema={"type": "object"},
                  context_sections={}, task_spec_digest="s", counter=list)
        raw1, d1, _ = providers.build_complete_request(model=_profile(), **kw)
        raw2, d2, _ = providers.build_complete_request(
            model=_profile(context_limit=999999), **kw)
        self.assertNotEqual(d1, d2)
        self.assertNotEqual(raw1, raw2)

    def test_serialized_size_recorded(self):
        _raw, _d, measurement = providers.build_complete_request(
            "W", "t", {"U1": "A"}, "do X", {"type": "object"}, {}, "s",
            _profile(), counter=list)
        self.assertGreater(measurement["serialized_characters"], measurement["input_tokens"])


class TestF08Reads(unittest.TestCase):
    def test_open_unit_stale_source(self):
        man = partition.build_manifest("S", b"A\n")
        with patch.object(cli, "load_json", return_value=man), \
             patch.object(cli, "Path", return_value=__import__("types").SimpleNamespace(
                 read_bytes=lambda: b"Z\n")), \
             patch.object(cli, "emit", side_effect=lambda p, code=0: (p, code)):
            import types
            payload, _code = cli.cmd_open_unit(types.SimpleNamespace(
                manifest_file="m", source_file="s", unit_id=man["units"][0]["id"]))
        self.assertFalse(payload["ok"])
        self.assertIn("STALE", payload["error"])

    def test_query_unicode(self):
        data = "é\nneedle\n".encode("utf-8")
        man = partition.build_manifest("S", data)
        with patch.object(cli, "load_json", return_value=man), \
             patch.object(cli, "Path", return_value=__import__("types").SimpleNamespace(
                 read_bytes=lambda: data)), \
             patch.object(cli, "emit", side_effect=lambda p, code=0: (p, code)):
            import types
            payload, _code = cli.cmd_query(types.SimpleNamespace(
                manifest_file="m", source_file="s", text="needle", max_hits=50))
        self.assertTrue(payload["hits"])


class TestF09Snapshot(unittest.TestCase):
    def test_corrupt_snapshot_refused(self):
        with tempfile.TemporaryDirectory(prefix="r1-") as temp:
            root = Path(temp)
            (root / "a.txt").write_bytes(b"original\n")
            snap = root / ".snapshot"
            snap.mkdir()
            digest = hashlib.sha256(b"original\n").hexdigest()
            (snap / digest).write_bytes(b"corrupt")
            with self.assertRaises(inventory.ContractError):
                inventory.freeze_scope(root, ["a.txt"])

    def test_valid_snapshot_reused(self):
        with tempfile.TemporaryDirectory(prefix="r1-") as temp:
            root = Path(temp)
            (root / "a.txt").write_bytes(b"v\n")
            first = inventory.freeze_scope(root, ["a.txt"])
            second = inventory.freeze_scope(root, ["a.txt"])
            self.assertEqual(first["scope_digest"], second["scope_digest"])


class TestF10LedgerOwnership(unittest.TestCase):
    def test_foreign_db_untouched(self):
        db = sqlite3.connect(":memory:", isolation_level=None)
        db.execute("CREATE TABLE foreign_data(x TEXT)")
        with patch.object(ledger.sqlite3, "connect", return_value=db):
            with self.assertRaises(ledger.LedgerError):
                ledger.connect("not-opened")
            tables = [r[0] for r in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            self.assertEqual(tables, ["foreign_data"])
        db.close()

    def test_unsupported_version_untouched(self):
        db = sqlite3.connect(":memory:", isolation_level=None)
        db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        db.execute("INSERT INTO meta VALUES('schema_version', '99')")
        with patch.object(ledger.sqlite3, "connect", return_value=db):
            with self.assertRaises(ledger.LedgerError):
                ledger.connect("not-opened")
            tables = [r[0] for r in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            self.assertEqual(tables, ["meta"])
        db.close()


class TestF11Imports(unittest.TestCase):
    def test_oversize_chunk_rejected(self):
        man = partition.build_manifest("S", b"AAAA")
        man["max_primary_bytes"] = 1
        man["manifest_digest"] = partition.manifest_digest(man)
        self.assertTrue(partition.validate_manifest(b"AAAA", man))

    def test_invalid_utf8_rejected(self):
        digest = hashlib.sha256(b"\xff").hexdigest()
        man = {"schema_version": 2, "source_id": "S", "source_digest": digest,
               "max_primary_bytes": 1,
               "units": [{"id": "U1", "range": [0, 1], "sha256": digest,
                          "parent": None, "kind": "madeup", "ordinal": 999}],
               "chunks": [{"id": "C1", "primary": ["U1"], "context_before": [],
                           "context_after": [], "payload_sha256": digest}]}
        man["manifest_digest"] = partition.manifest_digest(man)
        self.assertTrue(partition.validate_manifest(b"\xff", man))


class TestF12Results(unittest.TestCase):
    def test_invalid_fields_rejected(self):
        man = partition.build_manifest("S", b"A\n")
        good = results.make_result(b"A\n", man, man["units"][0]["id"], "t", "a", "A exists")
        bad = dict(good, interpretation="", findings=7, disposition="unknown",
                   task_digest="foreign-task", attempt_id="foreign-attempt")
        self.assertTrue(results.validate_result(bad, b"A\n", man))


class TestF13ContextPayload(unittest.TestCase):
    def test_payload_contains_context(self):
        man = partition.build_manifest("S", b"A\nB\n", max_unit_bytes=2,
                                       max_primary_bytes=2)
        chunk = man["chunks"][0]
        self.assertTrue(chunk["context_after"])
        payload = partition.payload_bytes(b"A\nB\n", man, chunk)
        self.assertIn(b"B\n", payload)
        self.assertFalse(partition.validate_manifest(b"A\nB\n", man))


class TestF05StrictAcceptPositive(unittest.TestCase):
    def test_valid_basis_accepts(self):
        art = {}
        with patch.object(artifacts, "store_bytes", side_effect=_mem_store(art)), \
             patch.object(artifacts, "open_verified",
                          side_effect=lambda _r, d: art[d]):
            db = ledger.connect(":memory:")
            source = b"alpha beta"
            man = partition.build_manifest("SRC-1", source)
            ledger.create_work_item(db, "W", "t", "SRC-1")
            att, digest = runner.prepare(db, "m", "W", "t", {"U000001": "alpha beta"},
                                         "do", {"type": "object"}, {}, "s",
                                         _profile(), counter=list, manifest=man, source_bytes=source)
            runner.approve(db, att, "ref")
            approval = ledger.issue_approval(db, att, digest, "p", "m", "e",
                                             "do", 500, {"max_spend": 0})
            rich = results.make_result(source, man, "U000001", "t", att, "parsed")
            runner.dispatch_via_adapter(
                db, "m", providers.TestOnlyAdapter([("ok", {"U000001": rich})]),
                att, approval)
            runner.accept(db, "m", att, "t", man, source,
                          {"provider": "p", "model": "m", "endpoint": "e",
                               "purpose": "do", "max_output_tokens": 500})
            self.assertEqual(ledger.accepted_attempt(db, "W"), att)
            db.close()


if __name__ == "__main__":
    unittest.main(verbosity=1)
