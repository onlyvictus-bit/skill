#!/usr/bin/env python3
"""Eval harness self-tests: scorer passes the good transcript, fails the
bad one on every prompt, and rejects unknown prompt IDs."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import scorer  # noqa: E402


def load(name):
    prompts = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
    transcripts = json.loads((HERE / "samples" / name).read_text(encoding="utf-8"))
    return prompts, transcripts


class EvalTests(unittest.TestCase):
    def test_good_transcript_passes_all(self):
        results = scorer.score(*load("good.json"))
        self.assertEqual(len(results), 10)
        self.assertTrue(all(r["pass"] for r in results),
                        [r for r in results if not r["pass"]])

    def test_bad_transcript_fails_all(self):
        results = scorer.score(*load("bad.json"))
        self.assertEqual(len(results), 10)
        self.assertTrue(all(not r["pass"] for r in results))
        self.assertTrue(all(r["reasons"] for r in results))

    def test_unknown_prompt_rejected(self):
        prompts, _ = load("good.json")
        results = scorer.score(prompts, [{"prompt_id": "P99",
                                          "states": [], "tool_calls": [],
                                          "cites": []}])
        self.assertFalse(results[0]["pass"])

    def test_empty_evaluation_fails(self):
        prompts, _ = load("good.json")
        results = scorer.score(prompts, [])
        self.assertFalse(all(r["pass"] for r in results))
        self.assertTrue(any("without transcripts" in " ".join(r["reasons"])
                            for r in results))

    def test_partial_and_duplicate_coverage_fails(self):
        prompts, good = load("good.json")
        partial = scorer.score(prompts, good[:1])
        self.assertTrue(any(not r["pass"] for r in partial))
        duped = scorer.score(prompts, good[:1] * 10)
        self.assertTrue(any("duplicate transcript" in " ".join(r["reasons"])
                            for r in duped))

    def test_shell_wrapped_forbidden_call_caught(self):
        prompts, good = load("good.json")
        spoof = dict(good[0], tool_calls=["shell: bd accept --task X"])
        results = scorer.score(prompts, [spoof])
        self.assertFalse(results[0]["pass"])
        self.assertTrue(any("forbidden call accept" in r
                            for r in results[0]["reasons"]))

    def test_malformed_transcript_types_rejected(self):
        prompts, _ = load("good.json")
        results = scorer.score(prompts, [{"prompt_id": "P01-upload-means-read",
                                          "states": "UNVERIFIED",
                                          "tool_calls": [], "cites": []}])
        self.assertFalse(results[0]["pass"])

    def test_all_verbs_in_one_call_checked(self):
        prompts, good = load("good.json")
        multi = dict([t for t in good if t["prompt_id"] == "P03-foreign-approval"][0])
        multi["tool_calls"] = ["shell: bd accept; bd dispatch --task X"]
        results = scorer.score(prompts, [multi])
        self.assertFalse(results[0]["pass"])
        self.assertTrue(any("forbidden call dispatch" in r for r in results[0]["reasons"]))

    def test_nonstring_prompt_id_structured_fail(self):
        prompts, _ = load("good.json")
        results = scorer.score(prompts, [{"prompt_id": [],
                                          "states": [], "tool_calls": [], "cites": []}])
        self.assertFalse(results[0]["pass"])
        self.assertIn("prompt_id must be a string", results[0]["reasons"][0])

    def test_unregistered_cite_rejected(self):
        prompts, good = load("good.json")
        forged = dict(good[0])
        forged["cites"] = list(forged["cites"]) + ["trust-me-because-i-said-so"]
        results = scorer.score(prompts, [forged])
        self.assertFalse(results[0]["pass"])
        self.assertTrue(any("unregistered cite" in r for r in results[0]["reasons"]))


if __name__ == "__main__":
    unittest.main(verbosity=1)
