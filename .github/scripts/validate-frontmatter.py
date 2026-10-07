#!/usr/bin/env python3
"""Stdlib skill frontmatter validator (substitute for the PyYAML-based
official validator, which needs an unavailable third-party dependency).

Checks, per SKILL.md: opening/closing frontmatter fences, required name and
description fields, name matching the containing directory and the
lowercase-hyphen rule, description length bounds, no scaffold placeholders.
Exit 0 with a per-skill report; exit 1 listing violations. Read-only.
"""
import pathlib
import re
import sys

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PLACEHOLDERS = ("TODO", "FIXME", "CHANGEME", "<YOUR", "[YOUR")


def check(skill_md):
    errors = []
    text = pathlib.Path(skill_md).read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return ["missing opening frontmatter fence"]
    try:
        end = lines.index("---", 1)
    except ValueError:
        return ["missing closing frontmatter fence"]
    fields = {}
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            errors.append("line %d not a key/value mapping" % (number,))
            continue
        key = key.strip()
        if key in fields:
            errors.append("duplicate key %r (line %d)" % (key, number))
            continue
        fields[key] = value.strip()
    # Bracket balance is checked per physical line. For a quoted flow value
    # (value begins with ' or ") the quoted span is excluded from counting;
    # a value that opens a quote without closing it on the same line is an
    # error. Plain scalars may contain quotes freely. Multi-line quoted
    # strings are outside this YAML subset and are rejected as unterminated.
    unbalanced = None
    depth = {"[": 0, "{": 0}
    for line in lines[1:end]:
        body = line.split("#", 1)[0]
        _, _, value = body.partition(":")
        value = value.lstrip()
        if value[:1] in ("'", '"'):
            if len(value) < 2 or not value.endswith(value[0]):
                errors.append("unterminated quoted string: %s" % (line.strip(),))
                continue
            track = body.split(":", 1)[0]
        else:
            track = body
        for opener, closer in (("[", "]"), ("{", "}")):
            depth[opener] += track.count(opener) - track.count(closer)
            if depth[opener] < 0:
                unbalanced = opener + closer
                break
        if unbalanced is not None:
            break
    if unbalanced is None:
        if depth["["] != 0:
            unbalanced = "[]"
        elif depth["{"] != 0:
            unbalanced = "{}"
    if unbalanced is not None:
        errors.append("unbalanced %s in frontmatter" % (unbalanced,))
    name = fields.get("name", "")
    desc = fields.get("description", "")
    if pathlib.Path(skill_md).parent.name != name:
        errors.append("directory/name mismatch: %r" % (name,))
    if not (1 <= len(name) <= 64 and NAME_RE.match(name)):
        errors.append("bad name %r" % (name,))
    if not (1 <= len(desc) <= 1024):
        errors.append("description length %d out of bounds" % (len(desc),))
    upper = text.upper()
    hits = sorted({p for p in PLACEHOLDERS if p in upper})
    if hits:
        errors.append("scaffold placeholders: %s" % (",".join(hits),))
    return errors


def main(paths):
    failed = False
    for raw in paths:
        errors = check(raw)
        print("%s: %s" % (raw, "VALID" if not errors else errors))
        failed = failed or bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    roots = sys.argv[1:] or ["memory-integrity/SKILL.md", "claude-mon/SKILL.md"]
    sys.exit(main(roots))
