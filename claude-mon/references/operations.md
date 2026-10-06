# Operations and verification

## Minimal walking skeleton

```bash
ROOT=/path/to/project
CM=/path/to/claude-mon
TASK=$ROOT/task-spec.txt

python $CM/scripts/claude_mon.py register --project "$ROOT" --source "$ROOT/requirements.md" --kind text
python $CM/scripts/claude_mon.py unitize --project "$ROOT" --source-id SRC-...
python $CM/scripts/claude_mon.py chunk --project "$ROOT" --source-id SRC-...
python $CM/scripts/claude_mon.py verify --project "$ROOT" --source-id SRC-...
python $CM/scripts/claude_mon.py payload --project "$ROOT" --source-id SRC-... --chunk-id C00000001
```

Process every chunk using the same task spec. Save outcomes as JSON, then:

```bash
python $CM/scripts/claude_mon.py receipt \
  --project "$ROOT" \
  --source-id SRC-... \
  --task-spec-file "$TASK" \
  --processor actual-model-or-tool \
  --outcomes-file outcomes.json

python $CM/scripts/fable_bridge.py --project "$ROOT" --task-spec-file "$TASK"
```

## Fable composition

Claude Mon must not patch Fable requirements/plan/tests schemas to smuggle source coverage into unknown fields. Compose the existing guard:

```bash
python $CM/scripts/fable_bridge.py \
  --project "$ROOT" \
  --task-spec-file "$TASK" \
  --fable-guard /path/to/fable_guard.py \
  --fable-gate execute
```

The bridge stops immediately if Fable's selected gate fails, then checks current task-bound source receipts.

Use `--source-id` repeatedly when a proof unit needs only a specific source subset. Without it, all registry sources marked `required=true` are checked.

## Token batching

`context_budget.schedule_batches()` consumes `(chunk_id, token_count)` pairs and an explicit context limit/reserved output/fixed overhead. It preserves order and includes every item.

If a chunk exceeds usable context, rebuild chunks smaller or use a processor with a sufficient context limit. Do not slice the payload after hashing and still record the original chunk as successful.

## Failure injection

Before trusting a workflow, test these cases:

1. Delete one primary unit from a copied chunk manifest -> verification reports missing coverage.
2. Duplicate one primary unit -> verification reports duplicate-primary coverage.
3. Change source bytes after a receipt -> receipt verifies as `STALE` without rewriting history.
4. Mark one chunk `truncated` -> aggregate receipt is `TRUNCATED` even if other chunks are `ok`.
5. Omit an expected chunk -> aggregate receipt is `PARTIAL`.
6. Omit or supply a wrong `input_sha256` for an `ok`/`truncated` outcome -> outcome becomes an integrity error.
7. Change the task spec -> prior receipts cannot satisfy the new task gate.

## Large-file check

The bundled check generates a 50 MiB UTF-8 source and verifies source hashing, unit coverage, chunk coverage, and manifest counts:

```bash
python tests/large_50mb_check.py
```

This is a representative verification, not a promise that every arbitrarily large source fits RAM. Source bytes are streamed; current metadata verification/chunk planning scales with unit count.

## Recovery

If interrupted before receipt creation, regenerate/verify manifests and continue missing chunks. If the source changed, re-register first and process the new source version. Never merge outcomes from different source/task/manifest bases into one `COMPLETE` receipt.

## Cleanup

`.claude-mon/cache/` is reproducible and can be deleted after receipts/evidence are no longer needed for active work, then regenerated from unchanged source bytes. Do not delete `docs/fable/claude-mon/receipts/runs/` when audit history is required.

## Troubleshooting

- `SOURCE_HASH_MISMATCH`: source changed after registration; re-register and rebuild.
- `UNIT_MANIFEST_DIGEST_MISMATCH`: cache file changed/corrupted; regenerate units from registered source.
- `CHUNK_MANIFEST_DIGEST_MISMATCH`: regenerate chunks from the verified unit manifest.
- `TASK_SPEC_MISMATCH`: use a receipt generated for the exact current task spec.
- `NO_COMPLETE_RECEIPT`: process all expected chunks or resolve error/truncation/staleness.
- optional dependency unavailable: continue core coverage or obtain explicit authorization to install/use the named adapter; never silently substitute approximate behavior.
