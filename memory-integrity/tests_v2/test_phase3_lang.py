#!/usr/bin/env python3
"""Phase 3 RED: cross-language extraction with explicit unknown states.

Each test names its requirement. Must FAIL before implementation, pass
after, without weakening any existing suite. Expected edge sets below are
the hand-derived independent oracle for the fixture sources.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from knowledge_bridge import lang_extract as le  # noqa: E402


def frag(path, text):
    raw = text.encode("utf-8") if isinstance(text, str) else bytes(text)
    units, pos = [], 0
    for idx, line in enumerate(raw.splitlines(keepends=True)):
        units.append({"id": "U%06d" % (idx + 1,), "range": [pos, pos + len(line)]})
        pos += len(line)
    source = {"path": path, "manifest": {"units": units}, "source_sha256": "x"}
    return le.extract_fragment("S1", source, raw, "repo-1")


class EsmTests(unittest.TestCase):
    SRC = ("import {a, b as c} from './mod.js';\n"
           "import def from './d.js';\n"
           "import * as ns from './n.js';\n"
           "import type {T} from './t.ts';\n"
           "export function f() { return a + c(); }\n"
           "export default 42;\n")

    def test_named_default_namespace_type_imports(self):
        out = frag("src/a.js", self.SRC)
        self.assertEqual(out["status"], "OBSERVED")
        kinds = sorted(i["kind"] for i in out["imports"])
        self.assertIn("named", kinds)
        self.assertIn("default", kinds)
        self.assertIn("namespace", kinds)
        self.assertIn("type-only", kinds)
        names = {i["name"] for i in out["imports"]}
        self.assertTrue({"a", "c", "def", "ns", "T"} <= names)

    def test_exports_and_resolved_calls(self):
        out = frag("src/a.js", self.SRC)
        exported = {e["name"] for e in out["exports"]}
        self.assertIn("f", exported)
        callees = {c["callee"] for c in out["calls"] if c["resolved"]}
        self.assertIn("c", callees)

    def test_spans_are_byte_exact(self):
        text = self.SRC
        out = frag("src/a.js", text)
        raw = text.encode("utf-8")
        for symbol in out["symbols"]:
            start, end = symbol["range"]
            self.assertIn(symbol["name"], raw[start:end].decode("utf-8"))


class CjsTests(unittest.TestCase):
    def test_require_and_exports(self):
        out = frag("lib/b.cjs", "const x = require('./x.js');\n"
                   "exports.run = function() { return x(); };\n"
                   "module.exports = {run: exports.run};\n")
        self.assertEqual(out["status"], "OBSERVED")
        self.assertTrue(any(i["kind"] == "require" for i in out["imports"]))
        self.assertTrue(any(e["name"] == "run" for e in out["exports"]))


class BarrelTests(unittest.TestCase):
    def test_reexport_edges(self):
        out = frag("src/index.js", "export * from './a.js';\n"
                   "export {f} from './b.js';\n")
        kinds = {e["predicate"] for e in out["edges"]}
        self.assertIn("REEXPORTS", kinds)


class DynamicTests(unittest.TestCase):
    def test_dynamic_import_unknown(self):
        out = frag("src/d.js", "async function load(n) { return import(n); }\n")
        self.assertFalse([e for e in out["edges"] if e["predicate"] == "DEPENDS_ON"])
        diags = {d["kind"] for d in out["diagnostics"]}
        self.assertIn("DYNAMIC_BINDING", diags)

    def test_shadowed_no_false_edge(self):
        out = frag("src/s.js", "import {v} from './v.js';\n"
                   "function f() { let v = 1; return v(1); }\n")
        self.assertTrue([c for c in out["calls"] if not c["resolved"]])
        self.assertFalse([e for e in out["edges"]
                          if e.get("object", "").endswith("v")])
        diags = {d["kind"] for d in out["diagnostics"]}
        self.assertIn("DYNAMIC_BINDING", diags)


class TsTests(unittest.TestCase):
    def test_namespace_and_interface(self):
        out = frag("src/n.ts", "namespace N { export const x = 1; }\n"
                   "interface I { id: string; }\n"
                   "import {y} from './y.js';\n"
                   "export function g() { return N.x + y; }\n")
        self.assertEqual(out["status"], "OBSERVED")
        self.assertTrue(any("N" in s["name"] for s in out["symbols"]))
        self.assertFalse([e for e in out["edges"] if "I" in e.get("object", "")])


class PythonParityTests(unittest.TestCase):
    def test_python_path_unchanged(self):
        from knowledge_bridge import extraction
        source = {"path": "m.py",
                  "manifest": {"units": [{"id": "U000001", "range": [0, 10]}]},
                  "source_sha256": "x"}
        out = extraction._fragment("S1", source, b"import os\n", "repo-1")
        self.assertEqual(out["status"], "OBSERVED")

    def test_other_suffixes_still_unsupported(self):
        out = frag("doc.pdf", b"%PDF-1.4\n")
        self.assertEqual(out["status"], "UNSUPPORTED")


class IncrementalTests(unittest.TestCase):
    def test_changed_sources_detected(self):
        prev = {"a.js": "h1", "b.js": "h2"}
        now = {"a.js": "h1", "b.js": "h3", "c.ts": "h4"}
        changed = le.changed_sources(prev, now)
        self.assertEqual(changed["modified"], ["b.js"])
        self.assertEqual(changed["added"], ["c.ts"])
        self.assertEqual(changed["removed"], [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
