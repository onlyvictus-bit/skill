#!/usr/bin/env python3
"""M5: strict unit challenges and declared-dependency reconciliation.

Deterministic checks only: number presence, negation-marker handling, and
registry-declared definition/dependency/conflict reconciliation. Findings
are evidence for review, never a proof of understanding; unresolved required
findings block strict readiness. Same-model self-review is labeled
correlated, never independent.
"""
import re

NEGATION_MARKERS_EN = ("must not", "mustn't", "cannot", "can't", "never", "not ",
                       "n't ", "except", "unless", "only if", "prohibited",
                       "forbidden", "no ", "without ")

# Narrow contrast pairs: original asserts the negative pole while the
# interpretation asserts the positive pole without the condition. Heuristic
# only — absence of a finding never proves semantic equivalence.
CONTRAST_PAIRS = (("never", "always"), ("cannot", "can "), ("can't", "can "),
                  ("must not", "must "), ("prohibited", "allowed"),
                  ("forbidden", "allowed"), ("without ", "with "))

NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


class SemanticError(ValueError):
    pass


def numbers_in(text):
    return NUMBER_RE.findall(text or "")


def challenge_unit(unit_id, original, interpretation, markers=NEGATION_MARKERS_EN,
                   reviewer="unreviewed"):
    """Challenge one interpretation against its original. Returns a report."""
    if not isinstance(original, str) or not original.strip():
        raise SemanticError("E_CHALLENGE_ORIGINAL: unit %s has no original" % (unit_id,))
    if not isinstance(interpretation, str) or not interpretation.strip():
        return {"unit_id": unit_id, "reviewer": reviewer,
                "findings": [{"check": "nonempty", "status": "unresolved",
                              "detail": "empty interpretation"}],
                "unresolved": ["nonempty"]}
    findings, unresolved = [], []
    lowered_original = original.lower()
    lowered_result = interpretation.lower()
    for number in dict.fromkeys(numbers_in(original)):
        if number not in numbers_in(interpretation):
            findings.append({"check": "numbers", "status": "unresolved",
                             "detail": "value %s absent from interpretation" % (number,)})
            unresolved.append("numbers:%s" % (number,))
    used_markers = [m for m in markers if m in lowered_original]
    if used_markers and not any(m in lowered_result for m in markers):
        findings.append({"check": "negation", "status": "unresolved",
                         "detail": "original conditions %s unaddressed"
                                   % (sorted(set(used_markers)),)})
        unresolved.append("negation")
    for neg, pos in CONTRAST_PAIRS:
        if neg in lowered_original and neg not in lowered_result \
                and pos in lowered_result:
            findings.append({"check": "negation-contrast", "status": "unresolved",
                             "detail": "original asserts %r but interpretation asserts %r"
                                       % (neg.strip(), pos.strip())})
            unresolved.append("negation-contrast:%s" % (neg.strip(),))
            break
    return {"unit_id": unit_id, "reviewer": reviewer, "findings": findings,
            "unresolved": sorted(set(unresolved))}


def strict_ready(reports, *, expected_ids=None, source_digest=None, task_digest=None):
    """True only when a declared non-empty review has no unresolved findings.

    An empty or malformed review is UNVERIFIED work, never a pass.
    """
    if not isinstance(reports, list) or not reports:
        return False, [("scope", ["empty-review"])]
    blockers = []
    seen = set()
    expected = None if expected_ids is None else list(expected_ids)
    if expected is not None and (not expected or len(set(expected)) != len(expected)):
        return False, [("scope", ["invalid-expected-set"])]
    for idx, report in enumerate(reports):
        if not isinstance(report, dict) or not report.get("unit_id") \
                or not isinstance(report.get("unresolved"), list):
            label = report.get("unit_id", "report-%d" % (idx,)) \
                if isinstance(report, dict) else "report-%d" % (idx,)
            blockers.append((label, ["malformed-report"]))
        else:
            ident = report["unit_id"]
            seen.add(ident)
            malformed = []
            if not isinstance(report.get("reviewer"), str) or not report["reviewer"].strip():
                malformed.append("reviewer")
            if not isinstance(report.get("findings"), list):
                malformed.append("findings")
            if source_digest is not None and report.get("source_digest") != source_digest:
                malformed.append("source-binding")
            if task_digest is not None and report.get("task_digest") != task_digest:
                malformed.append("task-binding")
            if malformed:
                blockers.append((ident, malformed))
            elif report["unresolved"]:
                blockers.append((ident, report["unresolved"]))
    if expected is not None:
        missing = sorted(set(expected) - seen)
        foreign = sorted(seen - set(expected))
        if missing:
            blockers.append(("scope", ["missing:" + ",".join(missing)]))
        if foreign:
            blockers.append(("scope", ["foreign:" + ",".join(foreign)]))
    return (not blockers), blockers


def reconcile_dependencies(results_by_id, dependencies):
    """Validate declared definition/reference/conflict edges mechanically.

    dependencies: [{id, requires:[unit_ids], conflicts_with:[unit_ids]}].
    A conflict whose both sides are marked resolved is flagged; a requires
    edge to a missing or unresolved unit is flagged. Returns findings.
    """
    findings = []
    for edge in dependencies:
        ident = edge.get("id", "?")
        for need in edge.get("requires", []):
            target = results_by_id.get(need)
            if target is None:
                findings.append({"edge": ident, "status": "unresolved",
                                 "detail": "requires missing unit %s" % (need,)})
            elif target.get("disposition") != "resolved":
                findings.append({"edge": ident, "status": "unresolved",
                                 "detail": "requires unresolved unit %s" % (need,)})
        foes = [u for u in edge.get("conflicts_with", [])
                if results_by_id.get(u, {}).get("disposition") == "resolved"
                and results_by_id.get(ident, {}).get("disposition") == "resolved"]
        if foes:
            findings.append({"edge": ident, "status": "unresolved",
                             "detail": "resolved conflict with %s" % (sorted(foes),)})
    return findings
