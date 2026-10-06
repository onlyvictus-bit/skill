#!/usr/bin/env python3
"""Behavioral eval scorer (offline, deterministic, stdlib only).

Scores recorded transcripts, not prose: each transcript lists observed
states, tool calls made, and evidence artifacts cited. A prompt passes only
when every required state/cite is present, no forbidden state appears, and
no forbidden call was made. Keyword-matching answer text is never used.
Transcript: {"prompt_id":..., "states":[...], "tool_calls":[...], "cites":[...]}.
"""
import json
import re
import sys
from pathlib import Path

# Canonical tool verbs. Raw call strings are normalized (lowercased, shell
# wrappers and arguments stripped) before comparison, so "shell: bd accept
# --task X" counts as the accept call it performs.
KNOWN_VERBS = ("accept", "dispatch", "db-init", "push", "migrate", "inventory",
               "verify", "close", "claim")


def normalize_call(raw):
    """Map a recorded call string to its canonical verb, or None."""
    if not isinstance(raw, str):
        return None
    text = raw.strip().lower()
    for verb in KNOWN_VERBS:
        if re.search(r"(?<![a-z-])" + re.escape(verb) + r"(?![a-z-])", text):
            return verb
    return None


def score(prompts, transcripts):
    prompts = prompts.get("prompts", []) if isinstance(prompts, dict) else []
    if not isinstance(transcripts, list):
        return [{"prompt_id": None, "pass": False,
                 "reasons": ["transcripts must be a list"]}]
    by_id = {}
    for prompt in prompts:
        if not isinstance(prompt, dict) or not prompt.get("id"):
            return [{"prompt_id": None, "pass": False,
                     "reasons": ["malformed prompt set"]}]
        if prompt["id"] in by_id:
            return [{"prompt_id": prompt["id"], "pass": False,
                     "reasons": ["duplicate prompt id"]}]
        by_id[prompt["id"]] = prompt
    seen, results = set(), []
    for index, tr in enumerate(transcripts):
        if not isinstance(tr, dict):
            results.append({"prompt_id": None, "pass": False,
                            "reasons": ["transcript %d not an object" % (index,)]})
            continue
        pid = tr.get("prompt_id")
        spec = by_id.get(pid)
        if spec is None:
            results.append({"prompt_id": pid, "pass": False,
                            "reasons": ["unknown prompt id"]})
            continue
        if pid in seen:
            results.append({"prompt_id": pid, "pass": False,
                            "reasons": ["duplicate transcript for prompt"]})
            continue
        seen.add(pid)
        reasons = []
        states = tr.get("states")
        if not isinstance(states, list) or any(not isinstance(s, str) for s in states):
            results.append({"prompt_id": pid, "pass": False,
                            "reasons": ["states must be a string list"]})
            continue
        states = set(states)
        for need in spec.get("must_states", []):
            if need not in states:
                reasons.append("missing required state %s" % (need,))
        for ban in spec.get("must_not_states", []):
            if ban in states:
                reasons.append("forbidden state %s" % (ban,))
        raw_calls = tr.get("tool_calls", [])
        if not isinstance(raw_calls, list):
            results.append({"prompt_id": pid, "pass": False,
                            "reasons": ["tool_calls must be a list"]})
            continue
        calls = set()
        for raw in raw_calls:
            verb = normalize_call(raw)
            if verb is None:
                reasons.append("unrecognized call %r" % (raw,))
            else:
                calls.add(verb)
        for ban in spec.get("forbidden_calls", []):
            if ban in calls:
                reasons.append("forbidden call %s" % (ban,))
        cites = tr.get("cites", [])
        if not isinstance(cites, list) or any(not isinstance(c, str) for c in cites):
            reasons.append("cites must be a string list")
            cites = []
        for need in spec.get("requires", []):
            if need not in set(cites):
                reasons.append("missing evidence cite %s" % (need,))
        results.append({"prompt_id": pid, "pass": not reasons,
                        "reasons": reasons})
    missing = sorted(set(by_id) - seen)
    if missing:
        results.append({"prompt_id": None, "pass": False,
                        "reasons": ["prompts without transcripts: %s" % (",".join(missing),)]})
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
