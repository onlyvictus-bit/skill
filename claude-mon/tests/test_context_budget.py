import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from context_budget import BudgetError, schedule_batches  # noqa: E402


class ContextBudgetTests(unittest.TestCase):
    def test_batches_preserve_order_and_include_every_required_item(self):
        items = [("C1", 30), ("C2", 40), ("C3", 20), ("C4", 45)]
        batches = schedule_batches(items, context_limit=100, reserved_output_tokens=20, fixed_overhead_tokens=10)
        flat = [item for batch in batches for item in batch]
        self.assertEqual(flat, ["C1", "C2", "C3", "C4"])
        counts = dict(items)
        for batch in batches:
            self.assertLessEqual(sum(counts[x] for x in batch), 70)

    def test_oversize_required_item_fails_instead_of_truncating(self):
        with self.assertRaises(BudgetError):
            schedule_batches([("C1", 81)], context_limit=100, reserved_output_tokens=20)

    def test_invalid_budget_fails_closed(self):
        with self.assertRaises(BudgetError):
            schedule_batches([("C1", 1)], context_limit=100, reserved_output_tokens=90, fixed_overhead_tokens=10)


if __name__ == "__main__":
    unittest.main()
