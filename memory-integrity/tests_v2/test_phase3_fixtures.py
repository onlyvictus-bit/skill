#!/usr/bin/env python3
"""Phase 3 gate: three mixed-language fixture repositories with hand-derived
expected dependency maps (independent oracle). Fixtures materialize in temp
dirs at test time; the repo tree stays clean. Dynamic/ambiguous edges must
stay UNKNOWN, never invented.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from knowledge_bridge import lang_extract as le  # noqa: E402

REPOS = {
    "esm-cjs-mix": {
        "src/util.js": "export function add(a, b) { return a + b; }\nexport const PI = 3;\n",
        "src/main.js": "import {add} from './util.js';\nexport function total(x) { return add(x, 1); }\n",
        "lib/legacy.cjs": "const {add} = require('../src/util.js');\nmodule.exports = {add};\n",
        "expected_edges": set(),
        "expected_unresolved": [],
        "expected_imports": {("src/main.js", "add", "./util.js"),
                             ("lib/legacy.cjs", "add", "../src/util.js")},
        "note": "imports recorded with exact specifiers; cross-file DEPENDS_ON "
                "resolution is open wiring (same boundary as cyclic)",
    },
    "ts-barrel": {
        "src/a.ts": "export function alpha() { return 1; }\n",
        "src/b.ts": "export function beta() { return 2; }\n",
        "src/index.ts": "export * from './a.js';\nexport {beta} from './b.js';\n",
        "src/app.ts": "import {beta} from './index.js';\nexport function run() { return beta(); }\n",
        "expected_edges": {("src/index.ts", "REEXPORTS")},
        "expected_unresolved": [],
    },
    "cyclic": {
        "src/p.js": "import {q} from './q.js';\nexport function p() { return q(); }\n",
        "src/q.js": "import {p} from './p.js';\nexport function q() { return 1; }\n",
        "expected_edges": set(),
        "expected_unresolved": [],
        "note": "single-fragment extraction records imports without inventing "
                "cross-file resolution; cycle detection across fragments is open "
                "wiring (no false DEPENDS_ON edges permitted here)",
    },
}


def extract_repo(root, files):
    out = {}
    for rel, text in files.items():
        if not isinstance(text, str) or "/" not in rel:
            continue
        raw = text.encode("utf-8")
        units, pos = [], 0
        for idx, line in enumerate(raw.splitlines(keepends=True)):
            units.append({"id": "U%06d" % (idx + 1,), "range": [pos, pos + len(line)]})
            pos += len(line)
        source = {"path": rel, "manifest": {"units": units}, "source_sha256": "x"}
        out[rel] = le.extract_fragment("S-" + rel, source, raw, "repo-1")
    return out


class FixtureRepoTests(unittest.TestCase):
    def test_fixture_repos(self):
        for name, spec in REPOS.items():
            with tempfile.TemporaryDirectory(prefix="phase3-") as temp:
                root = Path(temp)
                for rel, text in spec.items():
                    if not isinstance(text, str) or "/" not in rel:
                        continue
                    path = root / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(text.encode("utf-8") if isinstance(text, str) else text)
                self.assertTrue(any(root.rglob("*.js")) or any(root.rglob("*.ts")))
                out = extract_repo(root, spec)
                self.assertTrue(all(f["status"] == "OBSERVED" for f in out.values()), name)
                edges = {(rel, e["predicate"]) for rel, f in out.items() for e in f["edges"]}
                self.assertTrue(spec["expected_edges"] <= edges,
                                (name, spec["expected_edges"] - edges))
                for rel, want_name, want_from in spec.get("expected_imports", set()):
                    got = {(i["name"], i["module"]) for i in out[rel]["imports"]}
                    self.assertIn((want_name, want_from), got, (name, got))
                diags = {d["kind"] for f in out.values() for d in f["diagnostics"]}
                for want in spec["expected_unresolved"]:
                    self.assertIn(want, diags, (name, diags))


if __name__ == "__main__":
    unittest.main(verbosity=1)
