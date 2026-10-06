# v2 operations (memory-integrity)

```text
python scripts/memory_integrity_v2.py capabilities --claude-mon-root <engine>
python scripts/memory_integrity_v2.py audit --claude-mon-root <engine> \
  --scope-file S.json --source-dir D --manifest-dir M
python scripts/memory_integrity_v2.py report --layers-file L.json [--reasons-file R.json]
python scripts/memory_integrity_v2.py watchdog --canary TEXT [--scope S]
```

`audit` verdicts: READY (exit 0), STALE/BLOCKED (exit 1) with named
findings. `report` overall is READY_FOR_DECLARED_TASK only when every
required layer is READY; counts never override a missing layer.
`watchdog` runs the strict round-trip on an in-process TEST_ONLY backend;
a live AgentMemory service needs a running server plus its own approval
boundary and is not configured here.

The companion engine is always an explicit path. A digest mismatch fails
closed with recovery instructions; there is no automatic re-pinning.
