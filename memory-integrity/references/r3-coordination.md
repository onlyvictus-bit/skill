# R3 coordination and history — offline policy, not native qualification

Use this reference when work has prerequisites, when task-state branches must
be compared, or when retained audit history must be checked. The user-facing
skill remains `memory-integrity`; `claude-mon` is its explicit matching engine.
R3/m11 cannot use an R2/m10 companion. The pinned semantic digest is
`bf3c6314a1b0e8503230f483ef0be19cbf2ace1d4cab96eb4d7a2599b0270c9f`.

## Ownership and boundaries

Fable owns approved requirements and milestone authority. Beads is the intended
native operational task/edge/claim/Dolt-branch store. CM owns exact execution
proof, CAS and one central SQLite event chain. MI owns applicability checks and
reporting; cards are derived. Do not merge SQLite files, add another scheduler,
or treat a Beads `closed`/`ready` field as accepted audit evidence.

This release implements portable TEST_ONLY policy and fixture workflows. Native
Beads reads/writes are disabled: M7 must install and qualify the exact extracted
binary, native JSON contracts and disposable non-cloud database round trips.
The archive hash is not an executable hash. Installed promotion, real database
migration and live AI/backend calls are separate approvals.

Keep SOURCE_IDENTITY, EXTRACTION, COVERAGE, SEMANTIC_AUDIT, MEMORY and
PERSISTENCE_BRIDGE separate. Task coordination does not enlarge a model's
context window, prove interpretation truth, or make GPT memory permanent.

## Runnable offline task graph

Use `scripts/memory_integrity_workflow.py`. Explicit paths below are arguments,
not hard-coded user paths. Prepare a UTF-8 JSON plan with this exact shape:

```json
{
  "schema_version": 1,
  "workspace_id": "audit-project",
  "run_id": "approved-version-1",
  "requirement_digest": "<SHA-256 of the approved requirements>",
  "tasks": [
    {"id":"A","source":"<absolute source A path>","task":"Audit A",
     "responses_file":"<absolute supplied reviews path>","requires":[]},
    {"id":"B","source":"<absolute source B path>","task":"Audit B",
     "responses_file":"<absolute supplied reviews path>","requires":["A"]}
  ]
}
```

The digest must be 64 hexadecimal characters, not the placeholder. Review
fixtures have the exact R2 review schema (one row per declared source unit).
The plan is explicit local input, not inferred approval for external activity.
Task IDs are namespaced workspace::run::task. Each coordinated task audits its
complete source manifest in one bounded request; oversize requests refuse,
never silently accept a subset. R2 chunked standalone audits remain available.

```text
python scripts/memory_integrity_workflow.py coordinate-init --claude-mon-root <CM> --workspace-dir <new scratch workspace> --plan-file <plan.json>
python scripts/memory_integrity_workflow.py coordinate-ready --claude-mon-root <CM> --workspace-dir <workspace>
python scripts/memory_integrity_workflow.py coordinate-run --claude-mon-root <CM> --workspace-dir <workspace> --task-id A
python scripts/memory_integrity_workflow.py coordinate-run --claude-mon-root <CM> --workspace-dir <workspace> --task-id B
python scripts/memory_integrity_workflow.py coordinate-resume --claude-mon-root <CM> --workspace-dir <workspace> --task-id B
python scripts/memory_integrity_workflow.py coordinate-verify --claude-mon-root <CM> --workspace-dir <workspace> --query every
python scripts/memory_integrity_workflow.py coordinate-revoke --claude-mon-root <CM> --workspace-dir <workspace> --task-id A --reason <explicit reason>
```

The graph is a frozen, fully enumerated version. Hard and informational edges
are the only qualified relation types. Missing nodes, cycles, self-edges,
foreign identities, unknown relations and incomplete pagination refuse.
Changed requirements/graphs/claims need an approved successor basis, not an
in-place policy edit. OFF mode is a distinct task, never a downgrade of a
registered coordinated task.

The CM guard runs before preparation, adapter dispatch, acceptance, protected
low-level transitions and later consumption. Exact prerequisite proof references
and graph/policy digests are inside the measured request and its single-use
approval. Eligibility recheck, approval spend and DISPATCHING share a single
CM transaction; a late ledger prerequisite revocation cannot spend an approval
before rejection. Unverified/partial/revoked/stale predecessors block descendants.
Sources are reread by the public adapter before preparation, dispatch and
acceptance, and on public report/recall/resume; graph CAS is reopened at every
guard. These boundary observations are not a filesystem-wide atomic read.
Native lease/branch freshness is still M7-unqualified. Historical evidence is
retained, but no longer labelled currently applicable. Legacy CM CLI dispatch
and resume refuse coordinated identities. Supported same-task preparations are
serialized in SQLite; raw native commands/SQL outside the wrapper are outside
execution enforcement. There is no atomic SQLite–Dolt transaction.

Completed current tasks resume without dispatch. `coordinate-resume` continues
the same PREPARED/AWAITING_APPROVAL attempt using its exact stored request and
an unconsumed matching approval; RESPONSE_SAVED/VALIDATED resumes validation or
acceptance without a second adapter call. An interrupted unbound QUEUED claim
is cancelled in history before fresh preparation. DISPATCHING or interrupted
spent approval reconciles to DELIVERY_UNKNOWN and refuses automatic resend.
The low-level coordinated ledger also refuses replacement attempts while any
retained delivery is unknown. A caller-written retry reason does not unlock
the frozen coordinated run; reconciliation or a distinct approved run/basis
is required. Generic coordinated DISPATCHING transitions are refused even
with a valid context: only the atomic approval/start path may create them.
Cancellation or a retryable-error label cannot erase a spent approval with no
saved response. Such attempts must use uncertain-delivery reconciliation.
Uncertain delivery needs an explicit reviewed recovery decision/new approved
basis; it is never proof of success. Do not delete a blocker.

## History verification and checkpoints

Normal event UPDATE/DELETE and invalid inserts are refused by schema guards.
Events hash canonical identity, evidence references, predecessor and complete
projection snapshots. Replay validates each typed state delta, not only the
last snapshot. Generic events cannot alter projections or run inside a caller
transaction. Current task/attempt/approval/policy projections must match replay.
Corrections and revocations append, not erase. Legacy scratch
migration retains LEGACY_UNVERIFIED provenance and cannot become strict proof.

History reports keep these fields separate:

- `normal_append_only_enforced`: ordinary SQL guard presence;
- `internal_chain`: contiguity and canonical predecessor/event hashes;
- `projection_replay`: complete retained projections match current data;
- `anchored_completeness`: the current head matches the retained checkpoint;
- `anchored_through_seq` / `current_head_anchored`: a valid earlier prefix is
  identified separately; later unanchored tail completeness is UNVERIFIED.

No supplied checkpoint means anchored completeness is UNVERIFIED. Export a
checkpoint outside the checked workspace, retain it as a verifier-owned input,
and pass that same reference on future checks:

```text
python scripts/memory_integrity_workflow.py history-seal --claude-mon-root <CM> --workspace-dir <workspace> --owner <verifier identity> --seal-path <new external checkpoint.json>
python scripts/memory_integrity_workflow.py coordinate-verify --claude-mon-root <CM> --workspace-dir <workspace> --checkpoint-file <retained checkpoint.json>
```

Checkpoint fields are schema, checkpoint_id, owner, integer seq and event_hash.
The command uses exclusive creation and refuses a path inside the checked
workspace. This is a caller-retained reference, not a newly deployed protected
storage service. The filesystem owner can drop triggers or replace a database;
replacing both history and its trusted checkpoint is outside this guarantee.

## Task-state branch policy

`branch-preview` and `branch-merge-fixture` accept `--fixture-file` JSON with
`base`, `source`, `target`, `common_ancestor`. Each origin contains database,
branch, head, tasks (ID->state), edges (`from,to,relation`), evidence (basis
records), evidence_class=TEST_ONLY. Public database must be
`fixture:<workspace_id>` and task IDs must exactly match the selected plan.
CAS references are computed from actual origin bytes, not trusted declarations.

```text
python scripts/memory_integrity_workflow.py branch-preview --claude-mon-root <CM> --workspace-dir <workspace> --fixture-file <branches.json>
python scripts/memory_integrity_workflow.py branch-merge-fixture --claude-mon-root <CM> --workspace-dir <workspace> --fixture-file <branches.json> --operation-id <stable unique merge ID>
python scripts/memory_integrity_workflow.py branch-reconcile-fixture --claude-mon-root <CM> --workspace-dir <workspace> --operation-id <interrupted fixture merge ID>
```

Compatible three-way changes combine. Competing task/dependency/evidence edits,
unknown common ancestry, moved heads, malformed origins and resulting cycles
refuse. There is no automatic ours/theirs conflict resolution; a conflict needs
an explicitly reviewed new source/target basis, not a silent choice. Preview
digests are rechecked before application. Git repository/worktree/branch/head
and actual file-content hashes are observed separately; non-Git is explicit.
This does not merge user source code.

CM merge intent/outcome retains base and both source/target CAS origins and
heads. A fixture merge invalidates current frozen task-head applicability and
requires a new approved graph/basis and fresh evidence. It never consumes an
old approval or imports accepted strings. Stable operation IDs suppress repeated
logical application. Both origins/base/result are reopened on later workspace
verification; missing/corrupt refs block it. Interrupted intent remains UNKNOWN
until `branch-reconcile-fixture` reconstructs the pure deterministic fixture
result from retained CAS intent and appends its outcome; this is not a native
readback inference. Fixture native-operation recovery uses its actual readback
and never reissues an uncertain write.
Real native interruption/recovery still needs M7 qualification.

The optional Beads journal is clone/branch local and bounded/prunable. Cursor
gaps, merge/sync/restore and missing observation require explicit rebaseline;
never substitute it for CM's permanent canonical history.

## Uploaded ChatGPT / no-runner mode

List every approved task, prerequisites, missing/current evidence, branch
origins/conflicts and history/checkpoint limitations in the section-12 report.
Keep all six evidence states and five card dimensions separate. Label the
result MANUAL_REPORTED. Without actual execution, do not claim enforced
dependencies, immutable history, native merges, computed hashes or strict READY.
