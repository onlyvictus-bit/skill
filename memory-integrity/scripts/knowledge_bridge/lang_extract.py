#!/usr/bin/env python3
"""Phase 3: structural JS/TS extraction with explicit unknown states.

Dispatches .py to the unchanged Python extractor, parses JS/TS with a
length-preserving masked scan (all match offsets are exact source bytes),
and leaves every other suffix on the original UNSUPPORTED path. Dynamic
imports, unresolved calls, shadowed bindings and anonymous defaults never
become edges: they become diagnostics. Standard library only.
"""
import re

from . import extraction as _py

JS_SUFFIXES = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")
IDENT = r"[A-Za-z_$][\w$]*"


def _mask(text):
    """Blank comments with spaces (offsets preserved) and record string spans.

    Strings stay intact so specifiers remain capturable; every structural
    match must be checked against the string spans. Template-literal
    interpolations are treated as string content (documented limit).
    Returns (comment_blanked_text, [(start, end), ...]).
    """
    out = list(text)
    spans = []
    i, n = 0, len(text)
    state = None
    while i < n:
        ch = text[i]
        two = text[i:i + 2]
        if state is None:
            if two == "//":
                state = "line"
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if two == "/*":
                state = "block"
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if ch in ("'", '"', "`"):
                state = ("quote", ch, i)
                i += 1
                continue
            i += 1
        elif state == "line":
            if ch == "\n":
                state = None
                i += 1
            else:
                out[i] = " "
                i += 1
        elif state == "block":
            if two == "*/":
                out[i] = out[i + 1] = " "
                state = None
                i += 2
            else:
                if ch != "\n":
                    out[i] = " "
                i += 1
        else:
            _, quote, start = state
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == quote:
                spans.append((start, i + 1))
                state = None
            i += 1
    return "".join(out), spans


def _inside(pos, spans):
    return any(start <= pos < end for start, end in spans)


def _refs(source_id, source, span):
    try:
        return _py._refs(source_id, source, span)
    except (ValueError, KeyError):
        return [{"source_id": source_id}]


def _split_names(blob):
    names = []
    for part in blob.split(","):
        part = part.strip()
        if not part:
            continue
        bits = [b.strip() for b in part.split(" as ")]
        if len(bits) == 2 and bits[0] and bits[1]:
            names.append((bits[0], bits[1]))
        elif len(bits) == 1 and re.fullmatch(IDENT, bits[0]):
            names.append((bits[0], bits[0]))
    return names


def _parse_js(source_id, source, raw, repository, path):
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    masked, spans = _mask(text)
    flat = masked.replace("\n", " ")
    module = _py._module(path)
    component = "component:" + module

    def hits(pattern):
        for match in re.finditer(pattern, flat):
            if not _inside(match.start(), spans):
                yield match
    imports, exports, symbols, calls, edges, diagnostics = [], [], [], [], [], []

    def diag(kind, start, end, detail):
        diagnostics.append({"kind": kind, "source_id": source_id,
                            "range": [start, end], "detail": detail})

    def imp(kind, name, frm, start, end, type_only=False):
        imports.append({"kind": kind, "name": name, "module": frm,
                        "binding": name, "range": [start, end],
                        "type_only": type_only})

    for match in hits(r"\bimport\s+type\s*\{([^}]*)\}\s*from\s*(['\"])(.*?)\2"):
        for original, alias in _split_names(match.group(1)):
            imp("type-only", alias, match.group(3), match.start(), match.end(), True)
    for match in hits(r"\bimport\s*\{([^}]*)\}\s*from\s*(['\"])(.*?)\2"):
        if re.match(r"\s*type\b", match.group(0)[6:]):
            continue
        for original, alias in _split_names(match.group(1)):
            imp("named", alias, match.group(3), match.start(), match.end())
    for match in hits(r"\bimport\s+(?!(?:type\b|\{|\*))([A-Za-z_$][\w$]*)\s+from\s*(['\"])(.*?)\2"):
        imp("default", match.group(1), match.group(3), match.start(), match.end())
    for match in hits(r"\bimport\s*\*\s*as\s+([A-Za-z_$][\w$]*)\s*from\s*(['\"])(.*?)\2"):
        imp("namespace", match.group(1), match.group(3), match.start(), match.end())
    for match in hits(r"\bimport\s*(['\"])(.*?)\1"):
        head = flat[max(0, match.start() - 8):match.start()]
        if re.search(r"(from|import\s*\()\s*$", head):
            continue
        imp("side-effect", None, match.group(2), match.start(), match.end())
    for match in hits(r"\bimport\s*\("):
        diag("DYNAMIC_BINDING", match.start(), match.end() + 1,
             "dynamic import call is not statically resolvable")
    for match in hits(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*require\(\s*(['\"])(.*?)\2\s*\)"):
        imp("require", match.group(1), match.group(3), match.start(), match.end())
    for match in hits(r"(?:const|let|var)\s*\{([^}]*)\}\s*=\s*require\(\s*(['\"])(.*?)\2\s*\)"):
        for original, alias in _split_names(match.group(1)):
            imp("require", alias, match.group(3), match.start(), match.end())

    def exp(name, start, end, kind, default=False):
        exports.append({"name": name, "range": [start, end], "kind": kind,
                        "default": default})

    for match in hits(r"\bexport\s+type\s*\{([^}]*)\}(?:\s*from\s*(['\"])(.*?)\2)?"):
        for original, alias in _split_names(match.group(1)):
            exp(alias, match.start(), match.end(), "type-only")
        if match.group(3):
            edges.append({"predicate": "REEXPORTS", "subject": component,
                          "object": match.group(3),
                          "source_units": _refs(source_id, source,
                                                [match.start(), match.end()])})
    for match in hits(r"\bexport\s*\{([^}]*)\}\s*from\s*(['\"])(.*?)\2"):
        edges.append({"predicate": "REEXPORTS", "subject": component,
                      "object": match.group(3),
                      "source_units": _refs(source_id, source,
                                            [match.start(), match.end()])})
    for match in hits(r"\bexport\s*\*\s*as\s+([A-Za-z_$][\w$]*)\s*from\s*(['\"])(.*?)\2"):
        exp(match.group(1), match.start(), match.end(), "namespace-reexport")
        edges.append({"predicate": "REEXPORTS", "subject": component,
                      "object": match.group(3),
                      "source_units": _refs(source_id, source,
                                            [match.start(), match.end()])})
    for match in hits(r"\bexport\s*\*\s*from\s*(['\"])(.*?)\1"):
        edges.append({"predicate": "REEXPORTS", "subject": component,
                      "object": match.group(2),
                      "source_units": _refs(source_id, source,
                                            [match.start(), match.end()])})
    for match in hits(
            r"\bexport\s+(default\s+)?(async\s+)?(function\*?|class)\s+([A-Za-z_$][\w$]*)?"):
        name = match.group(4)
        if name:
            exp(name, match.start(), match.end(), match.group(3).strip(),
                bool(match.group(1)))
            symbols.append({"id": module + "." + name, "name": name,
                            "qualified_name": module + "." + name,
                            "range": [match.start(), match.end()],
                            "kind": "symbol", "scope": ""})
        else:
            exp(None, match.start(), match.end(), "default-anonymous", True)
            diag("DYNAMIC_BINDING", match.start(), match.end(),
                 "anonymous default export has no static symbol")
    for match in hits(
            r"\bexport\s+(?:default\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)"):
        exp(match.group(1), match.start(), match.end(), "var")
        symbols.append({"id": module + "." + match.group(1), "name": match.group(1),
                        "qualified_name": module + "." + match.group(1),
                        "range": [match.start(), match.end()],
                        "kind": "symbol", "scope": ""})
    for match in hits(r"\bmodule\.exports\s*=|\bexports\.([A-Za-z_$][\w$]*)\s*="):
        exp(match.group(1) or "module.exports", match.start(), match.end(), "commonjs")
    for match in hits(r"\b(?:namespace|module)\s+([A-Za-z_$][\w$]*)\s*\{"):
        symbols.append({"id": module + "." + match.group(1), "name": match.group(1),
                        "qualified_name": module + "." + match.group(1),
                        "range": [match.start(), match.end()],
                        "kind": "namespace", "scope": ""})
    for match in hits(r"\binterface\s+([A-Za-z_$][\w$]*)"):
        symbols.append({"id": module + "." + match.group(1), "name": match.group(1),
                        "qualified_name": module + "." + match.group(1),
                        "range": [match.start(), match.end()],
                        "kind": "interface", "scope": ""})

    bound = {}
    for entry in imports:
        if entry["name"]:
            bound.setdefault(entry["name"], []).append(("import", entry))
    for symbol in symbols:
        if symbol["kind"] == "symbol":
            bound.setdefault(symbol["name"], []).append(("symbol", symbol))
    scopes = {"": {"bindings": {name: [name] for name in bound}, "parent": None}}

    def _enclosing_block_start(pos):
        depth = 0
        for i in range(pos - 1, -1, -1):
            if flat[i] == "}":
                depth += 1
            elif flat[i] == "{":
                if depth == 0:
                    return i
                depth -= 1
        return -1

    def _rebound_before(head, pos):
        block = _enclosing_block_start(pos)
        if block < 0:
            return False
        region = flat[block:pos]
        pattern = r"\b(?:let|const|var|function)\s+" + re.escape(head) + r"(?![\w$])"
        return any(not _inside(block + match.start(), spans)
                   for match in re.finditer(pattern, region))

    keywords = {"if", "for", "while", "switch", "catch", "function", "class",
                "import", "export", "return", "typeof", "new", "else", "do"}
    for match in hits(r"([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\("):
        callee = match.group(1)
        head = callee.split(".")[0]
        if head in keywords:
            continue
        precede = flat[max(0, match.start() - 9):match.start()]
        if re.search(r"\bfunction\s*$|\bclass\s*$", precede):
            continue
        start, end = match.start(), match.end()
        candidates = bound.get(head, [])
        if candidates and _rebound_before(head, start):
            diag("DYNAMIC_BINDING", start, end,
                 "locally rebound name %r not resolved to import" % (head,))
            calls.append({"callee": head, "range": [start, end], "scope": "",
                          "subject": component, "resolved": False})
            continue
        if candidates:
            calls.append({"callee": head, "range": [start, end], "scope": "",
                          "subject": component, "resolved": True})
        else:
            diag("UNRESOLVED_CALL", start, end, "callee %r unbound" % (callee,))
            calls.append({"callee": head, "range": [start, end], "scope": "",
                          "subject": component, "resolved": False})
    return {"status": "OBSERVED", "module": module, "component": component,
            "nodes": [], "symbols": symbols, "edges": edges, "imports": imports,
            "exports": exports, "calls": calls, "mutations": [], "scopes": scopes,
            "diagnostics": diagnostics}


def extract_fragment(source_id, source, raw, repository):
    """Dispatch by suffix: Python unchanged, JS/TS structural, else UNSUPPORTED."""
    path = source.get("path", "")
    lowered = path.lower()
    if lowered.endswith(".py"):
        return _py._fragment(source_id, source, raw, repository)
    if lowered.endswith(JS_SUFFIXES):
        if isinstance(raw, bytes):
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                return {"status": "FAILED", "module": _py._module(path), "component": None,
                        "nodes": [], "symbols": [], "edges": [], "imports": [], "calls": [],
                        "mutations": [], "scopes": {},
                        "diagnostics": [{"kind": "PARSE_FAILED", "source_id": source_id,
                                         "range": [0, len(raw)], "detail": str(exc)}]}
        return _parse_js(source_id, source, raw, repository, path)
    out = _py._fragment(source_id, source, raw, repository)
    out.setdefault("exports", [])
    return out


def changed_sources(previous, current):
    """Generation-aware change set between {name: digest} snapshots."""
    previous = dict(previous or {})
    current = dict(current or {})
    return {"added": sorted(n for n in current if n not in previous),
            "removed": sorted(n for n in previous if n not in current),
            "modified": sorted(n for n in current
                               if n in previous and previous[n] != current[n])}
