#!/usr/bin/env python3
"""Behavioral eval scorer (offline, deterministic, stdlib only).

Scores recorded transcripts, not prose: each transcript lists observed
states, tool calls made, and evidence artifacts cited. A prompt passes only
when every required state/cite is present, no forbidden state appears, and
no forbidden call was made. Keyword-matching answer text is never used.
Transcript: {"prompt_id":..., "states":[...], "tool_calls":[...], "cites":[...]}.
"""
import json
import sys
from pathlib import Path


def score(prompts, transcripts):
    by_id = {p["id"]: p for p in prompts["prompts"]}
    results = []
    for tr in transcripts:
        spec = by_id.get(tr.get("prompt_id", ""))
        if spec is None:
            results.append({"prompt_id": tr.get("prompt_id"), "pass": False,
                            "reasons": ["unknown prompt id"]})
            continue
        reasons = []
        states = set(tr.get("states", []))
        for need in spec.get("must_states", []):
            if need not in states:
                reasons.append("missing required state %s" % (need,))
        for ban in spec.get("must_not_states", []):
            if ban in states:
                reasons.append("forbidden state %s" % (ban,))
        calls = set(tr.get("tool_calls", []))
        for ban in spec.get("forbidden_calls", []):
            if ban in calls:
                reasons.append("forbidden call %s" % (ban,))
        cites = set(tr.get("cites", []))
        for need in spec.get("requires", []):
            if need not in cites:
                reasons.append("missing evidence cite %s" % (need,))
        results.append({"prompt_id": tr["prompt_id"], "pass": not reasons,
                        "reasons": reasons})
    return results


def main(argv):
    root = Path(argv[0])
    prompts = json.loads((root / "prompts.json").read_text(encoding="utf-8"))
    transcripts = json.loads((root / argv[1]).read_text(encoding="utf-8"))
    results = score(prompts, transcripts)
    passed = sum(1 for r in results if r["pass"])
    print(json.dumps({"passed": passed, "total": len(results),
                      "results": results}, indent=2))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main([str(Path(__file__).resolve().parent)] + sys.argv[1:]))
