import json
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from claude_mon_core import build_chunk_manifest, register_source, unitize_source, verify_chunk_manifest, verify_unit_manifest

TARGET = 50 * 1024 * 1024

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "docs" / "fable").mkdir(parents=True)
    src = root / "large.txt"
    line = ("0123456789abcdef" * 16 + " αβγ🙂\n").encode("utf-8")
    with src.open("wb") as f:
        written = 0
        while written < TARGET:
            remaining = TARGET - written
            piece = line if len(line) <= remaining else b"x" * remaining
            f.write(piece)
            written += len(piece)
    rec = register_source(root, src, required=True)
    um = unitize_source(root, rec["source_id"], max_unit_bytes=64 * 1024)
    uv = verify_unit_manifest(root, rec["source_id"])
    assert uv["ok"], uv
    cm = build_chunk_manifest(root, rec["source_id"], max_primary_bytes=256 * 1024, context_units=1)
    cv = verify_chunk_manifest(root, rec["source_id"])
    assert cv["ok"], cv
    assert um["byte_size"] == TARGET
    print(json.dumps({"ok": True, "bytes": TARGET, "units": um["unit_count"], "chunks": cm["chunk_count"]}, sort_keys=True))
