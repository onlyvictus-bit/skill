import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "context_budget.py"
spec = importlib.util.spec_from_file_location("context_budget", SCRIPT)
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)


class FakeEncoding:
    name = "fake"
    def encode(self, text):
        return list(text.encode("utf-8"))


class FakeTiktoken:
    __version__ = "test"
    def encoding_for_model(self, model):
        if model == "known":
            return FakeEncoding()
        raise KeyError(model)
    def get_encoding(self, name):
        if name == "fake":
            return FakeEncoding()
        raise ValueError(name)


class ContextBudgetTests(unittest.TestCase):
    def test_calculate_input_budget_reserves_output_and_overhead(self):
        self.assertEqual(700, cb.calculate_input_budget(1000, 200, 75, 25))
        with self.assertRaises(ValueError):
            cb.calculate_input_budget(100, 90, 20, 0)

    def test_unknown_model_fails_closed_without_explicit_encoding(self):
        old = cb.tiktoken
        cb.tiktoken = FakeTiktoken()
        try:
            with self.assertRaisesRegex(KeyError, "explicit encoding"):
                cb.resolve_encoding(model="mystery-model", explicit_encoding=None)
        finally:
            cb.tiktoken = old

    def test_explicit_encoding_is_deterministic_and_fit_is_stable(self):
        old = cb.tiktoken
        cb.tiktoken = FakeTiktoken()
        try:
            enc = cb.resolve_encoding(model=None, explicit_encoding="fake")
            self.assertEqual(3, cb.count_tokens("abc", enc))
            candidates = [
                {"id": "b", "priority": 1, "text": "22"},
                {"id": "a", "priority": 2, "text": "111"},
                {"id": "c", "priority": 1, "text": "3333"},
            ]
            fitted = cb.fit_candidates(candidates, budget=5, encoding=enc)
            self.assertEqual(["a", "b"], [x["id"] for x in fitted["selected"]])
            self.assertEqual(["c"], [x["id"] for x in fitted["skipped"]])
            self.assertEqual(5, fitted["used_tokens"])
        finally:
            cb.tiktoken = old


if __name__ == "__main__":
    unittest.main()
