# Practical local fence WIP checkpoint — 14 October 2026

## Authority and scope

AUTH: the human requested `COMMIT IT` after the candidate was explicitly reported as unfinished. This is one local development-branch checkpoint, not a release, push, installed promotion or native qualification. The isolated stages1–5 approval remains in the canonical Fable records; it does not make the stages complete.

Branch: `development/r5-practical-fence-wip-20261014`. Parent source: `ad3f66e4cd885494cf5d4b10453d089288d7c517`; original tree: `003cf1770d86b684462ca6feb50060b8f9e7a280`. The detached isolated checkout was placed on this new local branch without resetting or replacing any existing branch. Git main and the separate older development checkout are not changed.

INTENT: retain the practical-fence development work and honest evidence so it can be resumed. The companion now reserves one immutable operation winner and permits UNKNOWN-to-exact-APPLIED readback reconciliation without repeating the mutation. The reviewed-invalid predecessor backend/consumer is stopped. The replacement request/SQL template binds actual lease facts, prohibits title-only ownership transfer and includes effect/receipt cardinality checks; it has no live dispatcher and is not native-proven.

## Exact added paths

- `claude-mon/tests_v2/test_practical_journal.py`
- `docs/changes/2026-10-14-practical-fence-wip.md`
- `docs/fable/derived/practical-fence-contract.json`
- `docs/fable/derived/practical-fence-plan.md`
- `docs/fable/derived/practical-resume-20261014.md`
- `docs/fable/evidence/practical-20261014/README.md`
- `docs/fable/evidence/practical-20261014/retained-artifacts.json`
- `memory-integrity/scripts/hybrid_bridge/practical_backend.py`
- `memory-integrity/scripts/hybrid_bridge/practical_consumer.py`
- `memory-integrity/scripts/hybrid_bridge/practical_contract.py`
- `memory-integrity/scripts/hybrid_bridge/practical_lease_sql.py`
- `memory-integrity/scripts/hybrid_bridge/practical_sql.py`
- `memory-integrity/tests_v2/test_practical_backend.py`
- `memory-integrity/tests_v2/test_practical_cli.py`
- `memory-integrity/tests_v2/test_practical_consumer.py`
- `memory-integrity/tests_v2/test_practical_lease_contract.py`
- `memory-integrity/tests_v2/test_practical_lease_sql.py`
- `memory-integrity/tests_v2/test_practical_quarantine.py`

## Exact updated paths

- `CHANGELOG.md` — links this WIP record and states the known failures/no-release boundary.
- `claude-mon/scripts/complete_read_v2/ledger.py` — protected practical event namespace, atomic reservation and exact readback recovery; legacy behavior remains subject to regression checks.
- `docs/fable/approvals.json` — preserves prior approvals and adds practical-range/local-commit authority.
- `docs/fable/plan.json` — appends the five scoped practical tasks while preserving earlier work.
- `docs/fable/requirements.json` — appends falsifiable practical requirements, not completed claims.
- `docs/fable/state.json` — records practical execution/resume without marking requirements complete.
- `docs/fable/tests.json` — appends explicit offline/native verification obligations.

Deleted paths: none. Old release ZIPs, content manifests, capability/version files, SKILL.md prefixes, Semantica implementation and installed copies are unchanged. External source/evidence/helper files are retained; the archive preserves their bytes rather than moving or deleting them.

## Fresh checks and retained identities

The existing `capture_checkpoint.py` was rerun before this commit. Captured source remained stable during the tests; every captured Python file parsed; all46 checked old release/Semantica files matched the original baseline. Results:

| Executed group | Actual result | Evidence limit |
|---|---|---|
| Lease contract, SQL text and predecessor quarantine | 10 passed | Offline validation/text/refusal only |
| Practical journal plus ledger/history/coordination regressions | 48 passed | SQLite/unit-test mechanics, not native Beads qualification |
| Native runtime policy | 4 passed | Offline environment/parser/scope checks |
| Predecessor and unfinished consumer/CLI integration | 21 ran: 1 failure, 10 errors | Candidate remains incomplete; reviewed-invalid route is stopped and CLI is absent |

The fresh checkpoint SHA-256 is `8f3de2b9a467b02f7eae03a0b171fc85efb04321bb40a9d13c56ffd652081154`. [Raw byte archive](../fable/evidence/practical-20261014/retained-artifacts.json) includes the complete logs and before/after source identities. The earlier stopped agent-host receipt SHA-256 is `a38619d99db9b5d3bca3d2750a40e4678707eaebafe138eb1d9a64822943b179`: scratch-root creation failed with WinError5 before any native command. It does not refute the earlier successful normal-PowerShell host-only test.

Pre-commit checks include Git whitespace/diff inspection, exact archive hash verification, candidate patterned-secret scan and staged-path inventory. No full source suite, extracted-package verifier, native transaction/expiry/crash pilot or exact-commit hosted CI is claimed to pass in this commit. No hosted CI was triggered by a local commit.

## Remaining work and rollback

See [the exact resume record](../fable/derived/practical-resume-20261014.md). Required work includes the real v2 schema/assertion routine, DB-minted300-second lease transitions, sealed native transport, full lease-bound CM consumer/CLI and verified dependency observations, native race/heartbeat/ABA/interruption/recovery proof, independent adversarial review, regression closure and matching final packages. Helper/reviewer agents stopped on workspace agent-credit exhaustion; their partial findings are not final approval.

Keep all qualification flags false. Do not install this candidate. Leave existing installations and old releases in place as the non-destructive rollback path. The stopped predecessor must not be re-enabled simply to make old fixtures green, and packing lists must not be regenerated to disguise unfinished behavior. Publication/push and installed replacement still require separate human approval.

## CI triage record — 14 October 2026 (afternoon, uncommitted)

Hosted CI on pushed HEAD `c6bde65` (run 38547854075, ubuntu 3.11) reported `Ran 427 tests: FAILED (failures=2, errors=10, skipped=54, expected failures=1)`. Disposition of all 12, resolved locally per file:

- `test_practical_consumer.py` SELECTION fixture repaired (added the contract-required `native_node_id`, assertions untouched); the 7 errors underneath were the deliberate v1 consumer STOPPED gate, so the file now holds 1 gate lock-in test (`test_stopped_v1_consumer_constructor_stays_stopped`) and 7 skips with explicit reasons (each names its in-flight v2 coverage or the missing committable target).
- `test_practical_backend.py` 2 errors were the deliberate v1 STOPPED gate (original to `adbbe1b`, gates kept); the tests now lock the gate (`test_stopped_v1_entry_points_stay_stopped_before_lease_dispatch`) and the shared operation seal (`test_operation_identity_is_never_rebound_and_unknown_never_retries`). File: 12 tests OK.
- `test_practical_cli.py` 2 failures are already green in this tree via the in-flight `practical-title` work (9 tests OK); that work is another worker's uncommitted surface and was not touched.
- `test_preservation.py` 1 failure is manifest drift, deferred to closure regeneration per plan (regenerating now would certify unfinished WIP).
- The `ValueError: bad companion` BLOCKED verdict in the log is a negative-path test working as designed (`test_m7_native_pilot.py:333`), not a failure.

Re-targeting the 9 stopped tests at the real v2 transport is blocked on other workers committing their surfaces: the lease backend pins `DOLT_PIN ca21a9d1…` (unreconciled with verified dolt v2.4.2 `317526a9…`), depends on the uncommitted ledger `consume_practical_native_dispatch`, and its tests are uncommitted. Tracked tests cannot import untracked modules (CI checks out committed code only). The P3 no-deletion decision (options a/b/c in the reviewer's plan) is still owed by the human and shapes the v2 consumer path.

## P3 decision — recorded 14 October 2026 (afternoon, uncommitted)

Human decision: **(b) release/unclaim/reclaim stay permanently offline-only.** No lease-row deletion permission is granted; the no-deletion invariant remains absolute. Native proof covers initial-grant, reassign (tombstone+mint, no delete needed), and heartbeat only. Consequences: the v2 lease builders for release/unclaim/reclaim are offline reference material, not natively provable paths. (Evening update: the stale/historical prerequisite guarantees already have executable v2 coverage — prerequisite refusal and reserve-level rebind tests, all green — since the lease transport committed; only live proof awaits a working host.)

## Implementation session — 14 October 2026 evening (uncommitted)

Base `12c394e`, tree clean before and after (no commit/push authority for
this session; all paths below are working-tree only).

- **B1 timestamps FIXED (TDD).** `initial_claim_sql` rendered receipt lease
  snapshots without the fractional suffix the title contract requires, so no
  claim-path receipt could feed a subsequent title request. Failing tests
  written first (3 sub-asserts failed as designed), then the three
  `DATE_FORMAT`s gained `.%f` (values stay second-truncated). Twin search:
  no other suffix-less lease rendering remains in the builder.
- **E consumer BUILT, 7 guarantees executable.** New
  `practical_lease_consumer.py` (`LeaseNativeConsumer`): concrete-type gate,
  internal current-authority precheck (refuses before reservation), winner-only
  dispatch with backend-persisted consumption, independent exact readback via
  the registered ledger callback, APPLIED-or-UNKNOWN completion, read-only
  reconcile. New `LeaseScratchBackend.read_current_authority` (SELECT-only,
  exact-shape, 0/ambiguity refused). The 7 skipped v1 tests are migrated to
  v2 bodies in place (gate test kept); skipped count drops by exactly 7 and
  the v1 stopped gates are untouched. A migrated test caught a real hole
  during development (callback once ignored a missing read and would have
  sealed APPLIED without backend evidence); fixed with an explicit None check.
- **B2 pin UNRECONCILED, recorded.** Local dolt v2.4.2 hashes `35BC2B8E…`;
  no local binary matches `ca21a9d1…` (bd.exe not present on this host).
  No substitution made. Needs the other worker's one-sentence answer.
- **C/D/F native BLOCKED (5th `dolt init` failure).** Fresh-temp retry
  returns identical `NotFound: FileSystem.access`; no native commands
  dispatched, no ACL/retry workarounds attempted. Race ladder, kill/crash
  recovery and grammar/rollback proof need a working host or workflow.
- **G retrieval BLOCKED without pinned runtime.** CI windows-latest shows
  `WinError 32` on session `output` cleanup plus one `Errno 22`; the file is
  untouched since Semantica 1.2 (not a WIP regression). Local worker runs
  fail earlier (`E_PYTHON_RANGE` on 3.14; venv install forbidden), so the
  exact failure is unreproducible here. No shared-code change made.
- **Full suites on final tree:** MI 463 tests, 0 errors, 1 failure
  (preservation manifest, deferred), 50 skips, 1 expectedFailure;
  CM 208 tests, 0 errors, 1 failure (preservation manifest).
- **Handoff corrections:** the GPT brief's "9 stale fixtures" framing is
  superseded (2 backend + 7 consumer re-targeted, not fixture-fixed); the
  brief's P1-step-2 assumed a committable lease precondition that only
  exists once the v2 transport committed. The no-deletion conflict stands as
  decided above; native reassignment remains unimplemented (sidecar grant
  helper only) and unproven.

## Adversarial review corrections — 14 October 2026 night (uncommitted)

Language standard adopted from review: **focused checks pass; reported
full suites have zero errors but two known preservation failures.** The
v2 consumer is an implementation under verification, not a completed
workflow. Offline-progressable work remaining (builders/bindings, CLI and
consumer wiring, race/interruption harness with assertions, regression and
release-verification logic) is distinct from runtime-gated proof (real
transitions, ladder, interruption, public end-to-end, final behavior).

An independent-shape review reproduced two defects without a native
database; both are fixed below with failing-first regression tests.
The reviewer also resolved the pin and scoped the remaining proof.

- **Consumer subclass readback bypass CLOSED.** The v2 consumer registered
  itself as the protected reader without guarding its own type, so a
  subclass overriding the readback callback could record APPLIED with zero
  native calls. `LeaseNativeConsumer` now requires exact-type construction
  and carries `__slots__` (instance-level method replacement is
  structurally impossible); backend subprocess paths were already
  exact-type guarded and needed no change. Regression tests cover subclass
  refusal and shadow-assignment refusal.
- **Grant lifecycle status corrected.** Producers write `CURRENT` (initial
  claim) and `GRANTED` (reassign mint); a task status such as `in_progress`
  is never a live grant. The consumer prerequisite now accepts exactly the
  producer set (plus the untouched tombstoned/pointer checks); all fixtures
  moved from `in_progress` to `CURRENT`. Retired lifecycles refuse.
- **Changed-authority test restored.** The historical test had drifted into
  a second digest-rebinding test; a dedicated changed-grant test now drives
  the original scenario (authority moves on after APPLIED, same request
  refuses at the prerequisite with no new intent or mutation) alongside the
  rebind test.
- **Pin RESOLVED (correction of this log's earlier claim).** Re-hashed here:
  `DOLT_PIN ca21a9d1…` is Dolt **2.4.1** at
  `R4-memory-integrity/runtime/dolt-v2.4.1/.../dolt.exe` (verified match).
  "No local binary matches" was a workspace-scope error. Dolt 2.4.1 fails
  `init` on this host identically (6th location); native proof still needs
  a working host or workflow, now with a known-good binary identity.
- **Label correction:** the v2 consumer is an implementation under
  verification, not the completed public workflow; `practical-title` and
  `practical-reconcile` stay preflight-gated pending native proof.

## Transfer semantics ADOPTED — human decision, experimental scope

The human explicitly adopts the in-place lease transfer (holder plus
transfer-moment heartbeat; granted time, granting node and original
expiry frozen; successor inherits remaining duration) as an EXPERIMENTAL,
scratch-scope custom protected-adapter protocol: disposable fence-owned
local databases only; not equivalent Beads behavior; not for production,
shared stores, replicas or merges; no-deletion kept; release/unclaim/
reclaim stay offline-only; original digest-bound facts immutable with
resulting facts under separate names; history assertions per write;
race/controls prepared but not executed. Native, commit, push, publish
and install gates all retained. Reopen only on materially new evidence.

## Ownership transition builder — 15 October 2026 (uncommitted)

New `LeaseReassignRequest` contract (transferor snapshot, distinct
successor, title, no deadline fields) and `reassign_title_sql` builder:
authority over issue, lease, grant, current pointer and metadata; issue
transfer plus title and token; native lease row updated in place (holder
and heartbeat only — granted moment and expiry never move, so the
original deadline survives); prior grant tombstoned, `GRANTED` successor
minted, current pointer moved, token/operation/receipt recorded, all
cardinality-asserted with rollback. This deliberately diverges from a
Beads delete-and-recreate transfer: the no-deletion rule forbids removing
the row, and the holder change shares one atomic transaction with every
dependent update. Failing-first builder and contract tests (5 new), all
green with neighbors; live grammar, rollback and race proof still require
a working host. Execution wiring (backend method, consumer path, CLI)
comes after, not in this change.
Review follow-up (same night): both grant-history inserts now carry
explicit row-count assertions (the "all cardinality-asserted" claim was
overstated without them); the receipt no longer overwrites the
digest-bound `lease_heartbeat_at_utc` — the transfer moment is recorded
under `resulting_lease_heartbeat_at_utc` while original facts stay
verbatim (the claim builder only ever added DB-minted fields, never
overwrote); the transfer is labeled a custom protected-adapter protocol,
not equivalent Beads behavior.

## Native race controller — PREPARED, NOT EXECUTED (no execution authority)

Prerequisites (all pending): a host where `dolt init` works, Dolt 2.4.1
(`ca21a9d1…`), a fresh disposable directory, and separate execution
authorization. No command below has been run; no process started or killed.

Setup (harness-owned DDL; the fence creates no Beads tables itself):
`dolt init`, start `dolt sql-server --host 127.0.0.1 --port <PORT> --no-tls`
(owned server, terminated after), apply `v2_schema_sql`, create minimal
Beads-shaped `issues`/`leases` tables covering exactly the columns the
fence predicates read, bootstrap namespace, register selection, seed one
open unassigned issue.

Paired cases (same schedule, observed barriers via
`experiment_guarded_title_sql(pause_seconds=20)` holding Alice's
transaction open, never sleep-only assumptions):
1. Alice's title batch authorizes against her live grant, then pauses.
2. Controller commits Bob's `execute_reassign_title` on a separate
   connection and reads back issue, lease, grant, pointer, token and
   operation rows.
3. Alice resumes unchanged: her UPDATE matches zero rows, the cardinality
   assert fails, the batch rolls back with no receipt row.
4. Fresh-process readback asserts Bob's state intact, zero stale Alice
   effect, zero stale receipt, journal UNKNOWN for Alice's op, APPLIED for
   Bob's; no retry or authority refresh anywhere.
Positive control: Bob's title through the same path succeeds.
Fence-disabled comparison: the identical schedule with fence predicates
stripped from both batches (harness-only SQL variants, no production
disable flag) must expose the stale title effect the enabled arm
prevents; if both arms refuse for another reason the comparison is
inconclusive, not proof. Expiry, heartbeat, ABA, spelling and foreign
cases reuse the same schedule with varied snapshots. Client-kill and
server-crash runs need their own separate authorization and are not
prepared here.

## Gates A-C execution — uncommitted follow-up (same night)

- Gate A done: one-second-wrong/invalid-precision/missing resulting
  heartbeat now refuses (new `E_MI2_RECEIPT_HEARTBEAT`: strict
  microsecond-zero format plus exact equality with authorization time
  truncated to seconds; granted-time lower bound kept). Non-vacuity shown:
  bounds-only logic accepts the probe. The truncation rule assumes MySQL
  `CAST(x AS DATETIME)` truncates rather than rounds; live behavior stays
  unverified until observed on a server.
- Gate B done except full suites below: positional history association
  (TOMBSTONED assert between the inserts, MINTED assert after) green;
  journal (10) and dispatch (8) green through the ledger V3 change.
- Gate C done except execution: `practical_race_controller.py`
  (schedule builder from the real builders, harness-only disabled arm,
  engine verification with pin + `.beads` marker, run path refusing by
  default and marked UNVERIFIED) plus `practical_race_verify.py` (pure
  PASSED/FAILED/INCONCLUSIVE oracle) with 8 offline harness tests green.
Adapted native-workflow spec: new push-triggered workflow on the WIP
branch running the controller against a working host with the pin
assertion first; file not created, nothing dispatched.

## Gate C repair (refuted labels corrected, uncommitted)

- Verifier is now fail-closed: empty snapshots, absent journal entries,
  missing dispatch observations and disappeared rows are reasons, never
  passes; stale title with unchanged ownership fields fails via full-row
  comparison; disappeared rows fail; unattributed changes are inconclusive
  unless fence-attributed proof exists; observed stale/duplicate/loss
  always fails.
- Orchestration implemented behind the confirmation gate with an
  injectable driver seam (order, barrier evidence, refusal mapping,
  stop-always all offline-tested with fakes); the live driver internals
  are UNVERIFIED and have never run.
- Engine identity split: structural preflight (paths, pin, `.beads`
  marker) separate from observed store identity, which the beads run
  must supply; synthetic stores keep the synthetic label and cannot
  satisfy beads assertions.
- GATES.md repaired to explicit-ID format with full CHECK commands.
- Gate D: this record + report carry diff, outputs, locations, labels and
  blockers; independent review stays REVIEW_PENDING.

## Offline harness completion pass — 17 October 2026 (uncommitted)

Base HEAD `3ea2355`, 10 modified tracked files and 4 untracked files on
arrival. Authority: the local, non-destructive work packages 1–5 only. No
native execution, no commit, no push, no install, no deletion. The result is
OFFLINE_HARNESS_IMPLEMENTED_NATIVE_UNVERIFIED. Every qualification flag in
`practical-fence-contract.json` stays false.

**Reconciliation first.** Two claims in the Gate C repair section above were
refuted against the saved bytes rather than accepted:

- "GATES.md repaired to explicit-ID format with full CHECK commands" was
  false. The saved `docs/fable/GATES-lease-reassign.md` failed the parser with
  14 explicit errors and exit 2: no gate carried an explicit `ID:` prefix,
  attributes sat behind nested bullet marks so they read as orphans, several
  gates had no CHECK at all, and A2/A3/A4 used "same command as A1" prose.
- The harness was green at 16 tests while five integrated false passes were
  live. A strict helper existed and was unused: `run_race` called
  `verify_winner_predicates` and scored it with a private
  `_judge_predicates`, while `judge_outcome` sat unused beside them.

**Failing-first observations, all through the real `run_race()` entrypoint**
(a scratch driver, before any edit): `wait_barrier` returning None gave
PASSED; a stale successful backend operation record with an UNKNOWN CM journal
gave PASSED; extended expiry plus wrong grant actor plus disagreeing grant
revision gave PASSED; a real-Beads identity holding only an unverified marker
string gave PASSED; positive and disabled-control phases scheduled but never
executed gave PASSED. The parser gave exit 2 on the saved gates file.

**What changed.**

- `practical_race_verify.py` is now the single authoritative, fail-closed
  path. `judge_evidence` is the only verdict function; the divergent
  `verify_winner_predicates`, `verify_final_state`, `check_no_stale_receipt`,
  `check_single_dispatch` and `judge_outcome` are gone rather than kept in
  parallel. A strict evidence schema is required first: run id and schema
  version, source commit plus working-tree and source-manifest digests,
  controller and verifier digests, runtime pin, synthetic versus real-Beads
  evidence class, observed database identity, exact task/actor/grant/operation
  identities, validated barrier, S0/S1/S2 observations, backend operation
  records, CM history and dispatch counts, and both control results.
- Reasons carry explicit codes and severities. English-prefix classification
  is gone. UNSAFE forces FAILED even when other evidence is incomplete;
  everything unverifiable is INCONCLUSIVE; only zero reasons is PASSED.
- Row identity is per table, including `issue_id` and composite keys such as
  `(store_incarnation, grant_id)` and `(store_incarnation, row_token)`. The
  old generic `id`/`operation_id`/`grant_id` heuristic is gone, and duplicate
  identities are reported instead of being collapsed by dictionary
  construction.
- Database-generated conflict tokens are validated for type, freshness,
  uniqueness and cross-record agreement, never predicted before the run.
- `practical_race_controller.py` orchestrates the complete schedule with S0,
  S1 and S2 boundaries and calls `judge_evidence` exactly once. It contains no
  verdict logic of its own. Barrier evidence must be a validated mapping bound
  to the exact run, operation and database session, with
  authorization <= transfer <= resume ordering sampled from the database
  clock. `None`, an empty mapping, a boolean and a sleep string are all
  refused; unsupported synchronization is explicitly INCONCLUSIVE.
- The live driver is implemented rather than stubbed. It owns the server and
  client processes it starts, hashes the pinned binary, queries observed store
  identity instead of asserting it, runs the sidecar bootstrap and selection
  registration, builds requests from observed authority, and terminates only
  its own retained handles. Its SQL is builder-produced and allowlisted, with
  one statement per call. There is no production disable-fence switch. The
  harness claim step is labelled MECHANISM-ONLY because the protected
  consumer exposes no claim dispatch; it is not consumer integration proof.
- New `practical_race_alice.py` runs the stale owner's dispatch as a bounded
  separate client process, because the pause lives inside an open transaction
  and cannot be observed from a thread sharing the CM connection.
- The synthetic fixture now creates the `dependencies` table the generated
  transfer predicates join; the previous fixture could not execute the real
  SQL at all.
- The datetime rule is labeled a runtime-dependent assumption with no
  universal MySQL claim, and fractional-second boundaries plus minute, hour,
  day and year rollover are covered.

**Gate A3 was named but never implemented.** The historical ledger claimed the
validator rejected invalid-precision and missing heartbeat evidence "inside
the probe test"; no such test existed. `test_reassign_receipt_refuses_invalid_precision_and_missing_heartbeat`
now exists and passes.

**Fresh checks** (PowerShell 5.1, Python 3.14.3, this session, counts read from
output and never copied):

| Group | Command | Result |
|---|---|---|
| Race harness | `unittest discover -s tests_v2 -p "test_practical_race_harness.py"` | Ran 86, OK |
| Focused lease suites | `-p "test_practical_lease_*.py"` | Ran 44, OK |
| Companion journal/dispatch | `claude-mon` `-p "test_practical_*.py"` | Ran 18, OK |
| Full memory-integrity | `unittest discover -s tests_v2` | Ran 569, 0 errors, 1 failure, 50 skips, 1 expected failure |
| Full companion | `claude-mon` `unittest discover -s tests_v2` | Ran 208, 0 errors, 1 failure |

Both single failures are the known preservation-manifest drift, deliberately
not regenerated so it cannot certify unfinished work. Zero errors were
introduced. `docs/fable/GATES-lease-reassign.md` now parses: 39 gates, 28 met,
11 unmet, exit 1 because unmet gates exist.

**Not done and not claimed.** No native execution, no host observation, no
independent review (`REVIEW_PENDING`), no regression closure, no publication,
no installation, and no claim that the broader M7/R5 scope is complete. The
live driver is implemented but has never been executed.

## Review repair round — 17 October 2026 (uncommitted)

An independent read-only review refuted the completeness claim in the entry
above. Every finding was reproduced locally before anything was changed; none
was taken on assertion. Two gates whose evidence overstated what had been
proven (D5, E2) were reopened.

**Falsifier note.** The previous pass's own test suite was green while six
verifier false passes and six driver wiring defects were live. Green tests
derived from the same implementation are correlated evidence, not proof of
completeness; that is exactly the mistake this round corrects.

### Verifier: six further false passes, all confirmed through run_race()

| Case | Before | After | Reason code |
|---|---|---|---|
| Final transfer history emptied | PASSED | INCONCLUSIVE | `GRANT_HISTORY_INCOMPLETE` |
| Only the MINTED history row removed | PASSED | INCONCLUSIVE | `GRANT_HISTORY_INCOMPLETE` |
| Stale row in the final operations snapshot, omitted from the record mapping | PASSED | FAILED | `STALE_BACKEND_SUCCESS_RECORD`, `OPERATION_RECORD_DISAGREEMENT` |
| Snapshot and mapping disagree on one operation field | PASSED | FAILED | `OPERATION_RECORD_DISAGREEMENT` |
| Unrelated task present before the race disappears | PASSED | FAILED | `ROW_LOST` |
| Unrelated grant present before the race disappears | PASSED | FAILED | `ROW_LOST` |
| Successor grant lease node / expiry / heartbeat / granted-at disagree with the lease | PASSED | FAILED | `GRANT_LEASE_FACTS_MISMATCH` |
| Current-grant pointer in a foreign namespace | PASSED | FAILED | `POINTER_MISMATCH` |
| No attributable protected-fence refusal | PASSED | INCONCLUSIVE | `REFUSAL_UNKNOWN` |

Root causes and repairs:

- The append-only transfer record was never required to exist. History is now
  checked for both the prior `TOMBSTONED` and the successor `MINTED` rows, and
  a history entry for an unrelated grant is a foreign event.
- Two observations of the same backend state were never compared. The final
  operations snapshot and the operation-record mapping must agree on identity,
  digest, authorization time and resulting token; a stale row appearing in
  only one of them is an observed stale effect.
- "Unaffected work survives" was enforced only for tables classified as
  unaffected, so a vanished unrelated row inside `issues` or `grants` passed.
  Survival is now scoped per row: only the claimed task's rows, its two grant
  ids, its winner token and its winner operation may change.
- The successor grant's lease snapshot was not cross-checked against the lease
  row it claims to describe. All four lease fields are now compared.
- The current-grant pointer was matched by task id only, so a foreign-namespace
  pointer satisfied it. The namespace is now bound.
- An absent refusal source was treated as no objection. A pass must now
  establish that the protected mechanism refused the stale write.

### Driver: six wiring defects plus a synchronization gap, all confirmed

| Defect | Before | After |
|---|---|---|
| `apply_ddl` refused its own multi-statement schema batch | `E_HARNESS_SQL: exactly one statement per call is required`, zero invocations | 4 batch invocations; the stored procedure body and its internal semicolons survive intact |
| `cm_observations` concatenated a string with a list | `TypeError: can only concatenate str (not "list") to str` | iterates stale plus every winner id |
| `run_transfer` subscripted a dataclass | `TypeError: 'LeaseReassignRequest' object is not subscriptable` | reads `request.operation_id`; committed requires an exact `WORKING_SET_APPLIED`, so returning without an exception is not proof |
| `read_state` flattened results and zipped them onto table names | 10 rows in, 8 kept, a grant-history row filed under `current_grants` | grouped results; every row stays under its own table |
| `positive_control` treated a non-exception `UNKNOWN` as success | `applied: True` with `PRACTICAL_NATIVE_UNKNOWN` | `applied: False`; success additionally confirmed by independent readback of the issue title |
| `disabled_comparison` refused its own comment-led batch | zero SQL invocations, `executed: True` claimed anyway | executes in one builder-verified batch, confirms the stale effect by readback, and reports `executed: False` when it cannot run |
| `start_alice` marked a paused batch the worker never ran | marker absent from the worker spec; the worker rebuilt the ordinary unpaused SQL | the spec carries only a pause length; the sealed backend derives the paused batch itself |
| `store_identity` read metadata before the sidecar existed | identity observed before bootstrap | schema, bootstrap and registration now precede identity; no task is seeded without it |
| The child could not import the harness or the companion | no `PYTHONPATH` | the client environment carries the resolved script roots |
| The owned client process was never released | only the server was stopped | both owned processes are released on every path, and a failed release blocks a pass |
| Source hashing omitted the worker and the companion | 6 modules | 7 harness modules plus the companion ledger actually used |

### The paused-batch synchronization gap

The marked, paused batch existed only inside the harness. The worker called
the ordinary protected dispatch, and the sealed backend built the ordinary
unpaused title SQL, so the intended paused transaction was never the batch that
ran. Repair: `LeaseScratchBackend.execute_paused_guarded_title` derives the
paused batch itself from the validated request and a bounded 1..30 pause, and
`LeaseNativeConsumer.dispatch_paused_lease_title` exposes it over the same
journal, consumption, receipt and UNKNOWN path. All three protected dispatches
now share one `_execute_protected` body, so reservation-before-dispatch,
winner-only consumption, exact receipt validation and the APPLIED-or-UNKNOWN
terminal cannot drift apart. No caller SQL crosses any boundary, and the
transport bound grows by exactly the pause. The ordinary transport budget
would otherwise have timed out a 20-second pause, which this also fixes.

### Fresh checks

| Group | Command | Result |
|---|---|---|
| Race harness | `unittest discover -s tests_v2 -p "test_practical_race_harness.py"` | Ran 114, OK |
| Reviewer verifier cases | same, `-k ReviewerVerifierCaseTests` | Ran 10, OK |
| Driver wiring | same, `-k DriverWiringTests` | Ran 18, OK |
| Focused lease suites | `-p "test_practical_lease_*.py"` | Ran 44, OK |
| Companion journal/dispatch | `claude-mon` `-p "test_practical_*.py"` | Ran 18, OK |
| Full memory-integrity | `unittest discover -s tests_v2` | Ran 597, 0 errors, 1 failure, 50 skips, 1 expected failure |
| Full companion | `claude-mon` `unittest discover -s tests_v2` | Ran 208, 0 errors, 1 failure |

Both single failures remain the known preservation-manifest drift, deliberately
not regenerated. `docs/fable/GATES-lease-reassign.md` parses at 42 gates,
31 met, 11 unmet.

**Two defects this round was caught introducing.** A refactor of the shared
consumer dispatch body lost a method's indentation, and the new backend helper
was first written without its `cm_db` and `reservation` parameters. Both were
found by the focused regressions before any claim was made, and both are
recorded here because the first pass's lesson was precisely that a green
harness is not a finished one.

**Still not claimed.** No native execution, no host observation, no
independent review of this round (`REVIEW_PENDING`), no regression closure, no
publication and no installation. The live driver and the paused dispatch remain
unexecuted against any server.

## Contract-integration repair round — 17 October 2026 (uncommitted)

A second independent review confirmed the previous round's fixes but found
that connecting the driver to the real components exposed contracts the new
mocks did not represent. All findings were reproduced locally first.

### What the mocks had been hiding

- `complete_practical_native_readback` returns exactly
  `{inserted, kind, binding}`. The driver read `observed_state`, which the
  companion never returns, so a real successful transfer was read as
  `committed: false`. The mock supplied the invented field, which is why its
  tests passed. `completion_outcome` now maps only an explicit terminal event
  name; a missing or unrecognized field is never success.
- The consumer can return an uncertain terminal **without raising**, so the
  worker's exception-only attribution lost the rejection entirely. The worker
  now reports the real terminal and no refusal at all. Attribution moved to
  the controller, which independently re-reads current authority: if Alice's
  own request can no longer satisfy the protected predicates, that is observed
  evidence the fence stopped it; anything else stays unattributed. An unknown
  outcome is never promoted to a fence refusal.
- `_claim_request` built the historical v1 `InitialClaimRequest`, which the
  current `initial_claim_sql` refuses. It now builds the v2 `LeaseClaimRequest`
  (`schema_version: 2`, `action: initial_claim_lease`, `expected_status: open`)
  from observed facts, with no caller deadline, lease timestamp, node or token.
- `seed` ran an UPDATE against a row that does not exist on a fresh store. It
  now INSERTs the task, reads the database-minted namespace back, and rebinds
  the selection to it before anything is signed. Alice's own request is
  derived from post-claim authority rather than the pre-claim fixture packet.
- The controller marked a copy of the paused batch that the backend never ran,
  so the watcher's session search could never match. `PAUSE_BARRIER_MARKER` is
  now defined by the sealed backend and attached to the SQL that actually
  executes; the controller delegates to that one definition.
- Three more evidence cases passed: a successor grant omitting its lease
  snapshot fields (each field is now mandatory, not compared only when
  present), an S1 lease holder inconsistent with the claimed committed transfer
  (S1 is now validated as thoroughly as S2, including its pointer and prior
  grant), and a stale backend row observed in S1 but absent in S2 (every phase
  is now scanned, so an observed unsafe effect cannot disappear backwards).

### The decisive new test

`RealComponentIntegrationTests` runs the real builders, the real sealed
backend, the real consumer and an in-memory companion journal, faking only the
native process boundary. It confirms the real completion shape, that the
driver commits on `PRACTICAL_NATIVE_APPLIED` and not on
`PRACTICAL_NATIVE_UNKNOWN`, that the journal records exactly one dispatch
consumption with a verified chain, that the executed paused SQL carries the
marker, that the v2 claim request is accepted by the real builder, and that
the observed store identity satisfies the verifier.

The integration suite keeps retained, uniquely named temp journals and deletes
nothing, matching the standing no-deletion rule.

### Fresh checks

| Group | Result |
|---|---|
| Race harness | Ran 132, OK |
| Real contract tests | Ran 7, OK |
| Actual-component integration | Ran 6, OK |
| Second-round verifier cases | Ran 5, OK |
| Focused lease suites | Ran 44, OK |
| Companion journal/dispatch | Ran 18, OK |
| Full memory-integrity | Ran 615, 0 errors, 1 failure, 50 skips, 1 expected failure |
| Full companion | Ran 208, 0 errors, 1 failure |

Both single failures remain the known preservation-manifest drift. The gate
ledger parses at 45 gates, 34 met, 11 unmet. Gate H records this round.

**Still not claimed.** No native execution, no host observation, and no
independent review of this round (`REVIEW_PENDING`). The next native-run
proposal stays premature until that review clears.

## 17 October 2026 — saved offline integration repair

Status: OFFLINE_REPAIR_VERIFIED_NATIVE_UNVERIFIED for the current user's
bounded completion contract only. Earlier completion/coverage claims above
are historical; this section supersedes their current offline status and
explicitly retains every native/release/install limitation.

Arrival was HEAD 3ea23556fd336ba64a3ebcf6b4fc169e71051d11, ten modified tracked
files and five untracked files. A retained write probe succeeded. All 501
arrival files and intended edit targets were hashed/snapshotted before edits;
targets were rechecked before writes. The primary review was read completely
and treated as reproducible claims. No existing dirty change was reset.

Observed before/after findings and corrections:

- Actual resume_alice followed by run_race returned PASSED for UNKNOWN with
  E_UNRELATED_TRANSPORT_FAILURE and current Bob authority. The saved red
  regression captured that false PASS. Current staleness now returns
  by=null/code=E_HARNESS_EXECUTION_CAUSE_UNPROVEN; worker-supplied cause fields
  cannot establish a fence refusal. Cleanly wired uncertainty remains
  INCONCLUSIVE/REFUSAL_UNKNOWN.
- Bootstrap readback now validates the DB-minted UUID and independently
  observes its unregistered metadata before binding the selection, before
  registration. Existing/foreign/missing/malformed/contradictory namespaces
  refuse. Seed validates that registration's namespace rather than rebinding.
- Alice's generated operation ID replaces the pre-claim fixture everywhere
  it is consumed; the worker outcome ID is checked. The actual post-claim
  transfer packet and derived schedule batch are retained too. Claim,
  transfer, stale and positive-control operations stay distinct, and a second
  uncertain Alice start refuses before dispatch.
- Actual store_identity output is used. Physical tables map explicitly to
  logical evidence; all required tables, including dependencies, are checked.
  Missing/duplicate/malformed schema observations refuse. The observed Beads
  identity's nested shape is consumed correctly; real-Beads runtime identity
  remains UNVERIFIED.
- Backend WORKING_SET_APPLIED, companion PRACTICAL_NATIVE_APPLIED and UNKNOWN
  remain separate. Complete stored bindings/receipts are validated and
  retained, with actual per-event CM bindings and chain/replay observations.
  Missing/contradictory receipts and duplicate rows cannot pass.
- One committed-transfer validator serves S1 and S2. It checks owner/status,
  task/store/node, frozen lease facts and grant deadline, successor lease
  facts, prior-grant tombstone and preserved facts, current pointer/revision,
  token/history/operation relationships and baseline record preservation.
  A missing S1 operation or changed S1 status is no longer overlooked.
- S2 operations are read before controls, at the same boundary as S2 state.
  The baseline claim record/history is preserved. Positive/disabled controls
  keep their own later observations. A later observation error cannot erase
  an already observed unsafe effect, including a contradictory duplicate row.
- The new connected test found an additional real wiring defect: Alice tried
  to recreate the parent's existing CM work item. The worker now validates
  and reopens that registration, and closes its connection. The driver also
  closes its owned companion connection at completion.

Coverage correction: the older six RealComponentIntegrationTests substitute
authority, clock, consumer selection and snapshots. They remain useful
component tests and are retained under that narrower label. The six new
FullSequenceOfflineTests exercise actual fresh setup, namespace/registration,
seed/claim, observed request construction, paused worker/dispatch, transfer,
S1, Alice completion, S2, journal, controls, canonical verifier and owned
resource release. Only native filesystem/process/SQL transport boundaries are
modeled, from complete generated packets and shared phase state. This is
TEST_ONLY and proves no Dolt SQL execution, grammar, rollback or native race.

Fresh focused results: race suite 159 passed (including 27 new regression
bodies), lease suites 44 passed, protected consumer 17 passed, companion
practical journal/dispatch 18 passed. The new 27-test module also passes the
direct project unittest discovery command without the retention adapter.
The connected evidence collector records two uncertain cases and sixteen
fault cases; both uncertain cases reach judge_evidence exactly once with
REFUSAL_UNKNOWN as their only reason. Unsafe effects fail; unavailable cause,
missing evidence and failed cleanup cannot pass.

Broader results are adapted offline runs, not an unchanged full CI run.
Retained temporary directories and inherited audit guards block deletion,
external/native programs and network. Guarded Python subprocesses are allowed.
MI v2: baseline 615 and repaired 642, both 2 failures/36 errors/54 skips/1
expected failure, with no existing test changing outcome. The failures are
preservation drift and a containment test whose taskkill is blocked; 34 errors
are blocked actions and two are Windows short-path observations. CM v2:
baseline and repaired 208, both 1 preservation failure and 1 blocked file
deletion error. The baseline-copy retained-fixture parent was supplied before
that comparable CM rerun; its earlier setup errors are retained separately.
Additional legacy, repository and eval results, and every failure/error, are
listed in the report. No historical content manifest was regenerated.

Gates: H2 was reopened because its old six tests did not establish the
claimed complete workflow; it is closed only by the new connected test.
Gate I records OFFLINE-A through OFFLINE-I. B4/B5 and F1-F9 remain unmet:
full regression/release closure, native qualification, independent review,
packages, publication and installed use are still open. All native flags in
the adopted practical contract stay false. The source itself is saved;
qualification, release readiness and installation are not claimed.

Evidence: docs/fable/evidence/offline-repair-20261017/repair-report.md,
acceptance-source.json, connected-evidence.json, connected-fault-matrix.csv,
regression-comparison.json, all failing/passing transcripts, and verify_saved.py.
No deletion, native Dolt/Beads execution, install, commit, push, workflow,
packaging, release-manifest regeneration, external AI, agents, publication or
installed-copy replacement occurred. Independent review remains pending.
