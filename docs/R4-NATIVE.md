# R4 native-read candidate

This branch contains a real read-only adapter and public `native-observe` route.
It is not a qualified native execution profile or a finished successor release.
The exact R3 release assets remain available separately under `release/` and on
`main`; the inherited package content manifest intentionally detects R4 drift.

From the repository root, inspect the command before selecting a runtime:

```powershell
python -B memory-integrity/scripts/memory_integrity_workflow.py native-observe --help
```

The executable invocation requires these explicit inputs:

- `--claude-mon-root`: this checkout's matching companion directory.
- `--selection-file`: an exact selection object for the user's own executable,
  project and embedded database. It is not a credential file.
- `--receipt`: an absolute, new destination in an existing ordinary directory.

The selection schema is [NativeSelection](../memory-integrity/scripts/hybrid_bridge/native.py).
All fields must be present in the selection JSON, including `expected_project_id`,
`expected_database_name` and `expected_prefix`. Use actual observed identities and
hashes, not placeholders or the archive checksum in place of the executable hash.
The native observer is pinned to the declared v1.3.1 release/commit contract.
Do not download, initialize or mutate a database solely because this document
exists; those actions need their own authority and qualified runtime checks.

See the [native observation contract](../memory-integrity/references/m7-native-observation.md)
for supported dependency types, repeated-read drift detection, exact-byte
diagnostic retention, timeout/output limits and current process-tree limits.

A successful read remains `NATIVE_OBSERVED_UNQUALIFIED`, `active=false` and
`native_beads_qualified=false`. Native writes still refuse. An observed task
closure, assignee or lease does not establish accepted evidence or an effective
execution fence. Gate warnings and incomplete observations must remain blockers.
