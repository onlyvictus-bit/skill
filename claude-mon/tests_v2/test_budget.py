#!/usr/bin/env python3
"""M4a: budgets are measured with stated methods or refused."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import budget  # noqa: E402


def profile(**over):
    base = {"schema_version": 2, "provider": "test", "model": "m-1",
            "encoding": "o200k_base", "encoding_version": "tiktoken-1",
            "context_limit": 1000, "output_limit": 200, "counting_method": "tiktoken"}
    base.update(over)
    return base


def words(text):
    return text.split()


class BudgetTests(unittest.TestCase):
    def test_valid_profile_accepted(self):
        self.assertEqual(budget.validate_profile(profile())["model"], "m-1")

    def test_unknown_limits_refused(self):
        with self.assertRaises(budget.BudgetError):
            budget.validate_profile(profile(context_limit=None))
        with self.assertRaises(budget.BudgetError):
            budget.validate_profile(profile(output_limit=0))
        with self.assertRaises(budget.BudgetError):
            budget.validate_profile(profile(encoding=""))

    def test_unknown_field_rejected(self):
        with self.assertRaises(budget.BudgetError):
            budget.validate_profile(profile(mb_to_tokens=4))

    def test_injected_counter_with_provenance(self):
        count, method = budget.count_tokens("a b c", "o200k_base", counter=words)
        self.assertEqual(count, 3)
        self.assertEqual(method, "injected-counter")

    def test_bogus_encoding_fails_closed(self):
        with self.assertRaises(budget.BudgetError):
            budget.count_tokens("hi", "definitely-not-an-encoding-xyz")

    def test_measure_request_breakdown(self):
        got = budget.measure_request(profile(), {"a": "x y", "b": "z"}, counter=words)
        self.assertEqual(got["input_tokens"], 3)
        self.assertEqual(got["breakdown"], {"a": 2, "b": 1})
        self.assertEqual(got["methods"], ["injected-counter"])

    def test_plan_single_batch(self):
        units = [{"id": "U1", "input_tokens": 100}, {"id": "U2", "input_tokens": 100}]
        got = budget.plan_batches(profile(), units, per_unit_output=50)
        self.assertEqual(got["batches"], [["U1", "U2"]])

    def test_plan_splits_on_input(self):
        units = [{"id": "U1", "input_tokens": 600}, {"id": "U2", "input_tokens": 600}]
        got = budget.plan_batches(profile(), units, per_unit_output=10)
        self.assertEqual(got["batches"], [["U1"], ["U2"]])

    def test_plan_splits_on_output(self):
        units = [{"id": "U1", "input_tokens": 10}, {"id": "U2", "input_tokens": 10}]
        got = budget.plan_batches(profile(context_limit=1000, output_limit=120),
                                  units, per_unit_output=100)
        self.assertEqual(got["batches"], [["U1"], ["U2"]])

    def test_exact_boundary_fits(self):
        units = [{"id": "U1", "input_tokens": 990}]
        got = budget.plan_batches(profile(), units, per_unit_output=10)
        self.assertEqual(got["batches"], [["U1"]])

    def test_total_plus_one_fails(self):
        units = [{"id": "U1", "input_tokens": 991}]
        with self.assertRaises(budget.BudgetError):
            budget.plan_batches(profile(), units, per_unit_output=10)

    def test_input_alone_at_limit_fails_with_reserve(self):
        units = [{"id": "U1", "input_tokens": 1000}]
        with self.assertRaises(budget.BudgetError):
            budget.plan_batches(profile(), units, per_unit_output=10)

    def test_oversize_unit_refused_not_truncated(self):
        units = [{"id": "U1", "input_tokens": 1001}]
        with self.assertRaises(budget.BudgetError):
            budget.plan_batches(profile(), units, per_unit_output=10)

    def test_safety_covering_context_refused(self):
        units = [{"id": "U1", "input_tokens": 10}]
        with self.assertRaises(budget.BudgetError):
            budget.plan_batches(profile(), units, per_unit_output=10, safety_reserve=1000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
