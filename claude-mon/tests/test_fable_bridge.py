import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from claude_mon_core import build_chunk_manifest, record_receipt, register_source, unitize_source  # noqa: E402
from fable_bridge import check_required_sources  # noqa: E402


class FableBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs" / "fable").mkdir(parents=True)
        self.src = self.root / "req.md"
        self.src.write_text("A\nB\nC\n", encoding="utf-8")
        self.rec = register_source(self.root, self.src, required=True)
        unitize_source(self.root, self.rec["source_id"], max_unit_bytes=2)
        cm = build_chunk_manifest(self.root, self.rec["source_id"], max_primary_bytes=4, context_units=0)
        self.chunks = [json.loads(x) for x in (self.root / cm["chunks_path"]).read_text().splitlines()]

    def tearDown(self):
        self.tmp.cleanup()

    def test_gate_blocks_until_matching_complete_task_receipt_exists(self):
        blocked = check_required_sources(self.root, task_spec="task-a")
        self.assertFalse(blocked["ok"])
        self.assertEqual(blocked["blocked"][0]["reason"], "NO_COMPLETE_RECEIPT")
        outcomes = [{"chunk_id": c["chunk_id"], "status": "ok", "input_sha256": c["payload_sha256"]} for c in self.chunks]
        record_receipt(self.root, self.rec["source_id"], "task-b", {"kind": "model", "name": "x"}, outcomes)
        still_blocked = check_required_sources(self.root, task_spec="task-a")
        self.assertFalse(still_blocked["ok"])
        record_receipt(self.root, self.rec["source_id"], "task-a", {"kind": "model", "name": "x"}, outcomes)
        passed = check_required_sources(self.root, task_spec="task-a")
        self.assertTrue(passed["ok"], passed)

    def test_gate_blocks_stale_receipt(self):
        outcomes = [{"chunk_id": c["chunk_id"], "status": "ok", "input_sha256": c["payload_sha256"]} for c in self.chunks]
        record_receipt(self.root, self.rec["source_id"], "task-a", {"kind": "model", "name": "x"}, outcomes)
        self.src.write_text("A\nB\nC\nD\n", encoding="utf-8")
        register_source(self.root, self.src, required=True)
        result = check_required_sources(self.root, task_spec="task-a")
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
