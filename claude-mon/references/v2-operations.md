# v2 operations (claude-mon)

Exact commands, in order. Every command prints a JSON envelope; exit 0
means the query succeeded (not that the project is ready), exit 1 means a
check blocked or failed, exit 2 means broken invocation. `capabilities-v2.json`
at the package root declares the supported surface; anything absent from it
is unsupported in this release.

```text
python scripts/claude_mon_v2.py freeze --run-dir RUN --sources REL...
python scripts/claude_mon_v2.py prepare --run-dir RUN --work-item W \
  --task-digest T --units-file U.json --instructions-file I.txt \
  --schema-file S.json [--context-file C.json] --task-spec-digest D \
  --profile-file P.json [--source-id SID] [--counter-words]
python scripts/claude_mon_v2.py preflight --run-dir RUN --work-item W \
  --manifest-file M.json --source-file SRC --profile-file P.json \
  --per-unit-output N [--task-spec-digest D] [--counter-words]
python scripts/claude_mon_v2.py run --run-dir RUN --attempt-id A \
  --approval-ref R --provider NAME --model M --purpose WHY --max-output N \
  --script-file SCRIPT.json [--accept]
python scripts/claude_mon_v2.py resume|status|accept|verify|export|open-unit|query ...
```

`run` executes the TEST_ONLY scripted adapter only; its evidence class is
recorded on every response. There is no live dispatch path in this release:
`runner.dispatch_live()` raises, and no CLI flag enables it.

Status meanings: attempt states follow the ledger machine
(QUEUED → … → ACCEPTED, plus terminal failures); `resume` converts
crash-orphaned DISPATCHING to DELIVERY_UNKNOWN and requeues undispatched
transients; receipts under `docs/fable/claude-mon/receipts/` are the v1
workflow and never satisfy v2 gates.
