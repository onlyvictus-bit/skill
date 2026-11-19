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
  --per-unit-output N [--expect-task-digest T] [--counter-words]
python scripts/claude_mon_v2.py run --run-dir RUN --attempt-id A \
  --approval-ref R --provider NAME --model M --purpose WHY --max-output N \
  --script-file SCRIPT.json [--accept]
python scripts/claude_mon_v2.py resume|status|accept|verify|export|open-unit|query ...
```

`run` executes the TEST_ONLY scripted adapter only; its evidence class is
recorded on every response. There is no live dispatch path in this release:
`runner.dispatch_live()` raises, and no CLI flag enables it.

Preflight checks the work-item task through `--expect-task-digest`. It has no
stored task-spec identity before prepare: supplying `--task-spec-digest`, even
an empty value, returns `E_PREFLIGHT_TASK_SPEC_UNSUPPORTED` with exit 2 before
creating a run directory or reading inputs. Prepare still requires and binds
its own `--task-spec-digest` in the complete measured request.

Operational file, encoding and SQLite failures return one `ok:false` JSON
envelope with exit 2. The `cause` preserves exception type/message, available
OS/database fields, notes and causal chain. Existing check refusals retain exit
1; programming errors and interrupts are not converted into input failures.

Status meanings: attempt states follow the ledger machine
(QUEUED → … → ACCEPTED, plus terminal failures); `resume` converts
crash-orphaned DISPATCHING to DELIVERY_UNKNOWN and requeues undispatched
transients; receipts under `docs/fable/claude-mon/receipts/` are the v1
workflow and never satisfy v2 gates.
