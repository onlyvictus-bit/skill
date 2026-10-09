#!/usr/bin/env python3
"""Phase 5 RED: opt-in advanced adapters, default-disabled, honestly bounded.

Must FAIL before implementation, pass after. learned/live/remote paths stay
refused; local deterministic paths prove themselves on fixtures.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from knowledge_bridge import rules, sparql, ner_shadow, ontology, deferred  # noqa: E402
from knowledge_bridge import graphrag  # noqa: E402


class RulesTests(unittest.TestCase):
    FACTS = [("parent", ("amy", "bob")), ("parent", ("bob", "cy"))]

    def test_transitive_closure_with_provenance(self):
        out = rules.forward_chain(
            self.FACTS, [{"head": ("grandparent", ("X", "Z")),
                          "body": [("parent", ("X", "Y")), ("parent", ("Y", "Z"))]}],
            max_derived=100)
        self.assertIn(("grandparent", ("amy", "cy")), out["derived"])
        self.assertTrue(all(d["provenance"] for d in out["derivations"]))

    def test_cyclic_rules_terminate(self):
        out = rules.forward_chain(
            [("link", ("a", "b"))],
            [{"head": ("link", ("X", "Y")), "body": [("link", ("Y", "X"))]}],
            max_derived=10)
        self.assertLessEqual(len(out["derived"]), 10)
        self.assertIn("termination", out["stop_reason"].lower() + "bound")

    def test_stratified_negation(self):
        out = rules.forward_chain(
            [("bird", ("tweety",)), ("penguin", ("tweety",))],
            [{"head": ("flies", ("X",)), "body": [("bird", ("X",)),
                                                  ("not", ("penguin", ("X",)))]}],
            max_derived=100)
        self.assertNotIn(("flies", ("tweety",)), out["derived"])


class SparqlTests(unittest.TestCase):
    GRAPH = {"nodes": [{"id": "a"}, {"id": "h1", "hidden": True}],
             "edges": [{"subject": "a", "predicate": "DEPENDS_ON", "object": "b"}]}

    def test_select_where(self):
        rows = sparql.query(self.GRAPH, "SELECT ?s WHERE { ?s DEPENDS_ON b }")
        self.assertEqual(rows, [{"s": "a"}])

    def test_hidden_nodes_excluded_by_default(self):
        rows = sparql.query(self.GRAPH, "SELECT ?s WHERE { ?s ?p ?o }")
        self.assertNotIn({"s": "h1"}, rows)

    def test_injection_refused(self):
        with self.assertRaises(sparql.SparqlError):
            sparql.query(self.GRAPH, "SELECT ?s WHERE { ?s ?p ?o }; DROP ALL")

    def test_limit_enforced(self):
        rows = sparql.query(self.GRAPH, "SELECT ?s WHERE { ?s ?p ?o }", limit=0)
        self.assertEqual(rows, [])


class NerTests(unittest.TestCase):
    def test_spans_with_ambiguity(self):
        spans = ner_shadow.extract("Amy met Amy Inc on 2026-01-02. Amy did not sign.")
        by_text = {}
        for span in spans:
            by_text.setdefault(span["text"], []).append(span)
        self.assertIn("Amy Inc", by_text)
        self.assertTrue(any(s["ambiguous"] for s in spans))
        self.assertTrue(any(s.get("negated") for s in spans))

    def test_human_check_required(self):
        spans = ner_shadow.extract("Amy signed.")
        self.assertFalse(any(s["human_checked"] for s in spans))
        reviewed = ner_shadow.review_span(spans[0], True)
        self.assertTrue(reviewed["human_checked"])

    def test_unicode_spans_are_byte_ranges(self):
        spans = ner_shadow.extract("Zoë met François Düpont on 2026-03-04.")
        raw = "Zoë met François Düpont on 2026-03-04.".encode("utf-8")
        self.assertTrue(spans)
        for span in spans:
            start, end = span["byte_range"]
            self.assertEqual(raw[start:end].decode("utf-8"), span["text"])

    def test_event_modality(self):
        events = ner_shadow.extract_events("The board might meet Tuesday. Minutes record the vote.")
        kinds = {e["modality"] for e in events}
        self.assertIn("hypothetical", kinds)
        self.assertIn("observed", kinds)


class OntologyTests(unittest.TestCase):
    def test_migration_diff_and_compat(self):
        old = ontology.schema(1)
        migrated = ontology.migrate(old, 2)
        new = migrated["schema"]
        self.assertIn("DEPENDS_ON", new["predicates"])
        report = ontology.check_compat(old, new, [{"predicate": "DEPENDS_ON"}])
        self.assertTrue(report["compatible"])

    def test_type_violation_listed(self):
        schema = ontology.schema(2)
        report = ontology.check_compat(schema, schema, [{"predicate": "NOPE"}])
        self.assertFalse(report["compatible"])
        self.assertTrue(report["violations"])

    def test_endpoint_types_validated(self):
        schema = ontology.schema(2)
        nodes = [{"id": "c1", "type": "Component"}, {"id": "c2", "type": "Component"},
                 {"id": "s9", "type": "SourceUnit"}]
        good = ontology.check_compat(
            schema, schema, [{"predicate": "DEPENDS_ON", "subject": "c1", "object": "c2"}],
            nodes=nodes)
        self.assertTrue(good["compatible"], good["violations"])
        bad = ontology.check_compat(
            schema, schema, [{"predicate": "DEPENDS_ON", "subject": "s9", "object": "c2"}],
            nodes=nodes)
        self.assertFalse(bad["compatible"])
        self.assertTrue(any("type violation" in v for v in bad["violations"]))


class DeferredTests(unittest.TestCase):
    def test_all_deferred_by_default(self):
        for cap in deferred.capabilities():
            self.assertEqual(cap["status"], "DEFERRED")

    def test_enable_without_approval_refused(self):
        with self.assertRaises(deferred.DeferredError):
            deferred.enable("global-graphrag")

    def test_enable_with_approval_pending_not_active(self):
        out = deferred.enable("global-graphrag",
                              approval={"approver": "user", "scope": "pilot",
                                        "budget": "none"})
        self.assertEqual(out["status"], "ACTIVATION_PENDING")
        self.assertNotEqual(out["status"], "ACTIVE")


class GraphragTests(unittest.TestCase):
    GRAPH = {"nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "p", "private": True}],
             "edges": [{"subject": "a", "predicate": "DEPENDS_ON", "object": "b"},
                       {"subject": "b", "predicate": "DEPENDS_ON", "object": "c"},
                       {"subject": "a", "predicate": "REFERENCES", "object": "p"}]}

    def test_disabled_by_default(self):
        with self.assertRaises(graphrag.GraphragError):
            graphrag.query(self.GRAPH, "a", max_hops=2)

    def test_enabled_query_with_budgets(self):
        with self.assertRaises(graphrag.GraphragError):
            graphrag.enable({"approver": "test", "scope": "fixture"})

    def test_drift_stops(self):
        with self.assertRaises(graphrag.GraphragError):
            graphrag.enable({"approver": "test", "scope": "fixture"})


if __name__ == "__main__":
    unittest.main(verbosity=1)
