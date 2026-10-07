# M7 native observation candidate

This candidate adds `native-observe` to the single public workflow. It checks
an explicitly selected executable SHA-256, v1.3.1/commit identity, ordinary
paths, embedded project metadata, the actual database path/prefix, and repeated
task export/head/info reads. It rejects unknown stderr, invalid JSON, missing
dependencies, unsupported relations, missing endpoints, cycles and data drift.

Export uses `--all --no-memories` to enumerate issue/dependency records without
exporting unrelated key/value memories. It is not a whole database backup.
Count mismatch refuses completeness, including owner exclusions and row caps.
The imported relation direction is prerequisite `from` to dependent `to`.
Every issue must match the selected known prefix followed by `-`, consistent
with v1.3.1's `ExtractIssuePrefixKnown`; foreign-prefix records refuse even when
the export count agrees. Multi-prefix databases need a separate approved map.
`blocks` is hard; the documented annotation relations are informational.
`parent-child`, `conditional-blocks` and `waits-for` require further policy and
are refused. External endpoints are refused until explicitly qualified.

All output stays `NATIVE_OBSERVED_UNQUALIFIED`, with `active=false` and
`native_beads_qualified=false`. Repeated reads detect observed drift but do not
establish an atomic cross-command snapshot. A task status, actor and future
lease are observations; they are not an effective fence or accepted evidence.
Native writes still raise `E_NATIVE_UNQUALIFIED` before any subprocess call.

Use an exact explicit selection JSON containing all NativeSelection fields,
including expected_project_id, expected_database_name and expected_prefix.
The receipt destination must be absolute, in an existing ordinary directory,
and new. The command preserves command stdout/stderr/exit data in its receipt
even on a warning refusal. A preflight failure reports BLOCKED on stdout.
Captured bytes are retained as base64, byte count and SHA-256 for each pipe.
Decoded display text is not the lossless evidence. Output beyond the per-pipe
limit is marked truncated and refused. Termination confines the tree: a Job
Object with KILL_ON_JOB_CLOSE under the extended-limit structure (class 9,
explicit signatures), closed on every return path so even clean exits cannot
strand descendants; where job setup is refused, a taskkill tree sweep runs at
kill time. Pipes must reach EOF or containment is refused (E_NATIVE_CONTAINMENT,
UNKNOWN). Residual limit: descendants spawned after sweep enumeration on
non-job hosts remain possible and are recorded, never labeled proven. The
containment fields (kill_path_used, tree_contained, method, note) are retained
in every observation receipt. Grandchild pipe-holder and clean-exit probes
cover both paths.

## Durable native-operation development seam

The R4 development branch now includes a CM-owned native-operation journal
seam. It requires an explicitly qualified adapter identity, current dispatch
guard, stable operation/work-item/command/selection binding and durable
`NATIVE_INTENT` before mutation. An interrupted operation becomes
`NATIVE_UNKNOWN`; the same operation ID can never issue the write again.
Recovery is backend-readback-only and appends `NATIVE_RECONCILED` only when
the selected effect is proven. Absent or ambiguous readback stays UNKNOWN.

The public/native wrapper derives its dispatch guard from the matching
companion's coordination module. Callers do not supply a trusted `ok=true`
guard object.

For the separately authorized disposable runtime/database pilot, use
`scripts/m7_native_pilot.py`. It verifies SHA-256 and the pinned
v1.3.1/commit before initialization, keeps the database external through explicit `BEADS_DIR`, uses a tiny sibling launcher Git repository only for the pinned v1.3.1 `beads.role`, and then runs `init --quiet --stealth`, creates a disposable task, claims it once,
injects an interruption after the native effect, reopens CM, reconciles by
readonly `show`, and verifies an idempotent second recovery. The receipt must
retain exactly one claim invocation and the journal sequence
`NATIVE_INTENT -> NATIVE_UNKNOWN -> NATIVE_RECONCILED`.

A successful disposable receipt is scoped evidence only:
`pilot_native_write_observed=true` while
`native_beads_qualified=false`. It is not authority for shared/project writes.

Native compatible/conflicting merge qualification, shared-database execution
qualification, successor packaging/promotion and installed replacement remain
separate gates. The m11 pair remains the released baseline until those gates
are separately approved and observed.
