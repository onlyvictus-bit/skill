import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from claude_mon_core import (  # noqa: E402
    IntegrityError,
    PathSafetyError,
    build_chunk_manifest,
    get_chunk_payload,
    derive_receipt_status,
    load_registry,
    record_receipt,
    register_source,
    sha256_file,
    unitize_source,
    verify_chunk_manifest,
    verify_receipt,
    verify_unit_manifest,
)


class ClaudeMonCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs" / "fable").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write_text(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="")
        return p

    def test_register_uses_content_hash_and_rejects_outside_root(self):
        src = self.write_text("src/a.txt", "alpha\nβeta\n")
        rec = register_source(self.root, src, required=True, provenance=["user-request"])
        self.assertEqual(rec["current_version"]["sha256"], sha256_file(src))
        self.assertEqual(rec["current_version"]["byte_size"], src.stat().st_size)
        self.assertEqual(rec["path"], "src/a.txt")
        self.assertTrue(rec["required"])
        with tempfile.NamedTemporaryFile(delete=False) as f:
            outside = Path(f.name)
        try:
            with self.assertRaises(PathSafetyError):
                register_source(self.root, outside)
        finally:
            outside.unlink(missing_ok=True)

    def test_register_changed_content_preserves_version_history(self):
        src = self.write_text("a.txt", "one\n")
        first = register_source(self.root, src)
        first_hash = first["current_version"]["sha256"]
        src.write_text("two\n", encoding="utf-8")
        second = register_source(self.root, src)
        self.assertNotEqual(first_hash, second["current_version"]["sha256"])
        self.assertEqual([v["sha256"] for v in second["versions"]], [first_hash, second["current_version"]["sha256"]])

    def test_unit_manifest_is_exact_deterministic_and_unicode_safe(self):
        text = ("αβγ🙂\n" * 31) + "tail"
        src = self.write_text("unicode.txt", text)
        rec = register_source(self.root, src)
        m1 = unitize_source(self.root, rec["source_id"], max_unit_bytes=17)
        m2 = unitize_source(self.root, rec["source_id"], max_unit_bytes=17)
        self.assertEqual(m1["units_sha256"], m2["units_sha256"])
        self.assertTrue(verify_unit_manifest(self.root, rec["source_id"])["ok"])
        units_path = self.root / m1["units_path"]
        with units_path.open(encoding="utf-8") as f:
            units = [json.loads(line) for line in f]
        self.assertGreater(len(units), 5)
        self.assertEqual(units[0]["start_byte"], 0)
        self.assertEqual(units[-1]["end_byte"], src.stat().st_size)
        for u in units:
            raw = src.read_bytes()[u["start_byte"]:u["end_byte"]]
            raw.decode("utf-8", "strict")

    def test_unitize_rejects_invalid_utf8(self):
        src = self.root / "bad.bin"
        src.write_bytes(b"abc\xffdef")
        rec = register_source(self.root, src, kind="text")
        with self.assertRaises(UnicodeDecodeError):
            unitize_source(self.root, rec["source_id"], max_unit_bytes=4)

    def test_chunk_manifest_has_exact_primary_coverage_and_context_is_not_primary(self):
        src = self.write_text("a.txt", "".join(f"line {i}\n" for i in range(60)))
        rec = register_source(self.root, src)
        unitize_source(self.root, rec["source_id"], max_unit_bytes=23)
        cm = build_chunk_manifest(self.root, rec["source_id"], max_primary_bytes=70, context_units=1)
        result = verify_chunk_manifest(self.root, rec["source_id"])
        self.assertTrue(result["ok"], result)
        chunks = [json.loads(x) for x in (self.root / cm["chunks_path"]).read_text().splitlines()]
        primaries = [u for c in chunks for u in c["primary_units"]]
        self.assertEqual(len(primaries), len(set(primaries)))
        self.assertTrue(any(c["context_before"] or c["context_after"] for c in chunks[1:]))

    def test_chunk_payload_materializes_exact_bytes_and_hash(self):
        src = self.write_text("payload.txt", "α\nβ\nγ\nδ\n")
        rec = register_source(self.root, src)
        unitize_source(self.root, rec["source_id"], max_unit_bytes=5)
        cm = build_chunk_manifest(self.root, rec["source_id"], max_primary_bytes=6, context_units=1)
        chunks = [json.loads(x) for x in (self.root / cm["chunks_path"]).read_text().splitlines()]
        payload = get_chunk_payload(self.root, rec["source_id"], chunks[0]["chunk_id"])
        self.assertEqual(payload["chunk_id"], chunks[0]["chunk_id"])
        self.assertEqual(payload["payload_sha256"], chunks[0]["payload_sha256"])
        self.assertEqual(payload["text"].encode("utf-8"), payload["bytes"])
        self.assertEqual(payload["primary_units"], chunks[0]["primary_units"])

    def test_chunk_verifier_detects_missing_and_duplicate_primary_units(self):
        src = self.write_text("a.txt", "a\nb\nc\nd\ne\nf\n")
        rec = register_source(self.root, src)
        unitize_source(self.root, rec["source_id"], max_unit_bytes=2)
        cm = build_chunk_manifest(self.root, rec["source_id"], max_primary_bytes=4, context_units=0)
        chunks_path = self.root / cm["chunks_path"]
        chunks = [json.loads(x) for x in chunks_path.read_text().splitlines()]
        victim = chunks[0]["primary_units"].pop()
        chunks[-1]["primary_units"].append(chunks[-1]["primary_units"][0])
        chunks_path.write_text("".join(json.dumps(c, sort_keys=True, separators=(",", ":")) + "\n" for c in chunks))
        result = verify_chunk_manifest(self.root, rec["source_id"], trust_manifest_digest=False)
        self.assertFalse(result["ok"])
        self.assertIn(victim, result["missing_units"])
        self.assertTrue(result["duplicate_primary_units"])

    def _prepared_source(self):
        src = self.write_text("a.txt", "".join(f"row-{i}\n" for i in range(40)))
        rec = register_source(self.root, src)
        um = unitize_source(self.root, rec["source_id"], max_unit_bytes=32)
        cm = build_chunk_manifest(self.root, rec["source_id"], max_primary_bytes=96, context_units=1)
        chunks = [json.loads(x) for x in (self.root / cm["chunks_path"]).read_text().splitlines()]
        return src, rec, um, cm, chunks

    def test_receipt_complete_is_task_bound_and_append_only(self):
        src, rec, um, cm, chunks = self._prepared_source()
        outcomes = [{"chunk_id": c["chunk_id"], "status": "ok", "input_sha256": c["payload_sha256"]} for c in chunks]
        receipt = record_receipt(
            self.root,
            rec["source_id"],
            task_spec="extract every requirement",
            processor={"kind": "model", "name": "test-model"},
            chunk_outcomes=outcomes,
        )
        self.assertEqual(receipt["status"], "COMPLETE")
        verified = verify_receipt(self.root, receipt["receipt_id"], task_spec="extract every requirement")
        self.assertEqual(verified["status"], "COMPLETE")
        self.assertTrue(verified["coverage_only"])
        receipt_path = self.root / "docs" / "fable" / "claude-mon" / "receipts" / "runs" / f"{receipt['receipt_id']}.json"
        with self.assertRaises(FileExistsError):
            receipt_path.open("x").close()

    def test_receipt_cannot_be_complete_without_exact_input_hashes(self):
        src, rec, um, cm, chunks = self._prepared_source()
        outcomes = [{"chunk_id": c["chunk_id"], "status": "ok"} for c in chunks]
        receipt = record_receipt(
            self.root,
            rec["source_id"],
            task_spec="hash-bound task",
            processor={"kind": "model", "name": "test-model"},
            chunk_outcomes=outcomes,
        )
        self.assertEqual(receipt["status"], "ERROR")
        self.assertTrue(all(o.get("integrity_error") == "MISSING_INPUT_HASH" for o in receipt["chunk_outcomes"]))
        verified = verify_receipt(self.root, receipt["receipt_id"], task_spec="hash-bound task")
        self.assertEqual(verified["status"], "ERROR")

    def test_verify_receipt_rechecks_input_hashes_in_saved_receipt(self):
        src, rec, um, cm, chunks = self._prepared_source()
        outcomes = [{"chunk_id": c["chunk_id"], "status": "ok", "input_sha256": c["payload_sha256"]} for c in chunks]
        receipt = record_receipt(
            self.root, rec["source_id"], "tamper-check", {"kind": "model", "name": "test-model"}, outcomes
        )
        receipt_path = self.root / "docs" / "fable" / "claude-mon" / "receipts" / "runs" / f"{receipt['receipt_id']}.json"
        saved = json.loads(receipt_path.read_text(encoding="utf-8"))
        saved["chunk_outcomes"][0].pop("input_sha256")
        receipt_path.write_text(json.dumps(saved, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        verified = verify_receipt(self.root, receipt["receipt_id"], task_spec="tamper-check")
        self.assertEqual(verified["status"], "ERROR")
        self.assertEqual(verified.get("reason"), "INPUT_HASH_INTEGRITY_FAILED")

    def test_receipt_status_precedence(self):
        expected = ["C1", "C2"]
        self.assertEqual(derive_receipt_status(expected, [{"chunk_id": "C1", "status": "ok"}]), "PARTIAL")
        self.assertEqual(derive_receipt_status(expected, [{"chunk_id": "C1", "status": "truncated"}]), "TRUNCATED")
        self.assertEqual(derive_receipt_status(expected, [{"chunk_id": "C1", "status": "error"}]), "ERROR")
        self.assertEqual(derive_receipt_status(expected, [{"chunk_id": "C1", "status": "ok"}, {"chunk_id": "C2", "status": "ok"}]), "COMPLETE")

    def test_receipt_becomes_stale_after_source_change_without_rewriting_history(self):
        src, rec, um, cm, chunks = self._prepared_source()
        outcomes = [{"chunk_id": c["chunk_id"], "status": "ok", "input_sha256": c["payload_sha256"]} for c in chunks]
        receipt = record_receipt(self.root, rec["source_id"], "task-v1", {"kind": "model", "name": "x"}, outcomes)
        receipt_file = self.root / "docs" / "fable" / "claude-mon" / "receipts" / "runs" / f"{receipt['receipt_id']}.json"
        before = receipt_file.read_bytes()
        src.write_text(src.read_text() + "changed\n", encoding="utf-8")
        register_source(self.root, src)
        verified = verify_receipt(self.root, receipt["receipt_id"], task_spec="task-v1")
        self.assertEqual(verified["status"], "STALE")
        self.assertEqual(before, receipt_file.read_bytes())

    def test_status_does_not_emit_source_content(self):
        secret = "SUPER_SECRET_CONTENT_42"
        src = self.write_text("secret.txt", secret)
        rec = register_source(self.root, src)
        registry = load_registry(self.root)
        rendered = json.dumps(registry)
        self.assertNotIn(secret, rendered)


if __name__ == "__main__":
    unittest.main()
