# Practical local fence: approved implementation plan

This is an implementation delta in the existing Fable control plane, not a new scheduler. The user adopted the contract and approved isolated stages 1–5. Authority and exact intake/source identities are in practical-fence-contract.json. Preserve the prior strict-contract record and all old source, packages and receipts.

## Judge finding and corrections

The ordinary-fence architecture is technically reasonable, not yet native-proven. Independent native Sol review returned FIX-FIRST on the submitted plan. This approved implementation includes the required corrections: backend-clock authorization, immutable grant/operation binding, shared issue row_lock conflict cell, ignored/local receipts, separate working-set and HEAD states, expired-heartbeat refusal with no re-arm fallback, and a bounded scratch-candidate route which never manufactures NATIVE_VERIFIED to bootstrap its own qualification.

INTENT: replace the protected route's actor/status-only proof with an operation-bound local backend fence and exact receipt readback. At authorization, the original deadline must still be live; after authorization persistence may finish later. This is not the old strict expiry-before-save promise.

Scope is the protected adapter/skill route on a single selected local database and main branch. Arbitrary raw bd/SQL writers are not forced to use this API. Unsupported protected close/delete/import/restore/batch/foreign/wisp paths must refuse rather than masquerade as covered. No Beads fork, new driver, service or toolchain is installed. Existing pinned Beads and Dolt executables are reused. No DOLT_ADD/DOLT_COMMIT occurs inside an open SQL transaction.

## Owners and surfaces

- Backend worker: new hybrid_bridge/practical_contract.py, practical_sql.py, practical_backend.py; tests_v2/test_practical_backend.py. Standard-library, bounded Dolt SQL CLI transport and strict packet/receipt validation.
- Journal worker: companion complete_read_v2/ledger.py and new tests_v2/test_practical_journal.py. Atomic winner-only reservations, protected event namespace and typed internally verified readback completion.
- Parent: retained native pilot/controller, practical consumer/public CLI wiring, baseline failure diagnosis, pair instructions/capabilities/contracts, canonical Fable deltas and exact-package builder/verifier.
- Native Sol reviewer: read-only architecture/final diff challenge. Reports are not completion; parent observes the actual behavior.

Workers are not alone and may not edit each other's surfaces. All authored edits use apply_patch. No cleanup/delete/reset, shared data, provider calls, commit/push or installation is authorized. Existing source and release artifacts remain available for rollback; disable the candidate route instead of undoing history.

## P1 — smallest backend fence

1. Record exact source bytes and untouched test baseline; source identity is not behavior proof.
2. Write reason-specific red tests against missing packet/SQL/receipt behavior before implementing the new modules.
3. Build one-session transaction SQL: compare incarnation/db/branch/task/actor/status/grant/original signed row_lock/fixed deadline/op ID/command digest; one DB clock sample; mutate title and fresh DB-generated conflict token and insert the bound operation receipt atomically.
4. Avoid identical-value token merges. Preserve a local uniqueness history for generated protected tokens; a collision refuses rather than allowing two authorities to share the conflict cell. The issue token is not the grant generation.
5. Run a real synchronized scratch experiment: Alice holds an open native transaction, Bob commits a newer grant/token, Alice resumes. Inspect title/token/grant/receipt independently. A sequential stale precheck is not the gate.
6. Pair the refusal with a current-owner success through the same path. Any stale committed effect stops that candidate immediately.

CHECK: native pilot's first conflict group, with exact raw commands and fresh readback.
EXPECT: zero stale effect and absent stale-operation receipt; winning grant preserved; successful current-owner control. No broad native qualification.

## P2 — ownership generations and heartbeat

Implement protected claim/live same-owner repeat, expired same-owner reacquisition, reassignment, unclaim and reclaim. Reassignment/reacquisition mint a never-reused grant. Preserve grant history; no SQL DELETE. Protected heartbeat requires current exact grant/holder/status plus a live DB-time lease. Missing/expired/foreign/spelling fallback cannot re-arm an old grant.

All protected transitions including heartbeat share the issue conflict cell. Keep a current-grant revision binding so an unprotected issue write invalidates an old protected ticket. Live renewal may extend the grant for future requests but never rewrites an already-issued operation's original deadline. Conservatively refusing a concurrent version change requires a fresh approved operation basis, not blind retry.

CHECK: backend tests and real native transition matrix.
EXPECT: expired heartbeat, A→B→A and synchronized ownership race refuse the original immutable request; valid control succeeds; unsupported routes cause no effect.

## P3 — actual consumer and protected CM journal

The public consumer derives current prerequisite/dispatch checks internally, then reserves the full immutable operation intent in CM atomically. Only the reservation winner gets an execution capability. The generic native qualification route must refuse the scratch candidate rather than accepting self-declared flags. Generic CM event APIs cannot manufacture the new native terminal namespace.

After execution or reconciliation, read the backend operation ID and validate its full binding; do not infer success from matching title, actor or status. Distinguish historical applied proof from current applicability. Later expiry/revocation must not erase legitimate history or allow it to authorize new work.

CHECK: public consumer tests, two-connection reservation race, forged/wrong-task/wrong-grant/rebound-ID/direct protected-call probes and actual native consumer run.
EXPECT: one winner/one effect, exact proof history, zero unauthorized execution/permission consumption, mismatches rejected and missing delivery retained UNKNOWN.

## P4 — real interruption and fresh recovery

Inject synchronization barriers into the test controller, not arbitrary caller SQL. Retain the exact child handle, active SQL session and observed barrier. Kill the native client while the command is outstanding; separately crash/restart only the controller's own local server. Reopen CM and the backend in fresh processes. Read the original operation record only. Never heartbeat, reacquire, refresh the revision or repeat an uncertain write.

CHECK: native pilot pre-effect, outstanding-command, after-effect/pre-reply, server-crash/restart and repeated-recovery groups.
EXPECT: exact historical applied result if proven; otherwise UNKNOWN; repeated recovery has zero additional native writes/events; all run files retained.

## P5 — release the exact observed pair

Run all source suites against the recorded baseline and diagnose baseline path/containment failures without weakening checks. Preserve Semantica and old release ZIPs. Update matching instructions, capability/version/companion pin only to the scope actually observed. Build new content manifests and new paired ZIPs after behavior is final; extract into retained clean directories and run all suites/verifiers again. Review the actual final diff and raw receipts independently.

CHECK: source and extracted-package suites, source/hash/prefix preservation, exact native receipt validation and adversarial final review.
EXPECT: matching candidate ZIPs, manifests and verification report with honest ordinary-local scope. Native merges, full backend enforcement, strict expiry-before-save, broad Gate B acceptance and installed/production activation remain unqualified. Publication and installation need separate approval.

## Current evidence

Source commit ad3f66e4cd885494cf5d4b10453d089288d7c517, tree003cf1770d86b684462ca6feb50060b8f9e7a280: all 401 tracked blobs matched the captured source bytes. Baseline suites were executed before behavior edits: MI legacy21 passed, CM legacy21 passed, CM v2190 passed, repository19 passed, eval10 passed. MI v2374 ran with two failures, one error and54 skips: Windows short-path identity and descendant-pipe containment. These are pre-existing observed failures in this host; they are not counted as passes and must be explained/closed for the exact final release environment.

No revised native fence case has passed at this checkpoint. The approval removes the old contract blocker, not the need for native proof.

## Continuation checkpoint

The exact 14 October continuation state and retained test receipts are in practical-resume-20261014.md. The predecessor mutation/consumer route is stopped after review; the lease-bound replacement contract and SQL template are offline-tested, not integrated or native-qualified. CM recovery was repaired and rerun. Independent agents cannot resume while workspace agent credits are exhausted. Public CLI integration and exact source/package completion remain unfinished; no stage is marked complete from the focused passing subsets.

## 14 October remaining-build refinement at 58a737a

Status: PLAN_CREATED; IMPLEMENTATION_AND_NATIVE_QUALIFICATION_STILL_PARTIAL. This dated refinement belongs to the existing P1-P5 campaign, not a second scheduler or authority store. Earlier checkpoints above and in practical-resume-20261014.md remain historical evidence. Where they say the v2 schema is wholly absent, the source observation below supersedes that implementation-status statement, not its unqualified-runtime verdict.

TARGET: finish the approved ordinary-local, real-lease-bound protected adapter and its actual Memory Integrity/Claude-Mon consumer, then verify and package the exact matching pair. The practical contract authorizes only while the original lease is live, but allows that already-authorized transaction to finish saving later. It does not satisfy the earlier strict expiry-before-save requirement.

### Verified starting point

- Local HEAD: 58a737a6eeb02f2a9eb4061d5d324b78671bd99b; tree affc732170445513bf8eff75814beaf4f6e715b8; branch development/r5-practical-fence-wip-20261014. Git reported no tracked or untracked changes before this plan edit, with warnings that the home Git ignore file was inaccessible. Remote publication was not rechecked in this planning turn; the supplied report says nothing was pushed.
- Relative to adbbe1b, this commit modifies practical_lease_sql.py and adds test_practical_v2_schema.py only. It does not activate a replacement backend, consumer, CLI, qualification flag or release.
- Fresh focused runs: 21 Memory Integrity v2-schema/lease-contract/lease-SQL/quarantine tests passed; ten companion practical-journal tests passed; four retained runtime-policy tests passed. These are offline evidence, not native SQL execution or crash proof.
- A separate fresh predecessor/backend/consumer/CLI run executed 21 tests with one failure and ten errors. Mutation entrypoints remain quarantined, consumer fixtures use the older selection contract, and practical-title/practical-reconcile are absent from the public workflow. Do not remove the quarantine merely to make those old fixtures pass.
- No full source regression run, native executable invocation, database initialization, process termination, package build, install, commit or push occurred in this planning turn.

Load-bearing primary evidence and discrepancies:

| Observation | Source location | Consequence |
|---|---|---|
| The grant CREATE TABLE lacks lease_node, lease_granted_at, lease_expiry and lease_heartbeat, but the title authorization query reads all four. | memory-integrity/scripts/hybrid_bridge/practical_lease_sql.py:41 and :217 | The schema and builder are not yet an executable pair; add a schema/query correspondence regression before native execution. |
| The new grant seeds accept a caller deadline and insert issue_revision=0/status=GRANTED; they do not mint/update a real native lease or the issue row. | practical_lease_sql.py:86 and :117 | Treat them as unqualified grant-table builders, never as evidence of a native claim. |
| No v2 namespace-mint/readback or v2 dolt_ignore setup exists in this builder. Its title predicate reads stored metadata. | practical_lease_sql.py:41 and :196 | Prove DB-owned namespace identity and actual ignored-table configuration before issuing a usable ticket. |
| The predecessor writes raise before dispatch and the consumer raises before registration. | practical_backend.py:243; practical_consumer.py:52 | Implement a reviewed lease-bound successor path; retain predecessor refusal and its regression tests. |
| The pinned Beads lease invariant removes the active lease row when a claim ends, while human scope excludes file/data deletion. | upstream-beads-v1.3.1/internal/storage/issueops/lease.go:164 and :191; practical-fence-contract.json:9 | Release/unclaim/reclaim need an explicit compatibility decision; grant tombstoning alone does not satisfy both constraints. |
| Protected expiry guards cannot safely delegate to stock heartbeat: its UPDATE has no live-expiry predicate and its fallback can re-arm a lease. | pinned lease.go:354 and :392 | Own and test the protected heartbeat path; refuse missing, expired, spelling-mismatched and foreign leases without fallback. |
| Existing R5/m13 builder/verifier in M7-final-05730c7 require qualified native merges and a different four-trap set; the verifier uses TemporaryDirectory cleanup. | older release/Build-Memory-Integrity-R5.py and Verify-Memory-Integrity-R5.py | Preserve both originals. Adapt reviewed successors to this narrower scope and retained extraction; do not run the old pair unchanged. |
| Source preservation tests and CI choose only R4/R3/R2 content manifests. | both packages/tests_v2/test_preservation.py:23; .github/workflows/ci.yml | A new R5 manifest alone cannot make exact-source checks correct. Select the current release explicitly while independently preserving/verifying historical packages. |

### Authority and non-goals

APP-PRACTICAL-ISOLATED-P1-P5 already covers the isolated local build, new disposable tests and termination only of retained own client/server processes. The human quote is "Adopt practical contract + approve isolated stages 1-5" as rendered here; the exact original quote remains in approvals.json and practical-fence-contract.json. Do not ask for duplicate approval for native tests, internal native-role review or necessary P1 control definitions within that scope. This request creates the plan only; it is not an instruction to start those experiments now.

Installs, new toolchains/services, real/shared database changes, external AI consultation, new commits, pushes and installed-copy replacement remain separate authority boundaries. A plan edit does not grant any of them. A new mechanism or changed deletion rule must return to the user; no scope-changing waiver is inferred.

Keep every existing file, database, receipt, stopped candidate and prior release. Retain unique run and extraction directories even on failure. No cleanup, recursive deletion, reset, history rewrite or ACL/safety-gate bypass is part of this route.

The done label is a narrow protected-adapter capability on one selected local permanent-issue database, main branch, and the verified no-dependency scratch path. It is not full M7/R5, arbitrary raw bd/SQL enforcement, generic native acceptance, native branch merging, replication, power-loss proof, standing shared-database authority or installed readiness. Those unresolved broader outcomes must retain their own requirements and false/unverified labels.

### Decision and alternatives

| Option | Mechanism and principal failure mode | Fit / cost / reversibility |
|---|---|---|
| No native build: retain the proven offline tools and the stopped candidate. | No new native authority; no stale-write protection is claimed. | Safe and lowest cost, but does not deliver the requested native capability. It is a reduced-scope alternative, not automatic completion. |
| Recommended: finish the lease-bound single-transaction protected route plus CM intent/readback. | Exact-current never-reused grant, original lease facts, shared issue conflict cell, effect and exact backend receipt in one transaction. Main risk is a stale transaction or incomplete rollback surviving the backend boundary. | Smallest continuation of approved work; reuses pinned binaries and journal; fail-closed disablement retains all history. Conditional on native atomicity and fencing proof. |
| Stronger future hybrid: extend/fork the native lease/storage integration so every supported writer uses a versioned authorization boundary. | Wider backend enforcement; risk shifts to maintaining and migrating a changed Beads runtime and every mutation path. | Potentially broader coverage, but new runtime/toolchain/migration/authority and maintenance burden exceed this approval. Not needed to prove the bounded protected route. |

RECOMMENDATION: take the protected-route option, cheapest falsifiers first. Do not begin with public CLI wiring or final packaging. Close schema/authority consistency and prove backend atomicity before investing in the larger integration.

WEAK LINK: the pinned backend must reject the old transaction at commit and preserve the effect/receipt pair across local crash/restart. Generated SQL text and grant uniqueness do not establish either property.

CHEAPEST TEST: first, a schema/query correspondence test exposes the missing lease columns without a database. After repair, run a minimal actual assertion/rollback probe and a synchronized old-owner transaction with positive and fence-disabled controls in one disposable database.

PIVOT: any protected stale committed effect, partial effect without its exact receipt, revived old request or ambiguous authority stops that candidate immediately. Retain negative evidence, keep qualification false, and obtain approval for a genuinely different mechanism. If only the environment blocks execution, repair or hand off the same reviewed pilot without weakening safety checks. After three failed correction cycles on the same issue, bank the evidence and re-plan; do not silently substitute offline-only completion.

CONFIDENCE: Medium in this completion order, because the approval, source discrepancies and offline behavior are directly inspectable. Native effectiveness remains UNVERIFIED: the decisive synchronized and crash falsifiers have not passed for this successor. No success percentages, confidence intervals or session-count promises are supported.

EVIDENCE FAMILIES: (1) direct human approval/constraints; (2) candidate plus pinned-upstream source, with copied documents counted in that same family; (3) measured offline runs, whose generated-text assertions are correlated with the implementation and do not independently prove native behavior. Future raw native commands and fresh-process readback provide the missing runtime measurement. Internal review is a challenge, not another runtime witness.

### Required decision: lease retirement without deleting data

Blocking for full P2 release/unclaim/reclaim. The deletion decision does not block offline closure or a non-deleting initial-claim probe. P1c remains blocked unless source inspection proves a semantically valid competing ownership transition that performs no prohibited deletion; otherwise explicit lease-row-deletion permission is required before Bob's arm runs.

- The pinned Beads contract requires removal of an active leases row when a claim ends. Keeping an expired row and merely tombstoning a grant does not meet that invariant.
- Under the current literal no-data-deletion constraint, refuse those operations before any mutation. Do not count P2 complete from those refusals: its approved required transitions remain open.
- Recommended decision if the user later permits it: retain an exact durable lease/history record, then authorize removal only of the disposable database's active coordination projection when the native invariant requires it. This is still row deletion and requires explicit permission; archival alone does not make it implicitly allowed.
- If no row removal is acceptable, the alternatives are an explicitly adopted smaller release scope or a separately approved runtime design that supports non-deleting retirement. Do not choose either silently.

### Execution order within the existing P1-P5 stages

The substeps below refine the existing tasks and stable criterion/test IDs; they are not new approved milestones. Proposed case names identify tests to implement, not tests already run. Before executing revised gates, update the canonical plan/test mappings, calculate their exact refined digests using the project's existing convention, and add an additive provenance record linking that basis and unchanged named scope to APP-PRACTICAL-ISOLATED-P1-P5. Reconcile state against that record. Preserve the original approval's quoted authority and historical digests rather than rewriting them. This records existing authority, not a new approval; a changed mechanism, deletion rule or expanded scope still requires the user.

#### P1a - close the schema and identity contract offline

Owner: backend implementer; parent owns authority and diff verification.

Surfaces: practical_lease_sql.py, practical_contract.py, corresponding tests_v2 files; existing Fable P1 mappings and this derived plan. Retain practical_sql.py/predecessor quarantine as historical, non-executable mutation material.

Build:

1. Reconcile every column/type/status used by the title batch with the schema and real issue/lease model. Specify one current grant for the selected task/claim incarnation; never infer it solely from a reusable actor name or an unconstrained set of grant rows.
2. Create/read namespace identity from the DB, then bind the selected database, main branch, node and complete selection. Missing/replaced metadata refuses. Caller-proposed operation/grant IDs are identifiers, not proof of authority.
3. Add and read back the actual local dolt_ignore entries for all v2 sidecar tables; do not pretend the CM SQLite journal is a Dolt table. Inspect working-set versus HEAD tracking explicitly.
4. Use one backend UTC authorization sample with a documented precision consistent with the approved contract and pinned native timestamp representation. Compare the grant's stored deadline/lease facts as well as the request and native lease; inconsistent copies refuse. Preserve strict less-than at the original deadline; before/equal/after remain distinct tests.
5. Protect normal adapter history operations against edits, deletion and ID rebind; verify history/checkpoint continuity. PK uniqueness or absence of a DELETE string is not a claim of DB-admin-proof append-only enforcement.
6. Define rollback/error behavior explicitly for every statement. A failed SIGNAL/cardinality/token collision must not be followed by a committing partial effect. NULL/unknown assertion values must refuse, not fall through SQL IF logic.

Gate TEST-PRACTICAL-P1, offline additions: schema/query column correspondence; DB-owned-identity contract; active-grant ambiguity refusal; unchanged original request digest/deadline; signed nonzero row-token validation; malformed/time/Unicode/duplicate-ID refusals; separate cardinality assertions. None promotes a native flag.

#### P1b - minimum real-lease claim and sealed native transport

Dependencies: P1a green; no new toolchain. This is the initial-claim and minimal ownership-change portion needed to create an honest P1 fixture, not completion of every P2 transition. If the selected ownership-change path removes a native lease row, settle the retirement permission decision before that case runs. Do not claim an arbitrary sidecar seed is a native ownership transition.

Surfaces: lease-bound successor backend/transport, request/receipt contracts, retained native_runtime.py/controller and focused tests. One owner edits shared backend/SQL files at a time.

Build:

1. In the guarded transaction, verify the exact open/unassigned permanent issue and absence of unauthorized existing claim state; mint DB-time lease facts with the selected 300-second TTL; set real owner/status, fresh shared row_lock, current grant, history and exact operation record coherently.
   Define the minimal legitimate ownership-change transition used by Bob in P1c with the same atomic issue/lease/grant/receipt protocol. Prove its basic current-owner effect before using it as the competing arm. Full P2 transition qualification still waits for the P1 fence gate; its minimum fixture implementation does not.
2. Bind real holder, node, granted-at, expiry and heartbeat snapshots into every request/receipt. A raw grant INSERT, caller expiry or revision zero is never claim proof.
3. Seal the production-shaped transport to pinned executables, exact physical approved scratch root, loopback server/database/main identity and one bounded SQL session. No public runner injection, shadowed trusted readback, arbitrary SQL, caller barriers or flags may fabricate native proof.
4. Parse actual pinned CLI output with a strict, tested result-set contract; retain stdout/stderr/exit/timeout. Unexpected diagnostics or missing/malformed output produce UNKNOWN, not retry or caller-created success.
5. Keep test-only synchronization in the reviewed retained controller. The command timeout must exceed its bounded pause; observe the actual SQL session/barrier rather than assume SLEEP timing proves a snapshot was held.

Gate: offline transport/refusal/receipt tests, then scratch native grammar and atomicity probes. Inject failures after issue update, grant update and receipt insertion; force a token collision, duplicate operation, wrong schema and wrong cardinality. Fresh readback must show no partial committed issue/lease/grant/receipt changes. Confirm the exact assertion routine used, not an incompatible pre-existing IF NOT EXISTS procedure. No DOLT_ADD/DOLT_COMMIT inside the SQL transaction.

If agent-host ancestor access fails, retain the blocked receipt with zero dispatched commands and prepare the same consistent, reviewed controller for normal PowerShell. Do not ask for another old host-only bootstrap, alter ACLs or skip the Beads safety gate.

#### P1c - falsify the actual fence before larger integration

Gate sentence to incorporate into TEST-PRACTICAL-P1 before claiming a native pass: alongside valid-owner success, a fence-disabled comparison must demonstrate that this schedule actually exposes the prevented stale effect.

Required paired native cases:

- Proposed test_p1_native_current_owner_applies: valid ticket succeeds through the same sealed path; fresh reader finds the exact effect/receipt.
- Proposed test_p1_native_held_old_snapshot_refused: Alice's actual transaction passes authorization and is held; Bob commits a new ownership/grant/conflict token; Alice resumes. Alice leaves no stale committed title/token/grant/history/op receipt, and Bob's result remains intact.
- Proposed test_p1_native_fence_disabled_exposes_stale_effect: use the same fixture/schedule with only the reviewed load-bearing fence mechanism disabled in the isolated test variant. Observe the stale effect that the enabled arm prevents. If unrelated checks also refuse the disabled arm, the control is inconclusive, not proof. Never expose this variant in the public skill or release.
- Proposed test_p1_native_authorized_before_deadline_finishes_later: authorization before the exact original expiry can finish later under the adopted practical contract; authorization at/after expiry refuses. Do not call this strict expiry-before-save proof.

Retain both client captures, barrier/session observations, before/after rows and a fresh independent reader. Stop on any enabled-arm stale effect. A positive control alone or a sequential stale precheck cannot close P1.

#### P2 - complete protected ownership and heartbeat semantics

Dependencies: native P1 gate passed; retirement compatibility decision settled for required ending-claim transitions.

Surfaces: successor contract/SQL/backend and its tests/controller. Retain the same shared conflict cell across initial claim, valid same-owner repeat, reassignment, expired reacquisition, heartbeat and authorized release/reclaim.

Gate TEST-PRACTICAL-P2:

| Required case | Observed result required |
|---|---|
| Valid initial claim and live same-owner operation | Real issue/lease/current grant agree; one permitted operation effect and exact receipt. |
| Live heartbeat | Only exact current, live, locally granted authority renews; shared revision changes invalidate old requests; already-issued deadlines remain unchanged. |
| Real 300-second expiry then protected heartbeat then old operation | Record DB time at actual expiry; heartbeat cannot revive the old authority and old operation cannot commit. Accelerated fixtures are extra tests, not substitutes. |
| Stock heartbeat extends expired lease without changing issue token | In a separate disposable arm, demonstrate the pinned behavior; the original protected ticket must still refuse because its original lease/grant/deadline binding changed or expired. Raw stock calls remain outside protected enforcement. |
| A-to-B-to-A and spelling-variant actor | Same actor returning receives a distinct current grant; old request and ambiguous spelling/foreign/missing node refuse. |
| Ownership/heartbeat changes between check and write | Synchronized native commit boundary refuses old protected work, not merely its next preflight. |
| Explicit fresh expired reacquisition | Fresh operation/authority and DB-minted lease; never reuses an old grant or original operation ID. |
| Release/unclaim/reclaim after approved retirement decision | Exact issue/lease projection and retained history satisfy both the chosen permission boundary and pinned semantics. |
| Dependency-bearing, wisp, foreign, close/import/restore/batch routes outside coverage | Refusal before mutation; no blanket native coverage claim. |

Exact-current never-reused grant equality is sufficient as a proposed ABA discriminator; numeric monotonic ordering is not an invented requirement. The issue row_lock is a conflict token, not a grant counter. Prove currentness and non-reuse across processes; a UNIQUE key by itself is insufficient.

#### P3 - integrate the public skill with the protected companion journal

Dependencies: P1/P2 proven for the supported scope. The scratch harness may run earlier; integrated skill qualification may not.

Owner/surfaces: parent consumer/CLI owner for practical_consumer.py and memory_integrity_workflow.py; companion owner for complete_read_v2/ledger.py. Coordinate changes to the exact shared binding schema, not parallel incompatible rewrites.

Build and gate TEST-PRACTICAL-P3:

1. Register current work and derive the no-dependency scratch policy/CAS observation internally. Reject missing/stale/revoked/foreign prerequisite or selection state before consuming execution authority, and repeat the native dependency guard in the transaction.
2. Extend CM's immutable intent binding to all real lease facts and exact command/backend op identity. Reserve before any native write. Two independent connections/processes must produce one dispatch winner.
3. Internally read the exact backend operation after execution; do not accept dictionaries, fabricated guards, matching titles, status or in-memory caches as proof. Try injected runner, subclass/shadowed reader, wrong task/grant/node/digest and rebound-ID attacks through the actual public entrypoints.
4. Wire explicit practical-title and read-only practical-reconcile routes with strict input validation and structured failure output. Missing input produces zero adapter calls, zero DB mutation and no self-declared qualification. Reconciliation never claims/heartbeats/refreshes/replays.
5. Rebuild old fixtures against the approved lease contract while retaining their original test intent and predecessor-stop tests. Do not simply add the missing node field and claim real integration.
6. Historical exact APPLIED proof remains history after later expiry/revocation, but never authorizes new/current work. Changed original binding refuses; uncertain delivery remains durable UNKNOWN.

Observe a real public-path current-owner run, stale/forged refusal and reopened-CM reconciliation. General cross-system Gate B acceptance and dependent native workflows stay unqualified; do not broaden the no-dependency proof into complete dependency enforcement.

#### P4 - actual in-command interruption and fresh-process recovery

Dependencies: P3 public path and exact binding stable. Owner: retained controller plus parent verification; no shared/system process termination.

Gate TEST-PRACTICAL-P4 uses synchronization/observed barriers for:

- Before-effect interruption, actual outstanding native-client kill, and after-effect/before-reply interruption. A Python exception after a successful returned command does not satisfy the in-command kill case.
- Separate termination/restart of only the controller's retained server process, covering transaction-not-committed and committed-effect-before-CM-readback windows.
- Fresh processes reopen native state and CM, validate the original exact operation, and reconcile once; a second recovery performs zero additional mutations or redundant terminal events.
- Fresh readback sees an atomic effect/receipt pair or no committed effect; mismatch/partial state stops qualification. Unavailable or ambiguous readback stays UNKNOWN and never replays the uncertain write.

Record retained child handles/PIDs, session/barrier proof, invocation/effect/event counts, command outputs and before/after source/runtime hashes. Merely restarting a server is not a native-command interruption test. No power-loss or multi-replica conclusion follows.

#### P5a - adversarial review and release-source closure

Dependencies: P1-P4 complete for the exact supported scope; no unresolved Required item silently omitted.

Use a fresh native Fable reviewer for actual code/diff/receipts; internal review is in scope, external AI calls are not. If review cannot run because credits/capability are unavailable, retain REVIEW_PENDING and do not replace it with self-review. Parent independently checks every load-bearing claim.

Run focused plus MI/CM legacy and v2, repository workflow tests, evals and Semantica regressions against a captured current source baseline. Reproduce Windows short/long-path identity and descendant-process/pipe containment issues on the exact release host; fix or explicitly limit release scope, never suppress failures or infer repair from another host's green result. No full-green claim while required behavior fails.

Resolve the manifest-selection architecture before building: current-source/extracted-package tests select the declared new content manifest; historical ZIP verifiers continue to check their own unchanged old releases. Keep R3/R4/Semantica artifacts intact. This removes the bootstrapping contradiction of trying to pass an old exact-content manifest against intentionally changed current source.

Review capability wording, companion API/pin and SKILL appendices before creating manifests. All broad/unsupported flags remain false. Only a specifically named ordinary-local practical capability may be marked qualified when its full exact-source proof bundle exists. No generic native acceptance or merge flag is enabled by this work.

#### P5b - retained exact-byte pair and verification report

Owner: parent release owner. Surfaces: matching SKILL appendices, capability/version metadata, companion contract digest/pin, both new content manifests, scoped builder/verifier successors, new ZIPs and release report; current-source CI/contract tests.

1. Preserve original instruction prefixes and every baseline function/file unless an approved change explicitly accounts for it. Keep older builder/verifier scripts and archives unchanged.
2. Create a collision-free successor release identity and output names for the practical scope; do not overwrite an earlier R5 candidate or assume its hard-coded m13 version/digest/trap truth is applicable.
3. Bind a qualification evidence index to exact source files, controller, runtime binaries, every required raw receipt/hash, contract and scope. Verify those bytes before deriving capability metadata.
4. Generate both content manifests after source/metadata behavior is final; exclude only the manifest's self-hash and documented forbidden cache/runtime/data material. Missing source or leftover secret/DB/executable fails packaging, not permission to delete evidence.
5. Produce deterministic paired ZIPs, exactly one SKILL.md each, safe unique member paths, companion digest and manifest/report. Retain failed candidates in uniquely named locations.
6. Extract both ZIPs into a new retained directory; check hashes, original prefixes, complete content identity and all packaged suites. Run the packaged public workflow, not only imports/help. Repeat the deterministic build and compare archive hashes.
7. If source/controller bytes change after qualification, invalidate the affected proof and rerun it before regenerating final artifacts. Metadata/report-only changes still require exact-package verification.

Release acceptance: all required source and extracted-package checks pass, independent review has no unresolved blocking finding, retained native receipts prove the exact supported behavior, and flags/report accurately exclude unproved capabilities. Deliver the build as VERIFIED_CANDIDATE_NOT_INSTALLED until publication/installation separately occur.

### Publication and installed use: outside P1-P5 authority

After the verified pair exists:

1. Request separate local commit approval for the exact final diff; then separate push/publication approval. The earlier WIP commit request is not perpetual permission.
2. Recheck remote main/branch identity and Semantica drift. Integrate non-destructively, with no force push/reset; any behavior change invalidates affected source/native/package proofs. Verify the exact final published commit and ZIP hashes.
3. Run Windows/Linux CI and relevant Semantica/package/native jobs against that exact SHA. Existing CI passes or old native pilot jobs cannot certify this new lease-bound protocol. A new publication/CI repair commit requires exact-SHA re-verification.
4. Ask separately before replacing installed copies. Preserve the prior pair and histories without deletion; verify installed bytes and companion digest, run an installed supported-workflow smoke test and rehearse rollback to the retained pair.

Public qualification is not installed qualification. Complete use of the whole originally requested M7/R5 feature set still also requires its separate Gate B, integrated native merge/conflict/recovery and adopted four-trap comparison proof. Do not relabel that wider unfinished campaign as complete merely because this narrower pair ships.

### Resources, checkpoints and stop rules

- One backend/SQL owner at a time; one companion-journal owner; parent owns integration, authority, retention, native controller and release. Read-only independent review can overlap inspection, not approval of unseen future code.
- Reuse standard-library Python, pinned Beads v1.3.1 and Dolt v2.4.1. New drivers, Go toolchains, services or changed runtimes require approval rather than becoming surprise prerequisites.
- Capture each reviewable substep's HEAD/dirty state and target hashes before edits; recheck for concurrent changes. Retain stdout/stderr, exact test counts, raw native commands, command/source/runtime identities and next resume action.
- Real TTL cases require actual time, not client deadline injection. Use interruptible/polled long-running tests and keep user updates available; no unbounded blocking sleeps or invented timing guarantees.
- Do not fund consumer, crash or packaging work after P1 falsifies the mechanism. Diagnose one concrete failure with changed evidence; after three failed cycles re-plan. Do not equate exhaustion of a session/credits with completion.
- End every substep with its criterion coverage, observed tests, native gap, retained evidence path/hash, unchanged rollback artifacts and precise next action. All earlier negative/REFUTED results remain available.

### Recommended immediate next action

Begin P1a's failing schema/query correspondence test and finish the executable v2 schema/identity/initial-claim design under the existing approval. Define the P1 fence-disabled control at the same time, before any passing native result is presented as fencing evidence. Keep backend/consumer dispatch stopped until that successor is internally consistent. Resolve the lease-retirement permission question before claiming full P2 completion. This plan creation itself starts none of those implementation or native actions.

### Fresh read-only architecture challenge

A fresh native Fable Sol reviewer completed a read-only source challenge during this planning turn and returned FIX-FIRST for the current WIP, not a runtime qualification. It independently identified the schema/query contradiction, sidecar-only minting, missing single-current-grant invariant, clock/transition gaps, lease-deletion authority conflict and scoped release-builder problem. The parent checked those load-bearing issues against source; the refinement above includes their closure gates. Final code/receipt review remains required after implementation.

The review advised "Resolve authority before native work." This plan preserves that restriction for any case whose native transition would remove an active lease row; offline consistency work and a non-deleting initial-claim probe do not consume that missing permission. Never use the distinction to run a deleting handoff, unclaim or reclaim implicitly. The first ownership race must use an explicitly permitted, semantically valid competing transition, or remain blocked.

## 2026-10-18 — next-step plan: retain original execution diagnostics

Authority: the user requested, "complete the next required step after created a best deep plan". This authorizes this bounded local code/test/documentation successor, not a native run, installation, release, commit or push. Existing P1-P5 acceptance criteria remain open. Fable is the only governor and this existing document is the plan; Superpowers supplies debugging, test-first and verification practices.

### Decision and observable target

Fix the observed loss at the sealed transport -> CM UNKNOWN -> worker -> controller boundary. A failed or timed-out mutating invocation must retain bounded original output bytes, exit/timeout classification, exact selection/request/SQL identities and capture completeness in the existing protected CM history. The parent controller must read that history independently rather than trust a worker's supplied cause. Diagnostics alone must never authorize replay, APPLIED, a fence-refusal verdict or any qualification flag.

Options: documentation-only is reversible but leaves the diagnostic loss; a new fence/service would add a mechanism and authority surface without addressing this first; a bounded transport observation bound into the existing UNKNOWN reason is the smallest adequate repair. Choose the existing-journal route: no second authoritative ledger, database migration, callback injection, driver install or SQL predicate change.

Constraint challenge: the consumer deliberately swallows delivery exceptions and reads back, so exception attributes alone cannot survive the worker boundary. Existing protected UNKNOWN reasons can retain the packet without changing the companion's history schema. Cost challenge: do not rerun native experiments or broaden packaging while command failure remains unattributed. Falsification challenge: invalid bytes, timeout, truncation, wrong operation/SQL/selection, forged worker fields and an unrelated error that mentions a fence code must not become proof. Implementation and mocked process tests are one correlated evidence family; real pinned-runtime diagnostics are the still-missing independent observation. Confidence in the bounded design is medium until its red/green and connected regressions run; native safety remains unverified.

### Scope and file ownership

Parent owns this successor: new `memory-integrity/scripts/hybrid_bridge/practical_execution.py`, its focused tests, transport integration in `practical_lease_backend.py`, controller readout in `practical_race_controller.py`, and the existing Fable state/resume/handoff annotations. Reuse `LeaseScratchBackend`, generated SQL, `mark_practical_native_unknown`, canonical binding and protected CM events. The consumer, companion engine, SQL builders/predicates, SKILL instructions, capability flags, old manifests/packages and Semantica implementation remain unchanged.

### Implementation checklist and verification

- [x] Baseline: retain HEAD, clean status, target hashes and all pre-edit file hashes in a new uniquely named local evidence directory. Recheck before edits.
- [x] Red: prove a real backend failure currently loses non-UTF8 stdout/stderr, exit status and invocation identity in its durable UNKNOWN reason. Use the real in-memory CM journal/backend and mock only the unavoidable subprocess/physical-host boundary.
- [x] Transport: capture byte prefixes (64 KiB per channel), original byte lengths and full-byte SHA-256 values. Record missing/non-byte output explicitly; timeout is not an engine rejection. Keep command arguments out of generic exception strings; record executable/runtime pin, loopback/db/main selection, SQL hash and fixed transport options. No credentials/environment values are serialized.
- [x] Journal: bind the observed command packet to the original exact immutable intent and generated SQL in the protected UNKNOWN reason before the exception can be swallowed. Preserve the single durable dispatch and readback-only recovery; no additional terminal event on retry.
- [x] Reader: add a read-only diagnostics query over exact practical events. Verify history integrity, operation binding, command identity and packet hashes; missing/ambiguous/foreign data is unavailable diagnostics, never permission to resend. Expose diagnostics as observations, never a fence verdict.
- [x] Controller: attach independently read CM diagnostics to Alice's observed result. Ignore worker-provided capture/cause fields. Leave `stale_refusal_attribution` and the canonical verifier unchanged.
- [x] Adversarial green: prove original bytes survive through UNKNOWN/readback and a reopened CM connection; wrong binding, malformed Base64, corrupt hashes, duplicate command, timeout, truncated bytes and caller-created cause cannot create APPLIED or qualify a run.
- [x] Regression: run current 70-case focused baseline, stopped-predecessor gates, practical consumer/journal tests, connected race tests and CLI refusal checks using retained fixtures. No deleting cleanup or native executable. Compare failures with the preserved baseline rather than relabeling blocked checks green.
- [x] Continuity: preserve the old handoff's original bytes as a prefix, append an explicit historical/superseded warning and point to the existing resume record. Update that resume/state with exact evidence and remaining gates, without changing historical receipt hashes.
- [x] Review/hand-off: inspect the actual diff, source stability, unchanged protected files and recurrence sites. Attempt a fresh read-only Fable reviewer; unavailable review remains PENDING, never substituted with a claim of independence. Save the observed verification report and hashes in a new evidence location.

Observed closure of this bounded substep: 275 MI checks (274 pass plus the unchanged expected-failure placeholder), 18 CM checks and 9 CLI checks; zero unexpected failures/errors in the final groups. Retained-fixture offline evidence only. The fresh reviewer attempt failed for workspace credits and is still PENDING, not completed. Parent verification report: `docs/fable/evidence/execution-diagnostics-20261018/verification.md`. Native cause/proof and parent P1-P5 gates remain open; no release or merge readiness follows from these checkboxes.

Cheapest falsifier: an unrelated process failure with fence-like text must still produce durable UNKNOWN and canonical INCONCLUSIVE after diagnostic capture. Pivot: if preserving diagnostics requires changing SQL authority, adding an evidence-as-authorization seam or changing the companion event schema, stop and revise this plan before building that larger mechanism. A captured SQL diagnostic is not yet proven execution causation: interpreting actual pinned-runtime diagnostics and real native grammar/rollback/paired race remains the next separately gated proof milestone.

No guarantee of zero defects is made. Completion of this substep means measured diagnostic preservation plus unchanged refusal/no-replay safety, not complete M7/R5, a releasable skill, native qualification or installation.

## 17 October 2026 — authorized offline integration repair

The current human request authorizes finishing and saving bounded offline
implementation, regressions and existing evidence records. It explicitly
excludes native database experiments, new fences/authority stores, deletion,
agents, external AI, installation, Git commits/pushes, workflows, publication,
release manifests, packages and installed-copy replacement. This narrower
authorization governs this run; the older native stages above remain open.

Arrival was observed, not inferred: HEAD
3ea23556fd336ba64a3ebcf6b4fc169e71051d11, branch
development/r5-practical-fence-wip-20261014, ten modified tracked files and
five untracked files. Effective writes were demonstrated by a retained probe.
All 501 arrival files were hashed; intended source/evidence targets were
snapshotted and rechecked before writes. The supplied primary review was read
completely, SHA-256 61303dcd9331865434e9dd62eead6875c42d697da5c94d5a6d61997bef7aef3d,
and its claims were reproduced against the saved source.

INTENT: remove false execution-cause attribution and connect the existing
successor's producer/consumer contracts. UNKNOWN plus current staleness cannot
establish which predicate an earlier operation reached. Current authority,
delivery, execution cause, backend effects and companion terminals remain
separate observations. No new rejection-evidence mechanism was introduced.

The four approved local steps were: reproduce/correct attribution; repair
identity and result propagation; share transfer invariants and drive the real
offline sequence; verify and update this campaign's evidence. They were
executed autonomously under the user's approval, without another milestone
approval request. These are refinements of the existing practical campaign,
not new native-stage approvals or a second governance store.

Decision: keeping the review-only/no-build state would retain a reproduced
false PASS. Repairing the existing driver, worker and canonical verifier is
the smallest adequate option. A stronger hybrid with another fence, authority
store or new rejection protocol is outside this approval and was not built.
The remaining weak link is native execution-cause evidence. The cheap
falsifier was the unrelated-transport-failure sequence: it first PASSED, and
now reaches the canonical verifier as INCONCLUSIVE/REFUSAL_UNKNOWN. Native
cause, SQL grammar, atomicity, races and durability remain UNVERIFIED.

| Bounded criterion | Saved implementation and measured regression |
|---|---|
| OFFLINE-A: no false causal PASS | stale_refusal_attribution and actual resume_alice/run_race; RefusalCausationRegressionTests, including caller-created cause refusal |
| OFFLINE-B: one namespace/selection | bootstrap UUID readback and independent identity validation before registration; NamespacePropagationRegressionTests and connected setup |
| OFFLINE-C: actual operation identities | actual Alice packet, schedule, barrier, worker outcome and journal binding; actual post-claim transfer packet retained; OperationPropagationRegressionTests and connected binding assertions |
| OFFLINE-D: explicit observation contracts | actual physical schema map (including dependencies), nested Beads shape, complete backend receipts and CM event bindings, preserved claim records, S2 mapping before controls; ObservationContractRegressionTests and connected packet assertions |
| OFFLINE-E: complete applicable S1/S2 invariants | one shared committed-transfer validator, frozen lease/grant facts, tombstone, pointer/revision, token/history/operation agreement and preservation; Shared/AdditionalScripted/CompleteTransferRelationshipTests |
| OFFLINE-F: connected sequence | six FullSequenceOfflineTests drive actual driver/builders/worker/consumer/ledger/verifier; one fault test contains sixteen fault subcases; only native physical/process boundaries are modeled |
| OFFLINE-G: broader differences accounted | observed 501-file baseline copy verified byte-for-byte; adapted MI v2 615 to 642 with unchanged existing outcomes; adapted CM v2 208 to 208 with unchanged existing outcomes; all failures/errors retained |
| OFFLINE-H: honest campaign records | this section, state.json, GATES-lease-reassign.md and the WIP correction; broad/native/release/independent-review gates stay open |
| OFFLINE-I: saved bytes and preservation | acceptance-source.json, verify_saved.py, final inventory and Git diff checks; every arrival file retained and unrelated dirty changes unchanged |

Bounded status: OFFLINE_REPAIR_VERIFIED_NATIVE_UNVERIFIED. This does not close
P1-P5, full regression/release acceptance, public claim qualification, native
fencing or installed readiness. The claim remains a mechanism-only direct
sealed-backend step because the public consumer exposes no claim dispatch.

Evidence is retained under docs/fable/evidence/offline-repair-20261017:
baseline.json, immutable failing/passing receipts, acceptance-source.json,
connected-evidence.json (18 modeled cases), connected-fault-matrix.csv,
regression-comparison.json and repair-report.md. The report records exact
interpreter/CWD/commands, every remaining failure/error and source hashes.
The earlier six RealComponentIntegrationTests are retained as narrower
component coverage; they are no longer described as a complete workflow.

Rollback is retention plus disabled/unqualified use, not a reset or deletion.
The stopped predecessor, companion journal, practical timing contract and all
prior data/packages/evidence remain. No further implementation is required by
OFFLINE-A through OFFLINE-I. Independent review of the saved diff is pending;
any native experiment or release/install action needs separate authorization.

## 2026-10-18 - exact published repair review and next proof gates

### Target, authority and observed starting point

The user requested a deep plan followed by completion of the next required
step, identifying independent review before separately approved native
preflight/comparisons. The next review is now completed, not credit-blocked.
The reviewed range is fbabbab5e69e924ac4aae6c3a4fb6de62aae3d55 through
0f1fe58b66a03e34244b1f2ac56e5588d2489eee. Arrival was a clean checkout on
development/r5-practical-fence-wip-20261014. This section supersedes older
next-action wording, not historical test results or approval records.

The fresh Fable Sol reviewer returned FIX-FIRST for the bounded diagnostics
repair. Parent reproduction confirms the finding. Normal CM reserve,
consume and mark-unknown APIs can store a schema-valid caller-created
diagnostic packet. The reader reports available/complete and echoes the
SEALED_DOLT_CLIENT label without any native invocation. Rehashed changes to
port and command digest also pass its self-consistency checks. No APPLIED,
replay, fence verdict or qualification is produced; causal_status remains
UNVERIFIED. Integrity and byte completeness are not producer authenticity.

Evidence: docs/fable/evidence/execution-diagnostics-20261018/review.md.
The existing TEST-PRACTICAL-P1/P2/P3/P4/P5 acceptance criteria stay open.
No lease timing, fence predicate, companion schema, native authority or
deletion rule is changed by this plan. No native run is authorized by saving it.

### Decision and alternatives

| Option | Mechanism / primary failure | Decision |
| --- | --- | --- |
| Keep the checkpoint unchanged | Preserve offline containment but leave misleading producer/identity claims | Safe as held WIP; cannot close this review finding |
| Explicit unauthenticated diagnostics | Separate self-consistency, byte completeness and source claims from authenticated origin; keep all diagnostics non-authoritative | Recommended smallest correction, pending human approval of that explicit contract |
| Protected producer attestation | Add a producer capability and independently expected invocation binding so ordinary reason writers cannot impersonate sealed capture | Stronger but changes the trust boundary; separate architecture approval, not a quiet follow-up patch |

The recommended correction does not pretend to authenticate data. It makes
the existing actual guarantee explicit and test-enforced. Native command
identity/cause must still be established by reviewed owned-process observations
and backend readback; no packet label or hash substitutes for those witnesses.

Constraint lens: CM deliberately permits caller-written uncertainty reasons,
so their hash-chained storage proves retention, not who ran a native command.
Cost lens: adding another authority/ledger would broaden a small review repair
and its failure surface. Falsification lens: the cheapest test is the exact
schema-valid public-API forgery already reproduced, not a forbidden extra
field. Code, generated-text tests and parent/reviewer probes share the same
implementation evidence family; a fresh analyst is an independent challenge,
not a second native-runtime measurement. Confidence is high in the reproduced
provenance limitation; native effectiveness remains UNVERIFIED.

Weak link: a future consumer may confuse complete bytes with authenticated
origin. Pivot: if authenticated producer/command provenance is required, do
not describe the recommended annotation as its implementation; return for the
stronger trust-boundary design. No new fence is started to close this finding.

### Review focus and completion checks

| Input / failure class | Required observable check |
| --- | --- |
| Canonical caller packet through normal CM lifecycle | Never reported producer-authenticated, never APPLIED or causally proven |
| Rehashed changed port/executable/timeout/command digest | Cannot be presented as independently verified invocation identity |
| Historical SEALED_DOLT_CLIENT packet | Retain original stored bytes; expose its label as a claim with unverified provenance |
| Timeout, missing/truncated output, foreign binding or SQL | Keep incomplete/unavailable and read-only semantics; no replay to improve diagnostics |
| Unrelated transport failure mentioning a fence code | Connected canonical result stays INCONCLUSIVE/REFUSAL_UNKNOWN |

### Sequenced tasks inside the existing campaign

#### R0 - exact-commit independent review (completed)

- [x] Inspect the exact ten-file diff without changing HEAD/index/source.
- [x] Obtain the fresh read-only Fable Sol verdict; do not substitute parent
  inspection or the old credit failure for this completed review.
- [x] Parent reproduces the supported-API forgery and changed-command case
  without native processes, DBA writes, introspection or module patching.
- [x] Re-run the focused groups: 275 MI checks (274 pass, one known expected
  failure), 18 CM passes and nine CLI preflight passes; zero unexpected errors.
- [x] Read/hash the existing Dolt/Beads binaries without executing them.

#### R1 - bounded offline provenance correction (approval pending)

Scope: practical_execution.py, diagnostic fallback metadata in
practical_race_controller.py only if needed for uniform output, focused
test_practical_execution.py regressions, and these existing Fable records.
Do not change the companion ledger, SQL predicates, protected consumer,
public CLI activation, release files or installed copies.

1. Obtain explicit agreement to describe these packets as unauthenticated
   diagnostics rather than introduce a sealed-producer guarantee.
2. Write the valid public-API forgery regression first. Its observable target
   is explicit unverified provenance even when capture_complete is true, no
   successful terminal event and no write/replay authority. Observe it fail
   because the provenance distinction is absent, not because a fixture broke.
3. Make the smallest additive output/wording correction. A new source label
   must describe a claim; historical labels/packets remain readable and
   unmodified. Producer authenticity and independently verified invocation
   identity must never be asserted by a self-hash. Preserve byte-limit,
   missing/timeout/truncation, immutable-binding and SQL-digest checks.
4. Add separate malformed/rehashed invocation and legacy-packet cases, then
   exercise the real backend -> journal -> controller -> canonical verdict
   chain with only unavoidable process boundaries modeled.
5. Run focused MI/CM/CLI plus the safe largest feasible broader suites against
   a captured exact pre-fix baseline. Retain fixtures, blocked actions and
   named failures; a baseline-compared/adapted run is not unchanged green CI.
6. Obtain fresh read-only review of the saved successor and reproduce its
   findings. Only then close R1. No automatic commit/push follows.

#### R2 - pinned native grammar and forced-rollback preflight (gated)

Dependencies: R1 accepted; exact helper/source bytes reviewed; explicit
native-test approval. Reuse existing binaries, not a replacement toolchain:

- Dolt: work/R4-memory-integrity/runtime/dolt-v2.4.1/extracted/dolt-windows-amd64/bin/dolt.exe
  SHA-256 ca21a9d1dab233a694b99ad0be9e78590967a1cc2773eb202fa0dd2929239ba2.
- Beads: work/R3-memory-integrity/runtime/beads-v1.3.1/bin/bd.exe
  SHA-256 ac5b60114e5e7ef9de8878b45fc35941937341d3447366c99bc91c81557be7a4.

Paths above are relative to C:/Users/sakth/Documents/Codex/2026-10-02/ad.
Read/hash checks passed in this review turn; no version/native command ran.

Use one new retained UUID run below the already approved physical scratch
roots, ordinary Beads safety checks, private loopback server, no hooks/shared
DBs/credentials and only owned process handles. Refuse reused/foreign stores.
The reviewed helper must bind exact source/helper/binary/command hashes and
raw status/output before any test execution; no old helper is assumed ready.

Test the actual schema, procedure body, namespace/selection readback,
database/main identity, result-set shape and timestamp representation. Confirm
the assertion routine actually installed, not merely IF NOT EXISTS returning
against a different body. Force a known mid-transaction assertion failure and
separate late failures after issue update, grant/history update and operation
receipt insertion. Include token collision, duplicate operation and cardinality
failures. Use harness-only fixed fault points, never an arbitrary-SQL public
entrypoint. Fresh independent connection readback must show either the full
allowed effect/receipt pair or no durable partial effect; CLI exit alone is
insufficient. Retain every failed run; never retry an uncertain operation.

No DELETE/DROP, lease release/unclaim/reclaim, cleanup or file overwrite is
allowed. Stop only owned local processes and preserve files. Transaction
rollback is the behavior under test, not permission to remove prior data.
Any unsupported grammar, unexpected diagnostic, lost handle or ambiguous
effect is BLOCKED/INCONCLUSIVE, not a fence pass. A partial committed effect
refutes the tested candidate and stops the ladder.

#### R3 - enabled/disabled/valid-owner comparison (gated after R2)

Map to TEST-PRACTICAL-P1. Observe Alice's real authorization snapshot/session,
commit the legitimate Bob transition, resume Alice, and independently inspect
S0/S1/S2 issue/lease/grant/history/token/receipt/CM records. Prove the competing
transition satisfies the no-deletion scope before allowing that arm. Enabled
stale durable effect stops the candidate. A proper refusal requires observed
native causation, not UNKNOWN plus current staleness or captured error text.

Require a valid-owner success and the explicit harness-only disabled bundle
to expose the stale effect. Record exactly which predicates/token/history
checks the disabled arm removes; that is a bundle comparison, not proof about
one isolated check. An unrelated failure or non-executed control is
INCONCLUSIVE. No disable-fence switch enters the public workflow.

#### R4 - heartbeat/ownership-return, then real interruption (later gates)

After native P1 acceptance, map the real DB-time expiry/heartbeat and A-B-A
or spelling-variant cases to TEST-PRACTICAL-P2. No accelerated or mocked clock
substitutes for actual lease expiry. Release/reclaim cases stay blocked by
the unresolved lease-row-deletion decision; never silently change that rule.

After the protected consumer/public path and exact operation binding are
qualified, map actual outstanding-client interruption and separate owned-server
crash/restart to TEST-PRACTICAL-P4. Retain the inside-command barrier, owned
handles and before/after rows. Fresh-process readback uses the original
operation only; repeated recovery produces no new native write or terminal
duplication. A server restart or Python exception after return is not this test.

### Preservation, stop and release boundary

No production/source behavior was changed while creating this review plan.
All historical reports, failed candidates, raw receipts, manifests, packages
and installed skills remain. Current native/release/installed flags remain
false. The review/probes are not a whole-M7 verdict. Gate B, native merges,
four-trap comparison, broad regression closure, final packages, exact-commit
CI and installed smoke/rollback retain their own unmet gates.

Stop at any unapproved transition, scope-changing defect or unsafe enabled
effect. Three failed evidence-changing corrections on one mechanism require
re-planning. No promise of zero defects, fixed number of sessions or full
completion is substituted for the observations above.

### R1 authorization and execution ruling

After the specific offline-provenance approval question, the human answered:
"do whichis best, i just want to use this best skill to work to over come memory
and chunk and embedding issue while performing big and large and complex task
and coding and developing, dont remove any wanted and important file or detail,
i added most of best behaviour from various skill to make this hybrid skill.
give me what i expected".

This accepts the recommended bounded offline correction, not a new native
experiment, installed replacement, provider call or publication. The product
priority is usable memory/chunking/recall/embedding support with honest limits,
not an unbounded Beads detour. Existing hybrid functionality/files stay intact.

Ruling: implement R1 inline in the current isolated development checkout,
using this existing Fable plan as the ledger. Do not create another governor,
plan store, Git worktree or commits. No cleanup/deletion step from a generic
execution skill applies under the user's explicit preservation constraint.
The evidence contract is unauthenticated diagnostics: completeness refers to
retained bytes/status, not producer authenticity or independently checked full
invocation. New labels say DECLARED_DOLT_CLIENT; old SEALED_DOLT_CLIENT packets
stay readable verbatim. Both available and unavailable outputs explicitly
deny producer authentication and independent invocation verification. There
is no claim that a real caller packet is distinguished from a valid forgery.
Cost if the stronger guarantee is later required: a separately reviewed and
approved protected producer design, not reinterpretation of these flags.

Execution checklist:
- [x] Observe five provenance regressions fail against the pre-fix source.
- [x] Make the minimum diagnostic-label/output correction, preserving old APIs.
- [x] Repeat the focused groups and baseline-compare safe broader suites.
- [x] Fresh reviewer checks the exact saved successor; parent verifies findings.
- [x] Record exact source/test evidence and remaining native/usefulness gates.

R1 observed execution: 21 diagnostic tests red (five new failures) -> 21 green;
280 practical MI cases (279 passes and one known expected failure), 18 CM and
nine public practical CLI passes. Across 942 broader adapted cases per phase,
only those five failures closed and no new failure/error IDs appeared. Broad
suites are not fully green: old failures, guarded operations and frozen
manifest drift remain explicitly reported, not waived.

User-goal verification additionally observed the original public offline
workflow in fresh Python children: four fixture-based recall/resume/input-
refusal checks passed. A synthetic 50 MiB source reassembled exactly from
801 primary units/200 chunks and detected a missing primary. These prove
mechanical partition and bounded offline persistence, not semantic/model or
embedding quality. Evidence and exact hashes:
docs/fable/evidence/execution-diagnostics-20261018/provenance-correction.md.
Source is frozen for final review; no new commit/push or install is authorized.

R1 closure: the fresh saved-diff reviewer returned SHIP, no blocking/moderate
finding for the approved offline contract, nine independent selected no-write
checks passing. Parent acceptance is VERIFIED WITH CAVEATS after direct
reproduction and the retained evidence checks. Minor short-docstring wording
is recorded/deferred. R1 is complete; neither the native ladder nor the whole
memory skill/release/installation is declared complete. The next useful track
is task-relative core usability/retrieval/embedding acceptance and release
qualification, with optional native capabilities still disabled and tracked.

## 2026-10-18 - N1 core-memory acceptance: approved bounded plan

AUTH: the user requested "COMMIT IT AND THAN" followed by completion of the
next required step after a deep plan. The reviewed eight-path provenance
correction is locally committed as 6c5ba969feecabcdb1c05be12de41512aec01220.
Nothing was pushed. Then the user explicitly selected "Approve N1 acceptance
harness and local tests (Recommended)" in response to the bounded N1 card.
That approval covers this test-only milestone, not additional product behavior,
native execution, model installation/inference, releases, pushes or installation.

### Target, spec and architecture

Goal: observe whether the existing offline-run/verify consumer can retain and
reopen a bounded coding-source bundle without coverage loss, duplicate resume,
stale recall or silent artifact damage. This is one reviewable acceptance
milestone, not a new memory service, directory ingester or embedding engine.

Spec: existing memory-integrity/references/r2-workflow.md, workflow facade,
integrity_v2/report.py and recall.py, and companion partition.py. Their public
behavior remains authoritative. Supplied review fixtures are TEST_ONLY; all/
every/total/absence queries enumerate units, other queries locate substrings.
Neither route generates an answer or proves semantic understanding.

Architecture: a standalone retained harness under the existing sibling
build-validation directory invokes the actual public CLI in separate Python
processes. Exact source copies, fixtures, stdout/stderr, exit codes, before/
after file hashes and commands stay private there. Repository production code,
SKILL instructions, capabilities, manifests and ZIPs are untouched. Existing
Fable plan/resume/state remain the only campaign control plane.

### Evidence and choice

Facts: public verification reopens CAS/SQLite and rechecks current source
digests; the consumer already exposes source excerpts, coverage denominator
and zero-write shadow projections. The prior four fixture tests/50 MiB
mechanical check passed. Existing lexical TF-IDF/LSA is not a learned embedding.
The earlier authored model experiment did not demonstrate coding benefit.

| Option | Mechanism / main failure | Constraint fit | Decision |
| --- | --- | --- | --- |
| No build | Repeat the three-line smoke; larger-source omissions remain untested | Lowest risk, inadequate new evidence | Retain as regression baseline |
| Retained public-path harness | Exercise real code excerpts and negative variants through offline-run/verify; curated fixtures can be mistaken for comprehension | No new runtime or product changes | Recommended and approved N1 |
| Learned retrieval/graph hybrid | Select installed model runtime and measure retrieval/coding outcomes; more dependencies and quality uncertainty | Requires distinct model/runtime authority and an evaluation specification | Later, not silently activated |

Constraints/feasibility lens: exact source bytes and declared unit coverage are
observable without AI; semantic correctness and native fencing are not.
Outside-view/cost lens: reuse the functioning facade and retained harness
pattern rather than another authority or service. A larger fixture is still
not representative production quality; report its measured size/counts.
Pre-mortem: a test only compares a manifest with itself, accepts an arbitrary
error as tamper proof, or mutates the original run. Independent byte oracles,
cloned variants, exact refusal codes and before/after inventories catch those.

Evidence families: source and existing tests are one implementation family;
fresh subprocess artifacts/readbacks provide a distinct measurement, but the
curated expected source and fixture interpretations remain authored together.
Fresh review is an independent challenge, not independent semantic ground truth.
Confidence in this bounded approach: Medium until the fresh public-path run
and its adversarial controls are observed; no numeric confidence is invented.
Weak link: fixture review quality is not comprehension. Cheapest falsifier:
reassemble every recalled original_excerpt against the exact bundle bytes,
then change a copied dependency and demand STALE with no recalled records.
Pivot: if the current consumer accepts stale/damaged evidence, retain a failing
receipt and stop for a bounded product-fix design; never weaken the test.

### Declared surfaces and preservation

- Create build-validation/Core-Memory-Acceptance-20261018.py: offline harness.
- Create collision-free core-memory-acceptance-<UUID> directories there only.
- Append evidence and progress to this plan and practical-resume-20261014.md;
  update docs/fable/state.json without closing parent P1-P5/native requirements.
- Produce docs/fable/evidence/core-memory-acceptance-20261018/report.md after
  observing the run; do not publish source excerpts/raw private receipts.
- Do not edit any existing package source, test, capabilities, manifests or ZIP.
- Do not commit N1 artifacts under the earlier eight-path commit authority.

Before writing, record Git HEAD/status and source-file SHA-256 inventory.
Recheck declared edit targets before editing and integrate concurrent work.
Every baseline file must remain; package source hashes must remain identical.
New scratch variants are created exclusively; no baseline file is overwritten
or deleted. Scratch SQLite may create its own transient internal files; this
is not cleanup authority over existing user evidence. Keep every failed run.

### Test contract and execution order

Harness interfaces: create_bundle(run: Path) -> (source: Path, provenance: list),
call(label: str, command: str, *args: str) -> (exit_code: int, output: dict),
check(name: str, callable) -> retained per-check result, and main() -> int.
Only fixed actual Python offline-run/verify and companion capabilities
commands may be invoked. No shell, arbitrary runner, provider, native binary,
network or cleanup operation belongs to the harness.

1. Copy four actual implementation/test files into a framed UTF-8 bundle with
   per-file original byte hashes/ranges: memory_integrity_workflow.py,
   integrity_v2/recall.py, companion complete_read_v2/partition.py and
   tests_v2/test_r2_workflow.py. Add one separately labelled synthetic Unicode
   line longer than 4096 bytes, to exercise child-span boundaries. Source
   frames preserve original bytes. This is a single explicit text-source
   consumer, not proof of automatic repository/multiple-source ingestion.
2. Build exact primary IDs with the pinned companion manifest; independently
   check contiguous half-open byte ranges, per-unit hashes, byte reassembly,
   unique/ordered IDs and exact-once primary assignment. Do not derive the
   expected excerpt text from the consumer's output. Fixture interpretations
   explicitly say structural TEST_ONLY retention, not semantic review.
3. Invoke the public offline-run in one process; reopen verify in distinct
   processes for exhaustive and locator queries. Retain raw output separately.
4. Apply negative variants only to newly created copies, then reverify the
   unchanged original. Never delete an artifact to simulate missing data:
   make a fresh clone that omits that artifact while retaining its mapping.
5. Re-run focused correction/companion regressions, verify source preservation,
   request fresh read-only Fable Sol review, reproduce load-bearing challenges,
   and write the observed verdict. Blocked commands are not passing checks.

Required acceptance cases (each gets its own check record):

| ID | Public observation and independent expected result |
| --- | --- |
| N1-A | Fresh exhaustive recall: IDs equal ordered manifest primary IDs exactly once; concatenated original_excerpt bytes equal the entire bundle; all file frame ranges/hash identities survive; result remains TEST_ONLY and semantic_answer_generated=false |
| N1-B | Locator: for literal code phrase and absent phrase, returned IDs equal direct byte-slice substring matches, not model-ranked guesses; exhaustive queries never shrink denominator to locator hits |
| N1-C | Unchanged resume: resumed=true; entire existing run inventory and ledger bytes unchanged, including after fresh-process verify; zero-write shadow remains |
| N1-D | Changed-source copy: verify against a new dependency-changed bundle returns nonzero, STALE, E_RUNMAP_STALE, no recall; original source/run remains current and unchanged |
| N1-E | Missing response-artifact clone: nonzero BLOCKED, E_RUNMAP_ARTIFACT, no recall; clean baseline read remains successful |
| N1-F | Corrupt response-artifact clone: retained bad bytes; nonzero BLOCKED/E_RUNMAP_ARTIFACT, no recall; rehashed fabricated content is a separate control, not hidden by the outer hash check |
| N1-G | Rehashed approval-tamper clone: after a fixture-only provider change and rebinding the cloned ledger hash, verify still refuses through the inner ledger/request proof; assert specific refusal, not arbitrary transport failure |
| N1-H | Non-vacuity: feeding expected-assertion helpers truncated recalled records or a fake successful stale/tamper response must fail their assertions; do not alter production code to manufacture red/green |

Core excerpt oracle:

```python
records = fresh['recall']['records']
assert [r['unit_id'] for r in records] == expected_ids
assert b''.join(r['original_excerpt'].encode('utf-8') for r in records) == raw
assert fresh['recall']['coverage_basis']['units'] == len(expected_ids)
assert fresh['recall']['semantic_answer_generated'] is False
```

For a refusal, assert nonzero exit, ok=false, the required overall and named
blocker prefix, plus absence of recall. Runtime/tool failure alone must be
reported FAILED/INCONCLUSIVE, not accepted as the desired stale/tamper refusal.
Separate a rehashed tamper control from an outer-hash mismatch in reporting.

Run after implementation from source-git:

```powershell
& 'C:\Python314\python.exe' -B '..\build-validation\Core-Memory-Acceptance-20261018.py'
```

No product feature is implemented in N1, so production TDD red/green is not
claimed. The harness must demonstrate N1-H against deliberately bad observations
and distinguish any harness repair from a skill repair. Retry at most three
evidence-changing attempts on the same failure; retain every attempt and stop
at an unapproved surface, source drift, unexpected effect or scope contradiction.

### Checklist and gate after N1

- [x] Save this approved design, source baseline and explicit test boundaries.
- [x] Implement the retained harness; run N1-A through N1-H with actual CLI.
- [x] Observe focused regressions and unchanged production source bytes.
- [x] Fresh read-only adversarial review; parent reproduces key checks.
- [x] Record exact receipts, limits, unresolved findings and next resume point.

N1 can close only bounded current-source retention and recall acceptance.
Do not set native, embedding-quality, release-ready or installed flags true.
Model-quality evaluation, broad full-CI closure, matching release packaging,
publication and installed smoke/rollback remain separate milestones/approvals.

Observed N1 execution: all eight checks passed through 12 actual public CLI
invocations (eight exit 0 controls and four required exit 2 refusals). Four
actual source copies plus labelled synthetic Unicode produced 60,704 bytes,
965 primary units and four chunks. Original saved run has 24 byte-identical
files after resume/verification. Fresh valid clone passed before negatives.
The four negative arms produced the intended named stale/artifact/inner-
approval refusals, not generic transport errors. N1-H rejected three fake
passing/wrong-cause observations. No existing product source changed.

Private receipt core-memory-acceptance-14b735d8008744579f61b9c2616dd9d6/Receipt.json,
SHA-256 81cf6203ec30f1a9a28851496a4340dadf82b602035598ef2954bbe5b7ee30a8.
Verify-Core-Memory-Acceptance-20261018.py independently checks its raw logs,
source identities, controls/refusal causes, original run and all 526 baseline
files (523 outside the three intended doc edits unchanged). Report at
docs/fable/evidence/core-memory-acceptance-20261018/report.md. Review is pending;
do not infer independent acceptance from this execution paragraph alone.

Ruling: the Fable plan is the single ledger; do not create Superpowers' second
plan/workspace or run its cleanup/automatic-commit steps. The user's explicit
no-deletion and separate commit/install gates control. This costs retaining
more local evidence, not removal of any hybrid feature. Production TDD is not
claimed for a test-only harness; its critical oracles were falsified with bad
observations. N1-D is source-change invalidation, not dependency-graph repair.

N1 final closure: initial fresh independent review returned FIX-FIRST because
the rehashed approval arm did not replace the required rehashed response-content
arm. Parent accepted that important coverage finding. A retained check against
the first receipt failed MISSING_REHASHED_RESPONSE_CONTENT_CONTROL; the harness
then gained one new copied, hash-rebound CAS response/ledger/map variant and
the check passed. This is a test-only fix, not a skill behavior repair. The
original harness, verifier, every run and all red/green evidence are retained.

Final N1 receipt core-memory-acceptance-84d3b1f1dbd14de49676e64ea381053b/Receipt.json,
SHA-256 5102e7159d7a0b968e3fe9f6739ebb95b28dee5eb06154581318355a07ac557f:
eight groups pass through 13 public invocations, with eight successful controls
and five intended refusals. The added variant passes all outer mapped hashes
and CAS identity, then is refused with E_RESULT_CONTENT and no recall. Final
readback and original/clean-clone controls pass. All 527 baseline files remain;
523 outside four Fable edit targets unchanged. Product trees still match HEAD.
Post-fix regressions: MI 279 pass plus one known xfail, CM18 and CLI9 pass.

Final parent acceptance is VERIFIED WITH CAVEATS; the initial independent
FIX-FIRST verdict is not rewritten into an independent review of corrected
bytes. Per the inline execution contract, the review-driven fix is closed by
observed red/green control, complete N1 rerun, raw-artifact re-verification and
focused regressions. Current resume/state supersede their minor stale-action
wording. Whole-project CI remains non-green/unverified as previously recorded.

N1 is complete within its TEST_ONLY structural retention/recall contract. It
does not activate model/native/release/installed readiness. Next milestone is
a separately defined task-relative retrieval-quality evaluation or scoped core
release qualification; do not install models, regenerate historical manifests,
commit/push N1 work or replace installed copies without the appropriate gate.

## 2026-10-18 - N2 offline retrieval baseline and readiness plan

AUTH: user requested "COMMIT IT AND THAN" followed by the next planned step.
N1's four repository records were verified and committed locally as
0905d0e6ca12bfac16ee28794e63e25dd2a846f6. Nothing was pushed. The user then
explicitly selected "Approve N2 offline baseline and readiness checks
(Recommended)" for the bounded card: source obligations, actual no-worker
knowledge-project/retrieve, current source/access/budget refusal, no model/
native operation, install/download, deletion, production change or release.

Goal: establish what information the current configured retrieval paths can
actually deliver for four bounded coding tasks, without confusing mandatory
source delivery with ranked retrieval or claiming an embedding-quality pass.
Architecture: one private retained harness in the existing build-validation
directory; actual unchanged public knowledge CLI and source-aware substring
locator; exact frozen independent source obligations; per-command raw logs,
pack/source hashes and fresh-process negative controls. No second governor.
Spec: knowledge-project-2.md, knowledge-contract.md, actual workflow.py,
indexing.py, impact.py, retrieval_v2.py and integrity_v2/recall.py.

### Evidence-led decision

Observed preflight: no KNOWLEDGE_WORKER_PYTHON selection; C:\Python314\python.exe
is 3.14.3 and importlib find_spec reports numpy/sklearn/semantica absent. This
is the selected interpreter, not proof that no other installed runtime exists.
Without --worker-python the public status explicitly reports DEGRADED,
runtime UNAVAILABLE and graph-required readiness BLOCKED. A text retrieval
request has empty ranked results and no embedding metadata; only independently
declared required units reopen. AST feature vectors are signed hashed lexical
features, not learned semantic embeddings. Do not rename them as model proof.

| Option | Mechanism and main failure | Decision |
| --- | --- | --- |
| Keep N1 only | Exact retention tests; does not measure query discovery or optional runtime readiness | Retain, insufficient next evidence |
| No-worker baseline | Run actual configured path and literal locator against predeclared coding-task obligations; can reveal that ranking is unavailable | Recommended, approved N2 |
| Selected Semantica/learned runtime | Observe lexical/LSA/graph or learned vectors with pinned runtime/model files; dependency cost and quality still uncertain | Separate runtime/model selection and approval, no automatic install |

Constraint lens: measurement can observe current no-worker behavior now;
unavailable ranked engines cannot receive invented scores or synthetic passes.
Cost lens: avoid copying an old experiment or installing substantial runtime
dependencies before knowing what is missing. Do not optimize queries after
seeing outcomes. Pre-mortem: mandatory units make a search look successful by
construction; therefore report separate mandatory-unit delivery, literal
discovery and ranked-engine status with blocked scores null, not zero.
Evidence families: implementation and authored tests share one origin;
fresh CLI/artifact observations challenge actual integration; manual task
source obligations are a separate authored oracle but not a calibrated dataset.
Fresh review challenges both source mappings and claims. No numeric confidence.
Confidence: Medium for the measured scope until its negative controls/review;
learned quality remains unverified regardless of all structural checks passing.
Weak link: whether four hand-authored file obligations capture every real
coding dependency. Cheapest falsifier: a natural-language query with no
mandatory units must not acquire invented ranked results or a quality flag.
Pivot: if the configured route is degraded, finish the bounded report and
request explicit runtime selection; never silently install, fake a worker or
claim that predeclaring all required units demonstrates discovery quality.

### Frozen tasks, metrics and test boundaries

Copy four actual files to a new private project root, preserving bytes and
relative paths: workflow facade, integrity_v2/recall.py, integrity_v2/report.py,
and companion complete_read_v2/partition.py. Add a clearly labelled synthetic
Python canary that raises if imported; indexing must parse it without executing
it. This is a bounded declared corpus, not a representative production dataset.
The current working repository and every old run remain untouched.

Freeze these task declarations, literal probes and query strings in Oracle.json
before executing retrieval; retain its original SHA-256 after the run. Each
task requires every unit in its independently named files, not units selected
from retrieval output. Expected primary units derive from original UTF-8 line
bytes under the documented 4096-byte bound; if an actual line exceeds that
bound, use the companion's declared child-span protocol and retain that fact.

| Task | Query | Literal probe | Independently required source IDs |
| --- | --- | --- | --- |
| freshness | Which code rejects source edits before recalled results are returned? | E_RUNMAP_STALE | recall, report |
| unicode | Which code splits oversized UTF-8 lines without losing source bytes? | E_UNIT_UNSCHEDULABLE | partition |
| approval | Which code binds accepted results to the exact request and approval? | E_REQUEST_APPROVAL | report, workflow |
| resume | Which code refuses reuse when task or saved review basis changes? | E_RESUME_BASIS | workflow, recall |

Report literal matching unit IDs, observed required-file hit counts/denominator,
truncated flag and returned bytes; do not call that semantic recall. Report
the no-worker pack's required-unit counts and exact excerpts separately from
its empty ranked result list. All ranked/model comparison scores remain null
with BLOCKED_NO_SELECTED_RUNTIME; coverage/semantic truth remain UNVERIFIED.

Declared surfaces: create private Retrieval-Baseline-Acceptance-20261018.py
and UUID run directories under existing build-validation; append this plan/
resume, update state, add evidence/retrieval-baseline-20261018/report.md.
No package source/tests, SKILL, capabilities, historical manifests/ZIPs or
installed copies change. New implementation is a test-only harness, not a
production feature; prove its critical assertions reject bad observations.

Child startup uses the existing retained runpy pattern, not mocked command
responses. Only knowledge-status/project/impact/retrieve and exact companion
capabilities/read-only Git identity commands may run. No worker/model flags,
test execution of project source, native binary, network, shell or external AI.
Indexing normally unlinks writer.lock. To honor no-deletion, archive only the
current child PID's newly created writer.lock inside this run's exact index
directory to a unique retained filename. Refuse foreign locks and every other
existing-file deletion. This is a cleanup-retention adapter, not proof of
unchanged runtime cleanup, concurrency, OS sandboxing or crash durability.
No stale-lock removal/recovery test or shared/index migration is authorized.

### Execution, review focus and observable done

INTENT: current no-worker retrieval is degraded; this milestone measures and
reports it truthfully rather than enabling or improving an engine. Preserve
the core skill and all hybrid work. Record HEAD/status and all source hashes
before starting; recheck edit targets before writing, and reverify afterward.

| ID | Required observation / failure the test catches |
| --- | --- |
| N2-A | Public knowledge-status says DEGRADED/UNAVAILABLE/BLOCKED, never treating exit 0 as a ready worker |
| N2-B | Actual knowledge-project creates source-bound project-2 generation for all declared files, including parsed unexecuted canary; exact original hashes/ranges remain |
| N2-C | Four frozen task packs reopen exactly their complete mandatory units; raw bytes match originals; actual substring locator measurements remain separate; no-worker ranked results empty, metadata absent, semantic/coverage unverified |
| N2-D | Graph-required task without a worker refuses E_GRAPH_RUNTIME_UNAVAILABLE and creates no evidence pack |
| N2-E | Removing a required source from current access refuses E_REQUIRED_ACCESS_REVOKED, no pack |
| N2-F | Tiny authorized byte budget refuses E_PACK_BUDGET instead of truncating mandatory units, no pack |
| N2-G | A newly copied project changes one mandatory source; old generation refuses E_REQUIRED_STALE, no pack; unchanged original survives |
| N2-H | A changed optional source has explicit stale/impact reporting; unrelated mandatory units still reopen without admitting stale facts |
| N2-I | Natural-language query with no independently required units yields no invented search results; record this as unavailable discovery, not quality success |
| N2-J | Critical assertions reject missing/reordered source units, false readiness or forged embedding metadata on a degraded result; every original project/index/oracle file is retained and unchanged except the recorded normal new index publication |

For every refusal require nonzero process exit, ok=false, exact named blocker
and absence of a created pack; transport/permission/syntax errors do not pass.
Code pattern for mandatory oracle (expected is derived from frozen raw files):

```python
assert [(u['source_id'], u['unit_id']) for u in pack['units']] == required_pairs
for source_id in required_source_ids:
    assert b''.join(u['text'].encode('utf-8') for u in pack['units']
                    if u['source_id'] == source_id) == frozen_bytes[source_id]
assert pack['retrieval']['results'] == []
assert pack['retrieval']['embedding_metadata'] is None
assert pack['coverage'] == pack['semantic_audit'] == 'UNVERIFIED'
```

Startup retention affects filesystem cleanup, so compare no new source drift
against HEAD, rerun the relevant existing retrieval/type/contract tests using
retained fixtures, and retain any blocked/full-suite results explicitly.
Request one fresh read-only Fable Sol review. Parent reproduces key findings;
fix only approved test-harness gaps, not product behavior on a surprise.
Stop/replan on any product defect, unapproved operation, lost evidence or
three evidence-changing failures on the same issue. Keep every failed receipt.

- [x] Freeze plan, task oracle, source inventory and bounded runtime status.
- [x] Execute actual public path N2-A through N2-J and retain complete artifacts.
- [x] Verify original files/index, frozen oracle and unchanged product source.
- [x] Run focused regressions; review and record any limits/findings honestly.
- [x] Advance resume/state to the exact next unmet gate, not another N2 rebuild.

Run from source-git after implementation:

```powershell
& 'C:\Python314\python.exe' -B '..\build-validation\Retrieval-Baseline-Acceptance-20261018.py'
```

Completion is COMPLETE_OFFLINE_BASELINE_RANKED_QUALITY_BLOCKED, not a semantic
quality, embedding, coding-benefit, native, release or installed-readiness pass.
Next gate: explicitly select/verify an existing supported pinned worker, or
separately approve an isolated runtime install before actual ranked comparison.
No new commit/push is implied by approving this N2 test milestone.

Observed N2 execution: ten groups passed through13 actual public calls (nine
success observations, four specific expected refusals). Mandatory-unit delivery
is527/527,266/266,689/689,528/528 across four frozen task contracts. Literal
required-file hits2/2,1/1,1/2,1/2; natural-language literal hits zero. Ranked
comparison is BLOCKED_NO_SELECTED_RUNTIME with null scores, never a model pass.
Primary private receipt retrieval-baseline-acceptance-
50c35faff94f435eb22811536274e079/Receipt.json, SHA-256
a5bbe45fc7b26f76b9baf9dcd6215a5f6bc3de40eba867bb08c23384f0dd24f2.
Frozen oracle237cc6cc7a36811dfd5fb5724b10db649c6a3feadbde3c43e92a136ef0e41caa.
All527 repository before/after identities match; original project/index and
oracle remained unchanged. Selected existing host contracts22/22 pass, with
three relevant subprocess/runtime exclusions and no full-CI claim. Fresh
read-only review now gates acceptance; see the N2 report, not older next-task
instructions to implement the already executed harness.

N2 review correction: independent FIX-FIRST found absent retained locator IDs/
byte evidence and no recorded reordered-unit falsifier. Parent preserved the
initial helper/verifier/run, observed the coverage checker fail on that receipt,
then repaired only the private harness. New full run873e696aa2754c7aa0d142c08c03a14a
passes ten groups/13publiccalls; eight original locator payloads and reopened
unit lengths/hashes are retained. N2-J now exercises reordered-unit rejection.
Coverage checker, independent artifact verifier and fresh selected22contracts
pass. Primary receipt0667b4c80874ae52d2d6ee5dcabf4796894905dd8649d94671e685ddf29bf93b.
See report for red/green proofs and exact IDs/bytes. Repeat read-only acceptance
review is pending; no product fix or expanded qualification is claimed.

User's normal-PowerShell metadata check was received/hash-verified:
3b3d0cb032777eeb313efc39367f78c39b930c429f67d9b18250c71784501a1b.
Python3.12.10 has NumPy1.26.4, no sklearn/semantica import specs. No worker is
selected. Future supported runtime setup requires a bounded plan and separate
install approval; N2 does not install/activate any optional runtime/model.

N2 final acceptance: repeat read-only Fable review returned SHIP for N2 only;
both Important retained-evidence gaps are closed. Parent's observed complete
rerun and independent verifier support VERIFIED_WITH_CAVEATS, with ranked
quality still BLOCKED/null. See final report section for reviewed identities
and exclusions. Resume/state now point to supported isolated worker setup
planning/approval, not another N2 run. No product/native/model/release readiness
promotion, new commit, push or installation is included.

N2 checkpoint publication authorization - 2026-10-18: user subsequently said
"COMMIT AND WHAT NEXT STEP?". This authorizes the containing local commit of
the four N2 Fable records, not a push, runtime install, package or installed
replacement. Fresh artifact verifier, retained-evidence coverage checker and
selected22hostcontracts pass before commit. All private helpers/raw receipts
remain outside Git. The next unmet gate remains supported isolated worker
setup/evaluation planning and separate installation/activation approval.

## N3 isolated retrieval runtime and measured search - proposed 2026-10-18

Status: PLAN_VERIFIED_INSTALLATION_APPROVAL_PENDING; installation/activation approval is not yet
recorded. User requested completing the next step after a deep plan. This is
a bounded setup/evaluation of the existing worker, not a new memory authority,
native fence, embedding model or rewrite. Fable remains the single governor;
Deep Plan supplies decision synthesis and Superpowers supplies execution and
verification discipline. This section is the implementation plan; do not create
a parallel plan store or infer approval to commit it.

**Goal:** observe the existing pinned local worker perform lexical/LSA retrieval
through the actual public skill path, measure discovery independently from
mandatory source delivery, and preserve the current skill and all old evidence.

**Architecture:** a new UUID-owned Python3.12 virtual environment and retained
test run under sibling build-validation. Pass its absolute Scripts/python.exe
only to the test's --worker-python. Reuse the unchanged CLI, WorkerClient,
source maps, current policy, task obligations and verify_pack implementation.
No persistent worker environment variable or installed-skill promotion occurs.

**Spec:** existing N1/N2 done criteria, knowledge-project-2.md,
knowledge-operations.md, knowledge-contract.md, worker.py/worker_client.py,
offline_engine.py and retrieval_v2.py; exact measured source obligations remain
the four cases frozen in N2 Oracle.json. Installation and test authority must
be explicit and recorded before the first install/activation command.

### Opened evidence, assumptions and decision

- Basis0584a89f11bfeec4c9ae8caa81f4492cf10c2abb, initially clean worktree.
- The user-run metadata receipt3b3d0cb032777eeb313efc39367f78c39b930c429f67d9b18250c71784501a1b
  records Python3.12.10, NumPy1.26.4, no sklearn/semantica. It is not a working
  runtime or an exhaustive survey. Do not rerun that completed host command.
- worker.py runtime_identity rejects Python outside3.10-3.13 and requires
  Semantica0.7.0 with VCS revision320761de5d040a54a3220acc563223b4a7ffdc51.
  Its handshake checks identity and pyshacl import-spec availability; it does
  not establish successful numerical imports or a successful retrieval.
- The pinned upstream pyproject was opened read-only and agrees on the version,
  Python range and NumPy>=2.0.2 requirement. Existing NumPy1.26.4 is insufficient
  for that source. Do not upgrade the user's existing environment.
  Source: https://github.com/semantica-agi/semantica/blob/320761de5d040a54a3220acc563223b4a7ffdc51/pyproject.toml
- requirements-lock.txt is explicitly an observed dependency snapshot, not a
  hash-verified supply-chain lock. Preserve it; record the actual installer
  resolution, archive URLs/digests and pip check outcome. No silent unpinning,
  latest-version fallback, --ignore-requires-python or dependency omission.
- WorkerClient strips provider credentials from its child environment and
  enables offline model settings. The worker's Python socket blocking is not
  an OS sandbox. This plan invokes neither ModelClient nor provider APIs.
- N2's retained automatic projection has54nodes/171edges including its labelled
  canary. N3 uses only the four actual permitted files for its fair comparison;
  measure the new projection and visible candidate counts rather than infer
  them from N2. Preserve vector/message/pack limits; do not widen them to pass.
  A failed PowerShell JSON view was corrected with ConvertFrom-Json -AsHashtable;
  its earlier zero counts were a parsing failure, not a source observation.

| Option | Mechanism / primary failure | Decision |
| --- | --- | --- |
| Keep no-worker mode | Reopen authored mandatory sources; ranking remains unavailable | Preserve as rollback, insufficient for actual retrieval evaluation |
| New isolated pinned core worker | Run existing lexical TF-IDF and corpus LSA with separate dependencies; Windows launch/wheel/ABI failure is possible | Recommended smallest complete step |
| Learned weights plus advanced graph/model route | Adds model files, runtimes and evaluation surface; may increase cost without measured coding benefit | Future separate approval, not N3 |

Constraints lens: ordinary source/package/installed files must not change;
identity handshake alone cannot prove imports/ranking. Numerical/SHACL and
actual public retrieval controls are mandatory. Cost lens: reuse the existing
worker and corpus, avoid new providers/weights and broad native detours. Costs
are local disk/download/time; there is no calibrated duration/size estimate.
Pre-mortem: a green handshake is mistaken for a useful search engine, or all
required units are preinserted and misreported as discovered. Separate the
positive worker control, ranking-only arms, mandatory arms and quality metrics.
Evidence families: local implementation and its authored tests are one family;
upstream pinned dependency specification is another; user-host package metadata
and N2 raw public-path observations are environment measurements, not model
quality evidence. Historical CI/reports do not prove this Windows installation.
Confidence in the route: Medium; supported by those sources but launch, binary
dependency compatibility and corpus retrieval behavior remain unobserved here.
Weak link: supported version declarations do not prove this host can launch
the new environment and import the complete pinned stack. Cheapest falsifier:
new-environment isolation/version/import/handshake plus a three-node numerical
and SHACL positive control before any task-quality result. Pivot on failure:
retain everything, diagnose the exact cause, keep N2 as last verified baseline;
do not bypass Windows security, replace the pin or invent worker success.

### Authority, preservation and exact surfaces

Allowed only after named N3 approval: create one new UUID-owned runtime/run,
fetch Semantica at the exact VCS revision and its pinned core dependencies plus
pyshacl, and run the bounded local retrieval checks below. Use Python3.12.10
from the already observed host selection; do not install a different Python or
system toolchain. If the agent cannot launch it, retain a precise failed receipt
and prepare one host script with identical scope; no elevation/ACL/gate bypass.
N3 authority covers exactly one new virtual environment, at most one
non-installing resolution command and one install command. A failed creation,
resolution or install stops setup; no second environment, repeated install or
dependency fallback is authorized. Reusing an already-created empty run for a
host handoff requires proving no resolution/install command was started;
otherwise obtain revised approval rather than silently starting again.

The approval must explicitly settle installer-owned temporary cleanup:
package installers may delete their own newly created transient files even
with --no-clean (which retains build directories, not every temporary object).
No existing source, user data, old run, receipt, runtime, shared cache or skill
may be deleted/overwritten. Do not claim literal zero-file deletion during a
normal package installation. Without this narrow exception installation remains
blocked. Test evidence uses retention adapters instead of cleanup.
Official mechanics: https://pip.pypa.io/en/stable/cli/pip_install/
and https://docs.python.org/3.12/library/venv.html .

Create only after approval under
C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\build-validation:

- N3-Retrieval-Runtime-20261018.py: one coordinator for UUID isolation,
  source-bound observations, actual public commands, preserved raw logs,
  source/oracle checking and final receipt. Reuse N1 retention helpers and
  N2 patterns; do not copy a production implementation or change old helpers.
- Test-N3-Retrieval-Harness-20261018.py: host-only harness regressions using
  synthetic observations, never promoted as actual runtime/ranking evidence.
- Run-N3-Retrieval-20261018.ps1: optional host entrypoint, only if observed
  Windows access prevents the same approved command from the agent.
- n3-retrieval-<UUID>/: runtime, installer temp/cache, source copies, index,
  frozen oracle/policies/tasks, worker stream files, raw commands and receipts.
  Allocate the environment once. Distinct test cases/replays use new exclusive
  subdirectories/files inside that same run; they are not more environments
  or installation attempts. Never replace an earlier result.

Update only existing Fable plan/resume/state and new
docs/fable/evidence/retrieval-runtime-20261018/report.md after execution.
No product Python/tests, SKILL, capability, dependency snapshot, manifest/ZIP,
installed copy, Git index/config, native DB or external service write changes.
No commit/push is included. No learned model, provider extra, answer generation,
network service or broad benchmark is included. Do not execute tests from the
copied four-source target corpus, import that target code, or call knowledge-test.
Only the enumerated repository host contracts and actual-worker cases below
may execute; these are skill validation tests, not arbitrary target-project code.

### N3-A - isolated setup and real worker positive control

- [ ] Freeze HEAD/source/doc hashes and retained original N2 oracle/receipts.
  Compare current edit targets again before writing. Record the exact user
  N3 approval, its limits and installer-cleanup choice in the new run receipt.
- [ ] Write host-only checks first: unrelated path rejection, missing/mismatched
  VCS identity, handshake-only success, empty/skipped runtime tests and a fake
  worker result must not become qualified runtime evidence. Observe those
  checks fail against deliberately bad observations, then pass the validator.
- [ ] Allocate a fresh absolute directory, set process-local installer TEMP/TMP/
  cache there, and create the venv with no system-site-packages. Never use
  --clear/--upgrade on an existing environment or --user/global pip install.
  Verify sys.prefix != sys.base_prefix and include-system-site-packages=false.
- [ ] Non-installing resolution preflight first, then install from the existing exact
  requirements-lock.txt only after its report fits the approved core-only
  scope. Retain stdout/stderr/argv/status and available archive hashes. Use
  explicit PyPI/public GitHub origins, no extra indexes/provider credentials,
  no disabled TLS or Requires-Python checks. Stop rather than install a new
  compiler, interpreter, provider/model extras or silently change dependency
  versions if the snapshot cannot resolve. Build tools strictly needed by the
  pinned source may be confined to the same new installer build environment.
  Bind the requirements by absolute path and the recorded SHA-256 before both
  commands. --isolated ignores ordinary pip environment settings; use explicit
  --cache-dir in both commands, never rely on PIP_CACHE_DIR for isolation.
  Check and disable inherited package-index/configuration overrides without
  printing credentials; no shared pip cache or existing package tree is used.
  The installer child environment sets PIP_CONFIG_FILE=os.devnull and strips
  other inherited PIP_* overrides; explicit CLI --cache-dir/--index-url remain.
  This suppresses configuration loading without editing any user/system file.
  Source: https://pip.pypa.io/en/stable/topics/configuration/#pip-config-file .
  Record effective origins and stop on an unapproved extra index or TLS bypass.
- [ ] Record pip check, actual package versions, Semantica direct_url.json
  commit, executable hash and numerical imports under the worker's sanitized
  no-user-site environment. Check NumPy, scipy, sklearn, Semantica, rdflib and
  pyshacl imports explicitly; metadata-only success is insufficient.
- [ ] Invoke the unchanged public knowledge-status with --worker-python set
  only on this command. Then invoke the actual worker on a three-node fixture
  through WorkerClient: finite vectors, lexical correct top result, source
  lineage and genuine SHACL conformity. Record original result/ranges/hashes;
  failure must stop before presenting a task-quality pass.

Representative approved-only commands, substituting only the newly allocated
absolute venv path and new exclusive receipt paths:

```powershell
$n3Requirements = 'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\semantica-runtime\requirements-lock.txt'
if ((Get-FileHash -LiteralPath $n3Requirements -Algorithm SHA256).Hash.ToLowerInvariant() -ne '892900d3bb4e27e6b645dba453fbb9440f6ea46889181e3eae7bfd0bb0b453cf') { throw 'N3 requirements drift' }
$n3PipCache = Join-Path $n3Run 'pip-cache'
& 'C:\windows\py.exe' -3.12 -B -m venv $n3NewVenv
& $n3Python -B -m pip --isolated --disable-pip-version-check --cache-dir $n3PipCache install --no-input --index-url https://pypi.org/simple --dry-run --report $n3Resolution -r $n3Requirements
# The coordinator must recheck the requirements hash and accept the retained resolution before this install.
& $n3Python -B -m pip --isolated --disable-pip-version-check --cache-dir $n3PipCache install --no-input --index-url https://pypi.org/simple --report $n3Install -r $n3Requirements
& $n3Python -B -m pip check
& 'C:\Python314\python.exe' -B 'memory-integrity\scripts\memory_integrity_workflow.py' knowledge-status --claude-mon-root $n3Companion --worker-python $n3Python --worker-timeout 60
```

The coordinator must validate these paths before invoking them; they are not
instructions to paste unresolved variables or to run setup before approval.
An installer dry-run can still fetch/build metadata; it is not a no-download
or no-code-execution check. All setup is inside the installation consent.

### N3-B - frozen public-path retrieval, not mandatory-delivery theater

- [ ] Copy exactly the four original N2 actual source files byte-for-byte;
  assert their hashes against the retained Oracle.json. Preserve the original
  N2 canary/run, but exclude the canary from N3's comparison corpus. Freeze
  N3 Oracle.json with the unchanged four query strings, literal probes and
  independently required source IDs before any retrieval/metric computation.
- [ ] Freeze bounds for both ranking modes: max_hops0, seeds5, max_visits100,
  max_results5, outgoing direction, task max_bytes2,000,000, worker timeout60s.
  The corpus, access and byte ceiling are identical across the new literal,
  lexical and LSA arms; raw read bytes/returned bytes must be reported, not
  asserted equal. Record that locator returns unit IDs, ranking returns nodes
  and source closure, and the metric levels differ. Do not silently tune the
  query, corpus, budget, k or expected sources after an outcome.
- [ ] Build a new project-2 index via actual knowledge-project. Do not import or
  execute the copied project code. Archive only the child-owned writer lock;
  refuse foreign locks. Retain WorkerClient TemporaryFile streams in this
  new run using the exact test-only retention adapter below, not a fake process.
- [ ] For every case/mode run actual knowledge-retrieve twice with independent
  task files: ranking-only required_units=[] for discovery measurement; the
  original mandatory file obligations for safety delivery. Preserve exact
  ranked IDs/scores/path/edge IDs, lineage, source-unit references, fit-scope/
  configuration/sklearn identities, raw stdout/stderr and pack digests.
- [ ] Independently reopen every returned unit from frozen original bytes,
  validate range/hash/order, and calculate required-file hits/denominator,
  missing expected sources, unique discovered source/unit IDs, extraneous file
  hits relative to the authored oracle, reopened UTF-8 bytes and serialized
  pack bytes. Keep mandatory-delivery totals out of discovery numerators.
- [ ] Recompute the literal baseline on the same four-source N3 corpus; retain
  its exact observed IDs plus open_unit byte lengths/hashes. Keep historical
  N2 artifacts unchanged. Full natural-language substring matching remains a
  deliberately weak literal baseline, not an equal semantic algorithm; report
  this limitation and do not infer general superiority from its zero hits.
- [ ] Require a genuine SEMANTICA_OBSERVED result with matching0.7.0/revision,
  nonempty actual fixture results, genuine SHACL and finite bounded scores.
  Technical readiness and measured case quality are separate fields. A real
  task miss/OOV/scope refusal is reported as that case's failure/limitation,
  not a passing quality result or a reason to alter the frozen exam. No N3
  measurement establishes universal semantic understanding or learned quality.

Existing public command pattern (no --model-* or --rerank arguments):

```powershell
& 'C:\Python314\python.exe' -B 'memory-integrity\scripts\memory_integrity_workflow.py' knowledge-retrieve --claude-mon-root $n3Companion --project-root $n3Project --index-dir $n3Index --policy-file $n3Policy --task-file $n3Task --query-text $n3FrozenQuery --embedding-mode lexical --max-hops 0 --seeds 5 --max-visits 100 --max-results 5 --worker-python $n3Python --worker-timeout 60 --evidence-pack $n3NewPack
```

For the LSA arm only embedding-mode changes to lsa. Each call has its own new
output paths. Never overwrite a pack or retry to replace an unfavorable score.

#### Exact host-only worker stream retention adapter

The CLI and fresh verification process install this adapter before runpy/API
dispatch. Replace only worker_client's tempfile namespace in that host process,
not the global tempfile module and not the worker response/process function.
The actual worker still runs unchanged through WorkerClient/_process; Popen
receives real binary file descriptors with identical read/write/seek semantics.
No source file or response bytes are patched. Roles are harness labels, not
authenticated producer identity. Each host command has its own new stream root
and retained stream manifest; bind them to the outer command/ordinal and exact
stdout/stderr/input hashes. This is not unchanged CI or an OS sandbox claim.

```python
from contextlib import contextmanager
from hashlib import sha256
import os
from pathlib import Path
from types import SimpleNamespace
import uuid
from knowledge_bridge import worker_client

def install_retained_worker_streams(stream_root: Path, records: list) -> None:
    stream_root.mkdir(parents=False, exist_ok=False)

    @contextmanager
    def retained_file(*args, **kwargs):
        if args or kwargs:
            raise ValueError('E_N3_TEMPFILE_SIGNATURE_CHANGED')
        ordinal = len(records)
        path = stream_root / (str(ordinal) + '-' + uuid.uuid4().hex + '.bin')
        item = {'ordinal': ordinal, 'invocation': ordinal // 3,
                'role': ('stdin', 'stdout', 'stderr')[ordinal % 3],
                'path': str(path), 'closed_and_hashed': False}
        records.append(item)
        handle = path.open('x+b')
        try:
            yield handle
        finally:
            try:
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                handle.close()
            digest, count = sha256(), 0
            with path.open('rb') as retained:
                for block in iter(lambda: retained.read(65536), b''):
                    digest.update(block)
                    count += len(block)
            item.update(bytes=count, sha256=digest.hexdigest(),
                        closed_and_hashed=handle.closed)

    worker_client.tempfile = SimpleNamespace(TemporaryFile=retained_file)
```

The coordinator must exclusively save records in a finally block even if the
CLI raises SystemExit/ValueError or setup/spawn fails. Assert exactly three
closed/hashed descriptors for each observed worker invocation, except a
recorded partial stream-open failure, which cannot pass readiness. Independently
decode the stdin/stdout when JSON is expected and compare the original worker
result fields to the pack; stderr is retained as bytes, never causal authority.
Test this adapter with real tiny Python stdlib child I/O before using the pinned
worker: input/output/error bytes and exit statuses must survive context close,
and deliberate output alteration/missing roles must fail the artifact checker.
These are harness controls, not ranked-runtime proof.

For the selected existing unittest fixtures, reuse N1's retained
TemporaryDirectory context/cleanup pattern under this same run's fixture
directory: cleanup/__exit__ retain the newly created directory rather than
rmtree. Anonymous TemporaryFile handling is separate and is not supplied by
N1's directory adapter. Keep any fixture/worker-subprocess cleanup differences
explicit; never claim all third-party filesystem behavior is OS-contained.

### N3-C - fresh-process verification, refusal and regression evidence

- [ ] Reopen saved packs in a fresh host process with the actual
  retrieval_v2.verify_pack(pack,doc,root,policy,task,WorkerClient(...)). It
  reruns the real selected worker. Record exact equality/no new source drift.
  This is the existing API, not an invented knowledge-verify CLI command.
- [ ] In new copies, alter a required source and separately revoke required
  access: named E_REQUIRED_STALE/E_REQUIRED_ACCESS_REVOKED, nonzero BLOCKED
  result and no created pack. A command/permission/import failure is not a
  correct safety refusal. Test optional stale exclusion while valid unrelated
  required material survives; do not overwrite original source/index state.
- [ ] Tiny authorized pack budget must refuse E_PACK_BUDGET with no truncated
  mandatory material/no output. Unknown-vocabulary query must not invent a
  vector/result. Graph-required no-worker control must still refuse even
  though this separate runtime now exists; no global auto-selection occurs.
- [ ] In a copied pack forge the embedding model identity and rehash its outer
  digest; the actual verifier must reject it for a relevant inner identity/
  replay cause. Missing/reordered source bytes and invented ready/semantic
  flags must fail the harness oracle. Retain all bad copies and exact errors.
- [ ] Run the same22selected host contracts plus the previously runtime-gated
  RetrievalV2.test_actual_text_worker_incoming_replay_is_current_and_exact.
  Run these six ActualOfflineRuntime tests against the real selected worker:
  test_automatically_generated_vectors_rank_identifiers_with_real_semantica;
  test_latent_and_hybrid_modes_are_deterministic_without_model_downloads;
  test_oov_empty_input_and_unknown_mode_do_not_invent_vectors;
  test_only_passed_authorized_corpus_changes_fitted_identity;
  test_document_with_no_tokens_cannot_be_randomly_represented;
  test_real_shacl_applies_predicate_domain_and_range.
  Retain test IDs/counts/status/logs; a skipped required actual-runtime case
  cannot count as proof. The existing hybrid numerical fixture is not a new
  public hybrid search arm or learned-model run. Hash-seed/child-import cases,
  prose cases, RealBenefit fixture execution, full discovery/CI and package
  verifiers remain explicitly unrun unless separately scoped and approved.

### N3-D - preservation, review and honest handoff

- [ ] Compare every pre-existing repository source and retained N1/N2 artifact
  identity before/after, not merely Git status. Product, companion, releases,
  runtime definition files, CI and installed copies must remain unchanged.
  Never regenerate historical packing lists or promote capability flags.
- [ ] Preserve every raw command, worker stream, receipt, failed variant and
  runtime; rollback means stop selecting the new absolute worker path and
  retain it for diagnosis, not uninstall/delete data. Stop only the operation's
  own worker processes if timeout handling requires it; never a broad kill.
- [ ] Request one fresh read-only Fable reviewer of actual source bindings,
  numerical/runtime proof, equal-scope metric denominators, negative causes,
  preservation and claims. Parent reruns key verifiers. If a product defect
  is found, stop and replan; do not repair product behavior under N3 authority.
- [ ] Update existing plan/resume/state and the N3 report with exact hashes and
  separate statuses: INSTALLATION_OBSERVED, WORKER_RETRIEVAL_OBSERVED,
  CASE_QUALITY_MEASURED or CASE_FAILED/BLOCKED, SEMANTIC_TRUTH_UNVERIFIED.
  Only mark bounded N3 complete when actual positive worker control and all
  required safety/replay/preservation checks pass. Poor task retrieval remains
  visible and blocks a recommendation to rely on it for those tasks. Learned
  embeddings, real-project coding benefit, full CI, native fence, final paired
  packages and installed readiness remain separate unqualified gates.

Global stop conditions: new authority/scope, Windows access denial, unresolved
dependency/ABI/pin/source drift, unauthorized deletion, foreign writer lock,
missing original evidence, fabricated backend, or three failed correction
attempts on the same host-only harness-validation cause. The latter ceiling
does not authorize more runtime environments, package resolution/install tries
or replacement task-quality runs; setup has the one-cycle limit above. Record
precise failures and never bypass a gate.
There is no promise of zero defects; isolation, observable controls and honest
stop conditions protect the existing skill while uncertainty is tested.

### N3 requirement-to-proof map

| Requirement | Owner / exact proof | Closure boundary |
| --- | --- | --- |
| N3-R01 authority | N3-A retained human approval includes install, test-only selection and installer-owned new transient cleanup | No setup command before approval and reviewed plan |
| N3-R02 isolation | N3-A new absolute venv, sys.prefix/base_prefix, pyvenv.cfg, original package/source identities | No user/global package change or installed-skill selection |
| N3-R03 pinned identity | N3-A actual package versions/direct_url VCS revision, executable digest and WorkerClient check | No metadata-only or caller-declared runtime qualification |
| N3-R04 real operation | N3-A finite numerical/SHACL/lineage positive control and actual public retrieval | Handshake alone cannot pass |
| N3-R05 task discovery | N3-B frozen four queries and source obligations, required_units=[] ranking-only arms, raw ranked references/scores and independent file/byte metrics | Mandatory inclusion never enters discovery numerator |
| N3-R06 fair/reportable limits | N3-B identical four-source access/corpus/caps and retained locator payloads | Node ranking vs literal units disclosed; no general superiority claim |
| N3-R07 current evidence | N3-C new-process verify_pack rerun with real WorkerClient, original source closure and exact pack identity | No cached packet treated as fresh proof |
| N3-R08 safety | N3-C named stale/access/budget/OOV/no-worker and rehashed inner-forgery negatives, no created blocked packs | Unrelated transport/import error cannot pass |
| N3-R09 nonregression | N3-C same22 contracts plus one actual replay and six actual-runtime cases; exact IDs/no critical skips | Not full CI, learned evaluation or model benefit |
| N3-R10 preservation/handoff | N3-D source and N1/N2 inventories, unchanged product/installed files, independent read-only review and parent verifier | No native/release/installed qualification or commit/push |

Execution must report each requirement separately as observed, failed, blocked
or unverified. Planned test names, source inspection and review approval are
not executed evidence. This map adds no new milestone or authority.

### N3 planning review corrections (no runtime execution)

Initial read-only review required operational clarification before setup:
one environment/one resolution-install cycle rather than ambiguous multiple
attempts; explicit pip cache/index; absolute/hash-bound requirements; a concrete
retained TemporaryFile adapter distinct from retained directory handling; and
calling dry-run non-installing, never read-only. These corrections are now in
the plan. The reviewer returned SHIP for plan acceptance only, with no remaining
blocking finding. They are planning fixes, not observed installation, retrieval
or qualification results.

Final planning checkpoint: the exact reviewed plan snapshot is retained as
private N3-Reviewed-Plan-cdf1cd7f.md, SHA-256
cdf1cd7fa28cbee40d603572929f2b2adf0d71bd7ccab6aec66ca2a35a2a5c9f.
It is an immutable evidence copy, not a second governor/plan store. This latest
status/review annotation does not change the reviewed execution scope. Parent
source, CLI/API, dependency and preservation checks agree with the bounded
review. Original preflight N3-Plan-Preflight-becaf8a26b6f4df3a79dc73dd51491b3.json
SHA-25615c1d40fa648b7111ce6f91de65c2f8c889b676da9169a5967a691d3bcedd2cf
is retained but superseded: final verification found a transcribed worker.py
hash error in that receipt, not a product-source change. The corrected measured
N3-Plan-Preflight-corrected-20261018.json SHA-256
c993e852d52a4d4933c2422c4d248279bac2e8a07de169a127b4d6ab658f8c9e
binds all five fresh source hashes,528retained baseline files and525unchanged
outside three planning docs. This parent evidence correction does not change
the reviewed runtime plan or create new runtime/review qualification.

Only the pending human N3 installation/activation/installer-owned-new-transient
cleanup decision now blocks execution. If approved, execute N3-A through N3-D
within this exact one-environment/one-setup-cycle scope without re-asking for
the same milestone. If not approved, retain this ready plan and do not install,
activate, build the new harness or repeat already closed N1/N2/host discovery.
No actual N3 worker/runtime test, dependency resolution, download or installation
has run. No new commit/push, product/package/installed change or qualification
activation occurred.

### N3 execution authorization - 2026-10-19

AUTH: user approved "N3 isolated setup/tests" and explicitly listed N3-A through
N3-D. Follow-up cleanup decision: "Allow cleanup of new installer-owned temporary
files only (Recommended)". This closes the pending install/test-only-selection
and new-installer-transient exception, not a commit/push or installed-skill gate.
Execute the reviewed scope; do not ask for the same milestone again.

INTENT: create only private N3 harness/evidence and one isolated environment;
observe real retrieval if setup works. Product source, dependencies, packages,
installed copies and all pre-existing data remain unchanged. Existing three
dirty Fable planning files are preserved. Baseline HEAD is0584a89.

Execution ledger: N3-A in progress; N3-B/C await successful setup/positive control;
N3-D preservation/review follows observation. Ruling: retain all evidence and use
this existing Fable ledger rather than Superpowers' additional workspace/plan,
automatic commits or deletion lifecycle, because the approved plan explicitly
forbids competing governance, commits and removal of existing records. Cost if
wrong: less automatic bookkeeping; explicit retained receipts replace it.

N3-A execution checkpoint: private harness controls20/20 and existing selected
contracts22/22 passed. Original N2 obligations/questions and four source files
are frozen for N3; no canary or target-code execution. One py.exe venv command
started the launcher but its pinned Python3.12 child was denied access (exit101),
no venv exists, zero resolution/install commands. Retain the same empty run
n3-retrieval-9ec6fb1db36444acba2945896e8b8d17 and original Setup-Receipt hash
0b1e5fde9b8899474c21d46796b72e6dd2184676baa20abdb1a23f74df061dfd.
The normal-host handoff must not create another run or retry any started setup.
N3-B/C actual-runtime tests and quality metrics are BLOCKED, not passed; their
full orchestration is not yet implemented. N3-D independent execution review is
pending after the first reviewer hit capacity; one same-role retry requested.
Evidence/status: docs/fable/evidence/retrieval-runtime-20261018/report.md.

Ruling: the one-shot installer stop is preserved; a normal-host continuation is
only allowed after proving the pinned Python child never started, the venv is
absent and no resolution/install started. Launcher exit101 is distinct from a
Python-run failure. Cost if wrong: unintended second setup; the exact retained
diagnostic and no-environment/no-install guards refuse ambiguous cases.
Ruling: do not execute broad discovery/model/native tests despite a generic
testing instruction, because the approved N3 test allowlist excludes them.
Cost if wrong: unknown broader regressions; report this exact coverage limit.

Final parent checkpoint:21/21 controls after an additional exactPython3.12.10
pin falsifier passed RED-to-GREEN. Identity is checked before resolution and
again with numerical imports; no changed setup path was executed. Both fresh
read-only reviewer attempts failed from selected-model capacity; no review
verdict exists and no model was silently substituted. Retain Independent-Review
in the same run. Host N3-A entrypoint is parent-checked/hash-bound only. B/C
orchestration/actual-runtime observations and D independent review remain open.

### N3-A host resolution failure and bounded amendment — 2026-10-19

Host receipt f556ab5071892b5ae1d4daf0765fd5b74433aa76496b0998da871808f471571e
and all six logs are verified. The existing isolatedPython3.12.10 environment
was created and identity passed. The single permitted resolver started, then
Git clone refused the224-character .git path with '$GIT_DIR' too big. No install
command started; no numerical imports or worker retrieval ran. The previous
agent-access blocker is no longer the normal-host blocker.

Root cause reproduced read-only: installedGit2.53.0.windows.1 passes its length
gate at220characters (then refuses a nonexistent repo) but rejects221and224;
process-local core.longpaths=true still rejects224. Exact upstream setup.c
atv2.53.0.windows.1 lines1021-1022 checks PATH_MAX minus40. The coordinator's
deep installer TEMP layout was defective; no credential/pin/user error is shown.
Evidence: same run Host-Resolution-Diagnosis.json and latest N3 report.

N3-A2 PROPOSED, NOT APPROVED: keep the same venv, all helpers and receipts;
add one short exclusively owned installer workspace under
C:\Users\sakth\Documents\Codex\n3-install-<new8hex>, one recovery helper and
offline path/ownership/no-repeat regressions. No system config, ACL, archive
substitution, dependency pin or installed-copy change. Exactly one additional
resolver is proposed, and at most the original still-unused install after
validated resolution, followed by original N3-A positive checks. Preserve all
raw outputs under new exclusive names. Installer-only NEW transient cleanup
must explicitly cover the new owned workspace; old data are never removed.

Options: no-build hold; minimal one-letter temp inside existing run (Git dir211,
only9chars headroom); recommended short owned workspace (substantial headroom,
same venv/pins and provenance). Source guard and real boundary probes agree on
the failure; no runtime evidence proves the fix or dependency availability.
Weak link: remaining dependencies/ABI and installed-path behavior. Cheapest
falsifier: offline UTF-8 path-budget guard before the single new resolver;
stop on any mismatch/failure, no second retry or unpinning. Rollback: stop
selecting the new workspace and retain every file and prior checkpoint.

Approval for this retry/layout amendment is required because the original
one-resolution limit is now consumed. This is not a new approval for all N3
or a waiver of N3-B/C/D, review, release or installation gates. Do not rerun the
old one-shot host script, create another venv, or implement/run recovery yet.

### N3-A2 approved execution — 2026-10-19

AUTH: user replied "Approve bounded N3-A2 recovery (Recommended)" to the exact
short-workspace/one-additional-resolver amendment. Keep the existing venv and
all prior helpers/receipts. Scope includes successor private helper, retained
offline path/ownership/no-repeat checks, one short owned installer workspace,
one additional resolver and at most the original still-unused install after
validation. New installer-owned transient cleanup only; all old data retained.

INTENT: prevent the observed Git224>220path failure by rejecting predicted
UTF-8 Git paths above160bytes before invoking pip and using the approved short
installer workspace C:\Users\sakth\Documents\Codex\n3-install-ef149e14\tmp.
The workspace is created exclusively once and bound to this run/receipt; it is
not another Python environment. Old helper062b298d and hostreceiptf556ab50 stay
unchanged. If agent cannot start the existing venv, retain a precise result and
hand off the same reserved recovery before its resolver starts. Do not spend a
second resolver or ask for this already-approved amendment again.

N3-A2 checkpoint: successor and16retainedcontrols built, RED-to-GREEN; original
21controls and22hostcontracts pass fresh. Predicted .git path123UTF-8bytes,
97headroom, enforced cap160. No new resolution/install has started. Agent could
reserve recovery-a2 but approved short-root creation was denied; adjusted normal
New-Item diagnostic recorded actual AccessDenied. Stop directory retries here;
normal-host continuation may create that same exact approved root once without
another approval, not another workspace/env. Existing one-shot scripts unchanged.

Parent found/fixed an initial successor early-error receipt gap with two new
controls plus a missing/aliased-temp guard; first code snapshot11cc57df and null
receipt observation are retained. First exception was not captured; subsequent
directory denial is separate observed evidence, not reconstructed causation.
Current successor eba239e5 preserves pre-creation errors and binds the controlled
host handoff to source/receipt/denial identity and no prior child/resolver/install.

Native Fable reviewer again failed at selected-model capacity; one attempt this
amendment, no substitute, no independent pass. Parent-only handoff guards pass.
Normal-host command and exact traces are in latest N3 report. Review, actual
runtime and full N3 completion remain UNVERIFIED. TWINS: old installer-temp
construction remains only in the preserved original helper; successor overrides
TEMP/TMP for approved installer commands. No production source was changed.

### N3-A2 host result and bounded offline diagnosis — 2026-10-19

Receipt e857e7299fbd8279d2abf832bc57d79a34aa58e200ab8ccc85b8d8140b1340b5
confirms identity and the one additional resolver exited0. No installation
started. Reading pip's saved UTF-8 report with the controller's defaultcp1252
failed at byte29148. Pinned local pip install.py writes this report explicitly
as UTF-8. This is our private helper defect, not a user command/API-key error.

Read-only UTF-8 revalidation also exposed a second independent blocker: all50
approved package versions match, but Windows resolves53packages. Extra packages
are colorama0.4.6 (loguru/tqdm Windows markers), tzdata2026.5 (pandas Windows
marker), win32-setctime1.2.0 (loguru Windows marker). The unchanged strict
validator rejects the additions. Do not bypass it or silently change the lock.

INTENT: inside approved N3 diagnostic scope, add a private read-only UTF-8 report
auditor and RED-to-GREEN controls, bind existing receipt/report/helper hashes,
verify logs and preserve all old artifacts. No resolver, install, venv creation,
new workspace, pin change or production edit is authorized by this correction.
Update this same plan/evidence/state; propose a Windows-specific pin amendment
only after the actual saved report and parent dependency markers are verified.

Options: stop with retained evidence; recommended separately approved private
Windows overlay preserving all50pins plus the3observed exact dependencies and
reusing the saved resolution; rejected ignoring dependencies/using no-deps or
relaxing validation. No third resolver is currently approved or required to
inspect the saved report. The unused original install remains conditional on
validating a dependency scope approved by the user. No whole-N3 success claim.

N3-A2 diagnostic outcome:7/7newofflinecontrols passed after RED7/0; saved report
read and unchanged validator refuses the3extras. Diagnosisebc12741 retained in
same run; all4hostlogs/Results hashes match, no install directory or installed
package beyond originalpip25.0.1 exists. Original helpers left unchanged. Twin
search found the same defaultencoding pattern for Installation.json and stream
manifests; a future successor must handle all externalJSON explicitly asUTF-8.
Broader21/22suites and CI were not rerun for this private auditor-only correction.

N3-A3 PROPOSED, NOT APPROVED: a private Windows overlay adds ONLY
colorama==0.4.6, tzdata==2026.5, win32-setctime==1.2.0. Original50pins/source
revision/lock/source files remain unchanged. Reuse saved resolution92fca79b,
same venv/shortroot, all receipts; no third dry-run resolver. Implement/test an
install-only successor with explicitUTF-8 and exclusive unused-install claim;
at most originaloneactualinstall if the exact53package scope/provenance checks
pass, then original pipcheck/imports/status/positive retrieval controls. Preserve
all olddata; only approved installer-owned NEW transient cleanup. No globalGit/
ACL/skill/package-release/model/native/commit/push action. On further mismatch,
stop, retain evidence and return to user. Exact definition/limits in latest N3
report; this proposed dependency expansion requires separate approval.

### N3-A3 approved install-only execution — 2026-10-19

AUTH: "Approve N3-A3 private Windows overlay and guarded continuation
(Recommended)". The exact approved additions are colorama0.4.6, tzdata2026.5,
win32-setctime1.2.0. All50originalpins/source revision, same venv/shortworkspace,
saved report and old evidence remain intact. No extra dry-run resolver/newenv/
olddata deletion/globalconfig/model/native/commit/push/installedskill action.

The completed native read-only review ships the preceding diagnosis/proposal
only, not installation/runtime. Its install gates are adopted: complete53-row
validation before exclusive install claim; exact saved Start.json bindings;
explicitUTF-8 at every externalJSON boundary; full preinstall venv inventory;
unambiguous consumed-resolver versus auditor/no-resolver evidence fields.

INTENT: create only private recovery-a3 overlay, installer/evidence/tests and
guarded successor. Derive a complete install input from saved approved53rows,
binding52archiveURLs/hashes and exactSemantica VCS revision; no --no-deps or
acceptance relaxation. Use no existing pip cache writes. Retain full venv bytes
inventory before selection/after attempted execution, plus repository hashes.
Identity must pass in the existing interpreter before any exclusive install
claim. One actual install only; no resend after ambiguous/failed start. A known
agent process-start denial may hand off the same untouched environment before
install claim, not authorize another install. Scope/identity drift stops work.

Execution order: test guards RED-to-GREEN; prepare/hash all private inputs and
baseline; rerun previous7/21/22offline checks; obtain fresh final-code review;
attempt existing-interpreter identity and originalunusedinstall if accessible;
pipcheck/numericalimports/workerstatus/realpositive retrieval; inspect exact
receipts and preservation. If host launch is denied, retain exact result and
provide a sealed one-time normal-PowerShell continuation under this approval.
N3-B/C evaluation and N3-D final review do not become complete automatically.

N3-A3 pre-execution checkpoint:17controls pass (RED16toGREEN16, early-preflight
masking RED1toGREEN17). Prior7/21/22checks pass fresh; actual offline53row/Start
preflight passes, generating52wheelhashrefs plus pinnedVCS. Preview fullvenv
inventory861files107directories12049845bytes. No prepared/identity/install claim
yet. Final native code review failed remotecompaction/workspacecredits, then
same-role retry failed selected-model capacity. No substitute, no pass. Retain
Independent-Code-Review.json; no further retry at this checkpoint.

Ruling: continue already-approved isolated work on parent-verified controls,
explicitly marking independent code review UNAVAILABLE rather than passed.
Prepare immutable inputs/baselines and attempt existinginterpreteridentity;
only a valid sameenv identity and complete unchanged preflight can reserve the
originalunusedinstall. This does not close N3-D/release/installedskill gates.

N3-A3 actual agent observation: preparation and full preflight passed. The venv
launcher started (pid44544), exited103 with exact stderr "No Python at" pointing
to its original WindowsApps base alias, and emptystdout. This is NOTWinError5
and the existing narrow host guard correctly refused. No install claim/command
was created. Entire861file/107directory baseline and repo inventory are unchanged.
Retain receiptee02b50e and sealedoldsuccessore719eda7/Prepared.json untouched.

Primary CPythonv3.12.10 PC/launcher.c defines RC_NO_PYTHON103 and reports this
message when GetFileAttributesW cannot see the configured base executable,
before invoke_child. Agent cannot see that alias. Normalhost accessibility is
not established anew; priorhost3.12.10 identity succeeded. No path/ACL/env repair.

INTENT: necessary bounded N3-A3 correction, not new install authority: add a
small sealed host-only adapter that recognizes ONLY this hash-bound103receipt,
exactcommand/error/emptystdout and unchanged fullenv/source/input baseline.
Keep original installer, Prepared and failed receipt unchanged. Adapt only the
handoff predicate; originalfull53preflight, identity, exclusiveunusedinstall,
hash checks and runtime checks execute unchanged. No third resolver or agent
identity retry. Ordinary errors, changed evidence/env or prior install/hostclaim
remain refused. Tests must fail before adapter and pass after; normal-host
one-time command stays within existing N3-A3 approval. Native review unavailable.

### N3-A observed working; continue approved N3-B/C — 2026-10-19

Host receipt7e3a4605c2892e1aaad5082ab52e11a2ea6b644ffb13d2790e6006b0d8e8598e
matches; all6commands exited0,12output hashes/Result records verified. All53
installation rows match saved versions/origins/archive hashes/VCS revision;
pipcheck and numericalimports passed. Both retained workerinvocations match
publicstatus/positive stdout; retry ranks first, SHACLconforms, lineageverified.
No preexistingvenvfile changed; repository unchanged duringrun. Originalinstall
allowance consumed. Never rerun setup, select anotherenvironment or use old
empty-venv guards. Semantictruth/learnedquality/fullN3 remain unverified.

INTENT: execute remaining already-approved N3-B/C/D, no new scopeapproval:
private evaluation harness/tests/evidence inside same N3run; preserve frozen4
sourcefiles, Oracle/source-map, oldartifacts, same installedruntime and product.
Reuse original retained WorkerClient descriptor adapter/publicCLI. Prepare new
index and literal measurements without worker execution; record that Python
projectconstruction has0worker calls. Host then runs frozen lexical/LSA versus
literal arms, independent required-unit delivery, fresh-process verify_pack,
named safety negatives and exact29selectedtestcases. No installer/download,
model/provider/native action, copied-target execution, productfix or Git action.

Mechanism/verification detail: separate discovery(required_units=[]) from
mandatory arms in everycase/mode; explicitfrozen bounds/queries/access, opened
bytes and outerpack identity. Literal locator uses same sources, retains both
natural-language and assistederrorphrase probes; no semantic superiority claim.
Each invocation gets an exclusive new directory, streams and no output resend.
Fresh API verifier is a new host process, not a fictional CLI. Mutate only new
source/pack copies for stale/access/budget/OOV/no-worker/forgery refusals; require
named semanticcause, no outputpack. Preserve unrelatedvalidsource delivery.

Run only approved22hostcontracts+1actual replay+6ActualOfflineRuntime methods,
retaining fixture directories and realworkerstreams. No broad discovery or
targetproject tests. Preflight binds currentinstalled posthostmanifest and
alreadyobservedreceipt/source/oracle hashes, not prior pip-only environment.
No further agentPython3.12 launch attempt: previousalias failure remains known;
prepare a one-time normal-host evaluation entrypoint if access is still absent.
Write falsifiers first; independentread-only review requested at handoff, with
no pass assumed. Productdefect stops/replans; quality misses remain visible.

Progress:14oracle+7coordinator+21originalharness+22hostcontracts pass fresh;
allredfixtures retained. Publicindex/literalbaseline and8no-workerpublicpacks/
8freshverifiers observed; index4sources52nodes170edges,0constructionworker.
Questions/caps/sourceidentities unchanged. Prepared SHAae96299c169076491dd238898e512448bdf6aaea0cd26daf6160cb146573d992
binds runnerf935c051/contracts1970c7e0 and inputs. Ranked/safety/exact29runtime
evaluation unrun; freshreview requested, no passassumed. Hostentrypoint
-ValidateOnly passed. See sameevidencereport/currentresume for receipts and
measured literalmisses. No setup/product/model/native/Git/release/installskill.

Freshread-onlyreview returnedFIX-FIRST for evaluatorbinding/exact29allowlist/
OOVsafetybasis and separatelyforgedsemanticflag. Accepted, withinN3harnessscope;
no productfix/newmechanism. Retain sealedoldsource/Prepared/output. Successor
contracts-v2(515bd5e3), evaluator-v2(259e569d), newevaluation-bc-v2-20261019 root;
sameinstalledenv/frozenexam, no resolution/install/model/native/Git.20v2oracle
controls REDbefore/GREENafter plus7v2coordinator controls green; actualoldfresh
verifier counterexamples reproduced, newexperimentvalidator refuses. Preserve
diagnosticfalse-start logs. Obtainfreshv2review, prepare newindex/inputseals and
one-timev2hosthandoff; oldhostentrypoint superseded, do notrun. Actualquality/
worker-dependent safety/exact29runtime tests and N3-D stillunrun.

Secondreview acceptedpriorfixes and foundemptyrankedclassification gap. Same
approvedscope v3successor keeps alloldsource/records: classifyemptyrankedfailed,
retain/replaybutexclude fromsafetybasis; separateliteralbaselinelabel; finite
boundedscorechecks; explicitqualityfailures.25v3oracle+7coordinator+21existing
harness+22hostcontracts=75selectedchecks green. Prepared0d7a883a sealsv3runner
0f0c37e5/contracts d0bc0e9d in evaluation-bc-v3-20261019; public4sourceindex
52nodes170edges/0worker. Do notrunoldentrypoints. Freshfinalv3review/preflight
pending; no actualranked/safety/29runtime/N3-D completion claimed.

Finalv3 nativecodereview SHIP_FOR_APPROVED_HOST_HANDOFF_ONLY, nocritical/
importantfinding. Configuredhost -ValidateOnly actuallyexited0;2v3literalpacks/
2freshverifiers pass. ExtraWindowsPowerShell5.1 -File diagnostic refusedbyagent
scriptsdisabledpolicy, retained/no policychange/retry; notnormalhostresult.
Parentfinalread-only Pythoncontroller preflight separate, noPSsecuritybypass.
Only Run-N3-Evaluation-v3-20261019.ps1 (d11a168a) with Prepared0d7a883a iscurrent.
Alreadyapproved normalhostrun remainsnext; noinstall/download/model/native/
Git/product/installedskill changes. ActualB/C/N3-D remainsunrun. Readreport.

### Host preflight preservation discrepancy — diagnose only, 2026-10-19

User ran currentv3 once. It stopped in --inspect at
E_EVAL_ORIGINAL_EVIDENCE_CHANGED before --run/hostclaim. Do not rerun evaluation.
Current agent filehash comparison: fourprojectfiles and all454priorN1/N2files
equal originalBefore; strictscans reportnoerrors/nolinks. Normalhostdiscrepancy
not reproduced here. Differentvisiblepaths/content/context or a transientchange
remain hypotheses, not causes. No baseline replacement/ignore/requalification.

Options: genericerroronly cannot isolate cause; rebuildingbaseline could hide
realchanges and is rejected; recommended smallest step is one additive
read-only diagnostic under sameN3scope, binding immutablePrepared/Before/source,
enumerating only thosefourprotectedroots, retaining exactadded/missing/modified
paths/hashfacts and access/link observations separately on agent and host.
No worker/publicevaluation/install/resolver/process/security/Git/native/model
call. Tests must distinguish additions/deletions/edits from identicalviews,
and incompleteenumeration from a validno-difference observation. Keep allfiles.
Freshread-onlyreview before hostdiagnostichandoff. Cheapestfalsifier: exacthost
diff. Pivot: any changedhistoricalbyte needs source/provenance reconciliation;
anycontext-onlyviewdifference needs reviewedinventorydesign, not a relaxedguard.
Neitherfinding authorizes another native/ranked evaluation or baseline rewrite.

Diagnostic reviewFIX-FIRST accepted: remove secondunsafe rglob, addexternal
hashbinding, distinguish diagnosticnondeletion from missingoriginalcause, make
visiblemismatch nonzero. Successorv2(7399be39) and sealedlauncher(d9c26b8d),
11controlsREDbefore/GREENafter includingrealprivatejunctionno-targetread,
4actualPowerShellgatecontrols pass. Same4protectedroots/newreceipts only; all
oldcode/data/linkfixtures retained. Newfinalreview requested before one normal
hostdiagnostic. Noevalretry/rebaseline/product/runtime/Git/securitychange.

Finaldiagnosticreview SHIP_FOR_ONE_READ_ONLY_HOST_OBSERVATION; parent11controls+
4gatechecks pass, code7399/launcherd9c26 pinsunchanged. Normalhostcause notsolved;
only nextallowedaction is externallyhashchecked launcher to recordexacthostdiff.
No N3retry/baselinerewrite for any diagnosticstatus. Read latestreport/resume.

### Approved narrow evidence read grant and local checkpoint - 2026-10-19

AUTH: user requested "COMMIT EVERYTHING" with no file/data deletion, then
explicitly selected "Grant normal-account read access to the 19 folders/38
files; keep all checks (Recommended)". This replaces the earlier no-ACL-change
boundary ONLY for these exact targets and this normal account. It authorizes
neither push nor N3 evaluation retry, code disabling, exclusions or rebaseline.

Observed host diagnostic b7b0b4e39282a7b998fb168e3cd0f1aa333e2d5674f322a8ef38cca401bd4d5c
contains 19 PermissionErrors and 38 unobserved baseline paths; project4/N2-82
match. Agent readback confirms all38files currently exist and hash-match.
All19folders have protected DACLs owned by CodexSandboxOffline, with only
owner/SYSTEM/Administrators access. Both parents inherit normal-user access.
N1 retained tempfile.mkdtemp folders; Python3.14 creates them with0o700 and
protected Windows owner-only ACLs. N3's rglob inventory suppresses scan errors.
This explains the current cross-account observation difference and strongly
supports the old preflight-cause inference; original failed inventory was not
retained, so exclusive historical causation is not claimed.

INTENT: save original57ACL descriptors and38hashes, then add normal account
SAKTHI\\sakth (SID suffix1001) an explicit non-inheritable read/list/traverse
rule on19folders and read-only rules on38files. Preserve every old ACE, owner,
group and inheritance-protection flag. No Everyone/Users grant, write/delete
permission, file execution grant, recursive ACL reset, deletion or bypass.
Before.json under private permission-read-grant-20261019 retains all descriptors
and target/file/doc identities; hash4894b3826f7107b1de83e1ae6efd21b5044bd68316e3b0f04278729f94f3327a.

Done: exact57target allowlist/no-reparse validation, unchanged old descriptors
before mutation, intended vs actual descriptor equality after mutation, all
original458protectedfile hashes unchanged, sealed N3 inputs retained, no N3
claim/receipt created. Direct normal-host read remains separately UNVERIFIED
unless actually observed; static ACL proof must not be called a host read.
Record partial effects on any exception; never replay blindly or delete files.
Recovery reference is the retained original descriptors, not automatic removal
of permissions or data. Run no diagnostic/evaluation and keep retryfalse.

Then reconcile the existing four Fable records, validate their exact staged
bytes and all source preservation, and commit all pending repository changes
locally as a WIP evidence checkpoint. Private runtime/helpers/raw receipts stay
outside Git as previously specified. No push/CI/release/install qualification.

ACL execution checkpoint: the first Set-Acl attempt refused SeSecurityPrivilege
before any target was changed. After.json retains0applied and all57old descriptors/
38hashes still match. Stop that attempt; never rerun it or overwrite its outcome.
PowerShell7.6.5 primary source shows full-section copy plus a fallback comparing
audit protection against access protection; actual target has audit=false and
access=true, so it still requests Audit. No privilege/elevation/ownership change.
Review a separate Access-only successor using fresh DirectorySecurity/FileSecurity
and SetSecurityDescriptorSddlForm(expected, AccessControlSections.Access), then
FileSystemAclExtensions.SetAccessControl. Kernel DACL authorization still applies;
no audit/owner/group section or privilege APIs may be invoked. Same57allowlisted
targets, exact old/new descriptors and hashes, no new grant rights or authority.
If the revised method refuses, retain it and stop; commit accurate partial state.

Access-only result: first directory read ACE applied; exact-text guard stopped
because Windows set AI (DiscretionaryAclAutoInherited,1024). Its two children
also gained AI and reordered the SAME three inherited Allow ACEs; no rights,
owner/group/protected state or38file bytes changed. After-AccessOnly.json retained.
Microsoft documents this resource-manager normalization. Native reviewer SHIP
for a separate bounded continuation: require all57raw descriptors equal that
retained partial state, skip the completed directory, and apply remaining56once.
Use an exact multiset of complete binary AccessAllowed ACEs (duplicate counts
matter), exact owner/group/protected/other control flags, and only AI0-to-1.
Reject Deny/object/callback/opaque/null/empty DACL, ACE additions/removals/rights/
inheritance changes or AI removal. SACL is not read with privilege or written.
Original strict comparator reproduces3expected failures among14controls. First
semantic control run16/17 exposed a swallowed false result in a PowerShell array
expression; preserved unchanged. V2 throws to its outer refusal handler and all
17controls pass, including write/deny/missingACE/protection/owner/group/AI removal.
Prepared-Normalized.json binds exact known partial state/next expected ACLs;
all old source/receipts/claims remain immutable. Any new difference stops work.

### Final permission checkpoint - partial, no fourth write attempt

The normalized continuation added3grants before its raw pre-write guard stopped
at "Concurrent ACL change". Combined with the first directory, current verified
total is4of57 (2directories,2files);53remain (17directories,36files). Setting the
second parent's DACL normalized its children's inheritance metadata before the
child raw-SDDL check. The post-write semantic validator was correct; the remaining
pre-write raw comparison still failed to account for the parent's own effects.
Do not relabel this as a completed permission repair or external interference.

After-Normalized.json SHA256 ffc984df4a75234c1d12b5872b9a75ad73fc1274b7958135cad58da7e0a341c0
and Checkpoint-Partial-20261019.json SHA256 4febc0bfd6978abcaf7ee4cd10cb5f3869b5ff9eab85128f84afe299a84aea6f
retain the exact partial state. All57current descriptors match the saved outcome;
all old access semantics/owners/protection are preserved and all38filehashes match.
No further ACL writes after three stopped write cycles. Fable/Superpowers require
architecture discussion before another correction. User said CONTINUE; perform
read-only verification and the already-approved local commit, not a fourth trial.

Architecture options for discussion only: hold this safe partial state (no further
progress); recommended smallest successor processes pending36files before17parent
directories, verifies known raw state before the operation and semantic invariants
after every own write/final hierarchy check; stronger propagation-aware journal
refreshes every affected child after each parent write but adds complexity. Neither
successor is implemented or executed here. Test parent-induced child normalization
and hostile rights/owner/inheritance drift before selecting another write sequence.
Existing4grants must never be replayed. Any unexpected access difference stops.

Commit authority is local only: all four pending repository Fable records, including
the retained N3 history and latest honest status. No source code or important detail
is removed/disabled/excluded; private helpers/runtime/receipts stay retained outside
Git. A new commit changes HEAD while the old N3 evaluator pins0584a89; do not change
that guard, rerun old scripts or rebaseline. A reviewed exact-commit continuation
and explicit N3 retry authorization remain separate. No push, release or install.

### Approved files-first correction - 2026-10-19

AUTH: the current user requests completion of the remaining36files then17parent
folders with the same strict permission/content checks and explicitly excludes
deletion, push, installation and N3 evaluation. This approves the bounded53grant
successor following the three stopped cycles; it does not approve another commit.
Basis HEAD4f5885656d07bb938560a17451b372bc1ea94da1 is clean. Fresh read-only
verification confirms57raw descriptors equal After-Normalized.json and38hashes
match;4already-complete targets must never be replayed.

INTENT: replace parent-first scheduling only. Freeze all57raw starting descriptors,
skip4completed targets, apply pending36files before17sibling directories. Preserve
exact SID/rights/explicit noninheritance, owner/group/protection, old ACE multiset,
38contenthashes and AI0-to-1-only normalization. Fresh DACL-only .NET persistence;
no Set-Acl, owner/SACL/privilege operations, policy changes or recursive resets.

Options: holding preserves partial access but makes no progress; files-first is
the smallest complete correction; a propagation-aware scheduler adds unnecessary
state for this flat19-parent hierarchy. Weak link: unexpected backend normalization
or concurrent access change. Cheapest falsifier: retained parent-first ordering
regression followed by files-first execution; any unsupported ACL drift stops.

Tasks and proof: (1) reproduce old-order failure and add sequencing/descriptor
refusal controls; (2) prepare a sealed exact allowlist/order and check all current
raw state, reparse/hardlink safety, HEAD and preserved-source hashes; (3) execute
once with exclusive claim/durable per-target intent and outcome,36files then17dirs;
(4) verify all57semantic descriptors/38hashes plus458protected and1015preexisting
N3files and525unrelated repository files, then independent read-only review.
Stop on any unrecognized state; no automatic repeat, rollback, deletion or grant
removal. Original descriptors remain the recovery reference. All fixtures retained.

Fable is the sole governing ledger. Superpowers supplies test-first, inline
execution and fresh-review checks, not a competing plan store. Reuse the existing
isolated development checkout/private evidence; no new worktree, dependency setup,
automatic commit/cleanup or installed-copy replacement. User preservation rules
override skill cleanup defaults. No worker or full product suite is run for this
permission-only task: broader verification is baseline-compared byte preservation,
not a new claim that existing unfinished native/product tests are green.

Done means53new exact grants and57totalverified targets with no content loss or
extra authority. Agent readback proves ACL state, not normal-account runtime reads.
Normal-host read remains UNVERIFIED unless actually observed. The old N3 runner
still pins0584a89; do not bypass it, overwrite baselines or rerun evaluation. A
reviewed exact-commit continuation and separate evaluation authorization remain.

Execution result: COMPLETE_FOR_APPROVED_ACL_SCOPE, normal-host read UNVERIFIED.
Native Sol review SHIP preceded the one files-first attempt. Old natural-order
test reproduced2orderingfailures; successor23/23controls and2actualpreflight
drift/hash refusal probes pass. Initial newhelper preflight caught a PowerShell
array-expression grouping defect at the final countgate before anyACLwrite;
corrected grouping then passed458protected+1015oldN3+525unrelatedrepo hashes.
No baseline or expected count was changed to pass. All old artifacts retained.

Exactly36file then17directory DACL-only writes completed, each with durable
intent and verified outcome;4completed targets skipped. Final57descriptors,
38hashes and oldowner/group/protection/ACEsemantics verify.25priorprivateACL
artifacts and2outertemp-parent descriptors remain byte/raw-identical. No content
deleted or code hidden, no new qualification flag, N3retry, install, commit/push.
Receipt files-first-20261019/Receipt.json SHA256
7ecfc174be19ec2faf1512eb2c6e399715c820b087363807b7a251dfce575c26;
fresh Verification-After.json SHA256
cff8099a9908d8398a2795b9cb46b42ddecf865ea0c4e6c30ff41ecd0157b4fc.

TWINS: the earlier parent-first/raw child-gate attempts remain historical,
stopped, with claims intact. No other target tree or production permission code
was changed. Current helper retains the raw prewrite guard; scheduling, not a
relaxed guard, fixes self-induced pending-child metadata drift. Verdict VERIFIED
WITH CAVEATS for ACL scope only; this is not N3 or whole-skill readiness.
Next: reviewed normal-host readback and exact-current-commit N3 continuation;
old evaluator/diagnostic remain stopped. New Fable record edits uncommitted.

### Approved checkpoint commit and read-only N3 continuation - 2026-10-19

AUTH: "COMMIT EVERYTHING YOU FINISHED AND COMPLETE next step ... reviewed
normal-account readback and an N3 continuation ... Do not rerun the old N3
command or bypass its commit guard." Finished4Fable records committed locally
as4ef9638427e81a23d6ef5f2ee4b9ae133fb3d701, parent4f5885656d07bb938560a17451b372bc1ea94da1;
4committed blobs hash-match reviewed bytes,0files deleted, clean tree before
this continuation plan. No push. Machine-specific helpers/runtime/rawreceipts
remain outside Git by existing approval boundaries; no silent mass upload.

INTENT: build a separate read-only continuation/readback gate, pinned exactly to
4ef9638 and frozen original evidence. Old evaluator/contracts/Before/Prepared/
runtime/index remain byte-identical. Do not replace base.HEAD or monkeypatch
original preflight; no --ignore-head option, newbaseline, automatic retry or
evaluation authorization. This stage's proof is a continuation/readback packet,
not a replacement evaluation engine or a native/release qualification.

Options: hold leaves normal read unverified; rerunning or weakening oldguard is
rejected; recommended exact-commit read-only successor independently checks
commit ancestry/diff,529repositoryidentities (525unchangedproduct+4alloweddocs),
458protected project/N1/N2 hashes and1015preexistingN3 hashes. Existing public
evaluation requirements/4questions/29tests remain unchanged for later activation.
No duplicate worker, retrieval, ranking, evidence-acceptance or fence mechanism.

Task1: frozen read-only checker/core and retained tests. Tests must catch wrong
commit, forbidden source delta, stale/added/missing source, scan/read denial,
reparse/hardlink traversal, wrongaccount/elevation, changed legacy inputs and
duplicate attempts. Use Python3.14 stdlib and Windows token-query APIs only;
no worker/interpreter launch beyond controller, network, install or ACL write.
Task2: externally hash-bound PowerShell launcher validates actual normal SID
S-1-5-21-2571509308-2482563067-4170768140-1001 and non-elevation, records all
check failures in one new retained receipt; no false complete inventory.
Task3: test RED/GREEN and live agent read-only preflight, inspect frozen source
preservation, fresh native review of exact handoff, update this existing ledger.
Task4: normal-account readback requires the human's existing PowerShell context;
do not impersonate, solicit credentials, elevate, schedule or alter security.
If agent cannot run with normal SID, hand over only the reviewed command.

Done for local build: executable reviewed readback/continuation gate, pinned
newcommit and all oldinputs, negative controls, retained results. Host-read done
only after actual normalaccount observation. N3-B/C evaluation and29runtime tests
remain unrun and evaluation_retry_authorized=false; future execution needs its
own reviewed successor/authorization. Any new inaccessible original path stops;
no expansion of prior19folder/38file ACL grant, skipping or rebaseline.

Ruling: retain existing isolated development checkout/private artifacts and
singleFablegovernor, not a new worktree/environment/competing plan store. Retain
all old and new fixtures (user no-deletion overrides skill cleanup). This request
approved the finished checkpoint commit; new continuation edits remain local
unless separately authorized for commit. All helper claims are local self-
reported observations, not authenticated producers or qualification authority.

Build outcome: native independent review FIX_FIRST identified5loadbearing gaps
(optionalGitwrites, PATH-selectedGit, preclaimerrors, postreadpathswap/JSONreopen,
missingfinalHEAD/status/docsrecheck). Parent acceptedall and completedONEfixpass
with5targetedREDfailures and24/24GREENcontrols. No secondnativeSHIP claimed.
Correctedagentpreflight00533a38 verifies525product+458protected+1015oldN3+3index
files; Gitindex unchanged/finalrevision reread, actualsandboxSID1003. Full product
CI/N3's29runtime tests not run or represented by these local controls.

Ruling: one retained private scratchGit fixture init/config/add(no commit) proves
index behavior; no sourceGit or globalconfig writes by the corrected host helper.
The installed Git dispatcher naturally has2hardlinks (cmd/git.exe/git-lfs.exe);
pin its path/SHA/count2 only, while source/evidence remain strictcount1. Actual
fixture path-swap uses non-overwriting renames and retains both files. Old agent
preflights are retained but superseded for their unproven no-Git-write claim.
Review-and-Fix-Record.md retains findings/tests/rulings in the private continuation
directory. All5reviewfindings fixed; none deferred. Normalhost readback remains
unobserved, no evaluationretry; prepare/seal final3helperfiles/currentdocs only
after this record. User must run from actualnonelevatedaccount1001; agent cannot
impersonate it. Parent handoff verdict: VERIFIED_WITH_CAVEATS, not fullN3ready.

### User-approved readback checkpoint commit and exact rebind - 2026-10-19

AUTH: user "CONTINUE AND COMPLETE FROM WHERE YOU STOPED, AND COMMIT IT".
The finished4readbackFable records are now authorized for a containing local
commit. No push. Prior4ef9638-bound helper/Prepared/launcher and allrawartifacts
remain byte-identical and RETIRED_UNUSED after that commit; actualnormalhost
claim is absent. Do not hand over or run the oldcommand after HEADchanges.

Approved continuation of the same scope: after committing these4records, create
one sibling private directory named continuation-readback-20261019-<newshortHEAD>.
Reuse the verified3helperfiles with ONLY the literal EXPECTED_HEAD and launcher
checkerSHA changes; tests copied byte-identically. Prove normalizedsource equality,
newHEAD ancestry/original525source hashes and alloldinputs; rerun24controls and
23ACLcontrols. Seal a NEW Prepared in that newdirectory; never edit/reuse old
Prepared or change an oldguard. Oldguard must still reject the newcommit.

No new mechanism, evaluator, worktree, environment, sourcechange or permission
grant. Same actualnormalSID1001/nonelevation, one-shot receipt, noGitwrites,
hardlink/source protection and unauthenticatedpointintime caveats. No second
independentSHIP claim; priorfivefindings remain fixed/tested, no logicdiff.
This containing commit is the exact newbasis, resolved only after it exists;
the successor then hardcodes the resulting SHA. Keep repository unchanged after
that commit so the sealed handoff is commit-consistent and the tree stays clean.
Private postcommitproof and Handoff give exact measuredidentities. If rebind,
comparison, preservation or controls fail, stop and retain everything; do not
send a hostcommand or claimnormalread. Actualhostread remains the human-only
lastgate; no N3evaluation/29runtime/N3-D activation, install, deletion or push.

## Approved N3 evaluation continuation implementation plan - 2026-10-19

> For agentic workers: use superpowers:executing-plans inline, with one fresh
> native read-only final review. This section is the sole plan/ledger.

AUTH: "AUTHORIZED DO COMPLETE NEXT STEP ... IF NEEDED, MAKE A CLONE OF N3
AND DO CHSNGES FOR TESTING" approves the preceding five-step N3-B/C/D
continuation proposal. No new install/download/external AI/native Beads/ACL
change/deletion/commit/push/package/installed-copy replacement is included.

Goal: evaluate the existing retrieval implementation using the unchanged four
coding questions, original source obligations/bounds and exact29test selection.
Architecture: separate private evaluator successor and input-only clone; reuse
the old measurement/replay/safety functions and installed53package environment.
Do not run or modify the old evaluator or monkeypatch its base.HEAD/preflight.
Tech stack: Python3.14 stdlib controller, existing isolated Python3.12 worker,
PowerShell launcher; unchanged lexical/LSA/Semantica implementation.
Spec: original N3 section of this file, frozen Oracle.json and v3 contracts,
plus the user-approved five-step continuation proposal immediately above.

Observed basis: HEAD a6ee520b81e860ffaf6360d030c548aa53464381, clean development
checkout before this plan. ActualnormalSID1001/nonelevated readback succeeded;
receiptSHA0f8b59631efae98e716603a1b998dd52822fdec5d006af439a332aa4d781ec86.
All525product+458protected+1015originalN3+3index identities matched. Its false
evaluation_retry_authorized is historical read-only scope, not a missing initial
N3 approval. Preserve that receipt unchanged; this new authorization is separate.

INTENT: prior evaluator stopped before its host claim because original evidence
could not be observed from the normal account; permissions and actual readback
are now proven. New evaluation explicitly verifies current commit/readback and
unchanged original inputs, rather than disabling an existing stale-commit guard.

Options: hold produces no quality measurements; changing old guards destroys the
frozen handoff and is rejected; copying the entire environment creates redundant
runtime/install authority and is rejected. Recommended input-only clone, with
separate outputs/claim/receipt and new strict preflight. Source code unchanged.
Weak link: execution-context access to the existing WindowsApps-based worker.
Cheapest falsifier: one retained interpreter-identity probe before consuming the
actual evaluation attempt. Agent denial produces a normal-host handoff, never
impersonation, alternate Python, security change or automatic resend.

Global constraints: no deletion of ANY old or new files/fixtures; no question
retuning, source/canary expansion, pin changes, learned-model calls or package
updates. Existing old Before/Prepared/contracts/index remain byte-identical.
All outputs create-new. Keep metadata local/self-reported/unauthenticated and
semantic_quality/whole-skill/native/release qualifications UNVERIFIED/false.
Surrounding system must remain healthy against both original and new seals.

Review focus (with owning tests): wrong/stale commit or failed/unbound host
receipt (Task1 contract); input-copy/path alias or old-output write (Task1
clone); denied scan/path replacement (existing24guardcontrols plus Task1
preflight); postidentity failures/replay (Task1 attempt); subprocess side effects
and discovery/mandatory mislabelling (Task2 existing runner/measurement suites).

### Task N3-CONT-1: exact-commit successor and isolated input clone

Files under private n3-retrieval-.../: Evaluate-N3-Continuation-20261019.py,
Test-N3-Continuation-20261019.py, Run-N3-Continuation-20261019.ps1;
new evaluation-continuation-a6ee520-20261019/ only for inputs/results.
Consumes unchanged v3 contracts, original Prepared input hashes/index and
continuation-readback-20261019-a6ee520/continuation.py/normal host receipt.
Produces preflight(prepared=True), prepare(), run_evaluation() using exactHEAD,
strict readback/preservation checks, fresh clone and durable one-shot attempt.
- [ ] Write/run failing continuation tests: invalid host receipt/context, wrong
  HEAD/input hashes, repeat claim, postclaim preflight failure, clone preservation.
- [ ] Copy the old coordinator into a new filename, then change only orchestration
  gates/clone preparation/attempt capture; measurement/query/safety ladder and
  exactly29test IDs retain their original behavior and limits.
- [ ] Run focused controls and prior evaluator/runner contract suites; retain
  RED/GREEN outputs and fixture files. Expected zero unexpected failures/skips.
- [ ] Prepare clone with create-new files; verify source/template/index equality,
  original guard still refuses currentHEAD, all original evidence/runtime hashes.

### Task N3-CONT-2: review, actual evaluation and N3-D handoff

Consumes Task1 helper/clone hashes, original frozen questions/bounds/test IDs;
produces sealed Prepared/launcher, evaluation Receipt-host.json, honest report.
- [ ] Fresh native reviewer checks exact handoff; one parent Critical/Important
  fix pass with RED/GREEN tests if needed. No unreviewed automatic execution.
- [ ] Freeze allhelper/current4Fabledoc/input identities; preserve old packets.
  Run identity probe once; if agent cannot launch worker, provide one reviewed
  normal nonadministrator host command under this approval (not a new ask).
- [ ] Actual evaluation:24case/mode/arm measurements or explicit failed-arm
  results, fresh-process verification, stale/access/budget/forgery controls and
  exact29tests. Failure retains receipt, never retries or claims missing quality.
- [ ] Review actual results, independent review where available, recheck all
  preservation and record honest quality/readiness limits. No automatic release.

Ruling: this continues the already approved design and inline method; no repeat
brainstorm interview/approval, newworktree or competing Superpowers ledger.
Commit/cleanup steps in skill defaults are NOT authorized; retain everything.
No shell-specific task scripts that create a competing workspace are run; this
section records brief/BASE/tests/rulings/completion. BASE for both tasks=a6ee520.
If actual host execution is unavailable here, Task2 stays PARTIAL with exact
human-only command/receipt gap; do not mark N3-D runtime review complete.

Task N3-CONT-1 progress:9newcontrols GREEN after9expectedmissingfeatureRED;
25existingmeasurementcontracts+7existingrunnercontrols GREEN. AST comparison
verifies unchanged13query/measurement/replay functions and actual case/safety/
29test ladder. Original input/metadata/full17,273file installed-runtime preflight
passed without starting any query.53installedpackage identities/12setup logs
verified. This is current file identity plus historical positive-control evidence,
not a newly observed retrieval result. Fresh native code review still pending.

Ruling: one interpreter-only probe used the existing verified venv launcher,
not an alternate runtime. Stub started but exited103; stderr says "No Python at"
the normal account's WindowsApps Python3.12 path. Probe Result.json SHA256
8124d2784631c987d6ad08ffb2b97cffb7f28817b7c3a529fcdcc06783dc04fe.
No retrieval/evaluation claim was consumed. Actual evaluation requires the
normal account's execution context; provide one reviewed host command under
the existing approval, not another install, ACL change, identity spoof or retry.

## CHECKPOINT: user requested commit before usage limit - 2026-10-19

AUTH: "COMMIT EVERYTHING, WHICH IS FININSHED SO FAR, MY LIMIT IS going to over,
so need to save the details in git on whats completed so far, and to continue
from which we left". Stop further build/evaluation and commit the four current
Fable records locally. No push. Preserve all private helpers/fixtures/receipts
outside Git as before; their exact identities and resume details are recorded
here and in the report. Do not silently upload machine-specific runtime/raw data.

Status: NOT_SAFE_TO_FREEZE_OR_RUN. Native reviewer returned FIX_FIRST, one
Critical and two Important findings. No correction pass has started. No new
evaluation directory, Prepared seal, host claim, query or evaluation receipt
exists.9new+25existingcontract+7existingrunner controls are green but do NOT
close the review findings. Full existing runtime/input identity preflight passed;
agent interpreter stub exited103 as documented. No task/milestone/N3-D is done.

Resume artifact root (retained private):
C:/Users/sakth/Documents/Codex/2026-10-02/ad/work/R5-practical-fence-20261013/build-validation/n3-retrieval-9ec6fb1db36444acba2945896e8b8d17/

| WIP artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Evaluate-N3-Continuation-20261019.py |31717|5b915b282b997221b26cbb54204e896c7c3017522b9362111bf42231b09b8c80|
| Test-N3-Continuation-20261019.py |8106|e87e417ba33d742ec630b6d37f504617e1b86927cf83bd34bb46edf93a929c06|
| Run-N3-Continuation-20261019.ps1 |2137|bb52d63815d1a57d16acbf7a5269ed89065318bd108d22df881fcc27d0ea70a7|

### Required next correction pass (not implemented)

1. BEFORE ANY WRITE, verify the exact canonical output root and every existing
   ancestor with the pinned no-reparse reader. Reject a junction/symlink/root
   substitution before mkdir(host-claim). RED test must prove no target marker.
   Finding: coordinator115-117/368-376; launcher16-17. Critical.
2. Run one retained exact interpreter-identity probe in the actual normal-host
   context BEFORE evaluation claim. Agent probe is historical, not host proof.
   A failed host probe must leave no evaluation claim and must not auto-repeat.
   Finding: launcher21/coordinator368-369 versus plan preclaim requirement.
3. Externally bind the reviewed Prepared SHA through launcher/controller/child
   entrypoints; parse bytes captured by guard.safe_file only. Reopen clone inputs
   with that reader (hardlink/open-handle/postread path protection). Child gate
   must verify the external seal and relevant operation inputs. RED controls:
   altered Prepared; input+its self-hash co-edit; postprepare hardlink/path
   substitution; child-side substitution. Current mutable self-attestation fails.

Then ONE consolidated parent fix pass to GREEN, whole relevant offline suite,
new input-only clone and exact seals, host-only command under existing N3
approval, actual24arms/replay/safety/exact29tests and independent result review.
Do not launch until Critical/Important fixes and preservation pass. No new
runtime, install, model/native Beads/ACL operation or deletion is authorized.

Ruling: this containing checkpoint changes HEAD. All a6ee520-bound handoffs
are RETIRED for new execution, not edited/reset. Resume must obtain the actual
containing SHA with git rev-parse HEAD and build a separate successor pinned
to that exact SHA, updating current guard/Prepared/launcher identities together.
Preserve old base.HEAD=0584a89 and every old file/claim. The successful normal
readback receipt remains historical evidence for a6ee520; it is not relabelled
as a readback of the new commit. Compare the containing commit's diff (only
four approved docs) and all original product/input hashes before rebinding.
Cost if wrong: stale handoff or falsely promoted provenance. No old command run.

### Reviewer set-asides: parent rulings, all still unverified

1. Clone equality/seal: absent, must be observed after fixes; otherwise false
   prepared-input assurance.2.Normalhost launch: agent103 is not host failure;
   require own preclaim observation or execution remains blocked.
3.24arms/quality: unrun; no IDs/scores/hits/misses/OOV/pack bytes invented.
4.Fresh replay/safety: source-inspected only; require actual refusals/replay.
5.Exact29tests: selection preserved, not executed; never count as passed.
6.Real subprocess side effects: audit hook is not an OS sandbox; unobserved,
   do not assert actual network/filesystem/process containment.
7.N3-D: no actual results to review yet; code review is not result review.
8.Semantic/coding/product/native/release/install/fullCI benefit: outside this
   code review, all prior UNVERIFIED/false labels remain unchanged.
9.Future commit: explicit rebind required above; no --ignore-head/base mutation.

Deferred minors: fixture digest annotation misleading (hash recomputed in test);
native_execution flag ambiguous (means no native Beads, not no Python worker);
7runnercontrols target old evaluator (reported only as inherited controls).
Hard-abort/receipt-write failure may leave marker only: Ruling that means UNKNOWN
and no automatic repeat/acceptance, not a completed receipt. Add an immediate
create-new attempt-intent record in the resumed correction pass; do not claim
OS-process-interruption recovery proof. Cost if wrong: unknown partial execution.

Verification before commit: rerun9new+25oldcontracts+7oldrunnercontrols, JSON
parse/diff check, exact4stagedpaths/no deletions and committed blob identity.
Current WIP code and its failing-review state are retained without modification.
No push/installation/qualification activation. This is a resume checkpoint only.

## Approved correction pass resumed from 484d2ca - 2026-10-20

AUTH: "Continue from commit 484d2ca ... Verify the saved private artifact
hashes, fix the three review blockers with regression tests, and bind a separate
successor ... Do not run the old N3 commands, delete files or bypass guards."
Verified exactHEAD484d2ca83f5bed71c0f163e8614add2cedbe976b/clean checkout and
all3privateWIP hashes above. No correction previously existed; resume the one
consolidated parent RED/GREEN pass from the completed FIX_FIRST review.

INTENT: current WIP permits preclaim root aliasing, claims before actualhost
probe, and trusts mutable Prepared/selfhashes. The approved successor must
refuse all3 before query/evaluation effects and preserve the original evidence.

Private surfaces: Evaluate-N3-484d2ca-20261020.py,
Test-N3-484d2ca-20261020.py, Run-N3-484d2ca-20261020.ps1 at the original run;
continuation-484d2ca-20261020/continuation.py is a separate mechanical guard
copy pinned to484d2ca. New outputs only in evaluation-484d2ca-20261020/.
The old3WIP artifacts/guards/receipts/Before/Prepared/runtime/index are immutable.
Original normalaccount receipt0f8b5963 remains labelled observed at a6ee520;
current484d2ca ancestry/4doc-only delta/525product identities are independently
checked. No new normal-account readback claim is manufactured by rebinding.

Decision: retain input-only clone, existing runtime and full old measurement
ladder; hold is safe but makes no progress, editing old guards is rejected.
Use native directory handles with read/write sharing but no delete sharing to
hold verified output ancestors while writes occur, in addition to no-reparse
checks. They change no ACL/privilege/trust configuration. Microsoft CreateFileW
documents directory handles and the delete/rename sharing rule:
https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew
This is pathname protection, not an OS sandbox or authenticated producer.

Correction tasks and done evidence:
- [ ] RED controls: root/ancestor junction refusal before marker; attempted
  root rename while pinned; failed hostprobe leaves no evalclaim and refuses
  repeat; successful synthetic probe precedes durable attempt intent; wrong
  Prepared/external seal and input+selfhash coedit; hardlinked/postread replaced
  input; child dispatch/input substitution; wrongaccount and stalecommit.
- [ ] Implement directory pin before any output/probe/claim write; one retained
  normalhost interpreter probe BEFORE hostclaim; immediate fsynced intent after
  exclusive claim. Hardabort/receipt-write failure stays UNKNOWN/no retry.
- [ ] CLI requires externally supplied Prepared SHA for inspect/run; child
  environment carries that exact SHA plus a parent-created per-operation packet
  hash. Parse verified captured bytes; verify original immutable input-map scope,
  helper/doc/index/runtime-manifest/host-receipt pins and relevant child inputs.
  Prepared includes launcher hash, so external seal must be supplied AFTER
  preparation, not embedded into a circular launcher/Prepared hash dependency.
- [ ] GREEN full relevant offline controls, actual pathname/junction/rename
  probes, original input/source preservation and exact clone identity. Keep
  tests/fixtures/results retained. No second independent SHIP claim: completed
  review's one parent correction pass is verified by its regression tests.
- [ ] Update4Fable records before final sealing, then prepare new clone/Prepared
  and hashchecked normalhost command under existing N3 approval. Agent's saved
  exit103 is not retried or turned into a host verdict. Actual N3-B/C/29tests
  and N3-D remain unobserved until real normalhost execution and result review.

Rulings: keep existing isolated development checkout/singleFableledger and
inline execution; no new worktree/install/environment/commit/push/delete.
Fresh fixture junctions and attempted renames are confined to new retained
test directories only, never original outputs. Recheck target hashes before
edits; stage nothing. Stop on preservation/scope contradiction, not by weakening
checks. Parent directory pins require no elevated or backup privilege enabling.

### Correction outcome and host preparation boundary - 2026-10-20

The ONE parent correction pass implements all3 reviewed blockers in the separate
484d2ca successor. First new controls were RED (9failures/0errors); final focused
controls15/15, rebound readback guard24/24 and existing measurement contracts25/25
are GREEN with0errors/skips. These64 are offline controls, NOT the29runtime tests.
Every fresh fixture, junction, failed run and old artifact remains retained.

Final: fixed preclaim root aliasing - actual root junction/noncanonical path
controls RED->GREEN; full existing directory chain is checked and held open with
read-only Windows handles BEFORE output/probe/claim writes. An actual fresh
single-component rename control passes. Metadata-only access0 did NOT block
rename in a retained failed experiment; GENERIC_READ is the tested component
mechanism. No backup privilege, ACL change, ancestor skip or security bypass.

Final: fixed claim-before-host-probe - failed synthetic probe leaves no claim,
cannot repeat, and public-run ordering control passes. A successful real normal-
account existing-Python identity probe must precede evaluation claim. A caller-
seeded success JSON is insufficient: the same process must retain the successful
probe digest. Claim immediately records a create-new fsynced intent, not success.
Hard abort/receipt-write failure remains UNKNOWN/no automatic replay.

Final: fixed mutable Prepared/selfhash trust - external Prepared SHA is required
by inspect/run and propagated to children with a per-operation dispatch hash.
Captured verified JSON/inputs use the existing single-link/no-reparse/open-handle/
postread reader. Controls reject Prepared+input coedit, hardlinks and substituted
operation inputs. The valid-dispatch and exact original-input clone component
controls pass. Readback guard tests cover postread pathname replacement. Helper,
doc, index, original-input-map, historical host-receipt and runtime-manifest pins
are checked; original base.HEAD remains0584a89 and old artifacts are unchanged.

Ruling: actual full-chain GENERIC_READ opening is denied to this sandbox account
at C:\Users\sakth (WinError5). Component controls use an explicitly limited fresh
fixture; they do not prove normal-host full-chain access. DO NOT weaken/skip the
ancestor or change ACLs. Cost if wrong: host preparation may stop safely. Hand
off preparation ONLY in normal nonadministrator PowerShell, requiring15controls
plus a real full-chain/rename control there; then full input/runtime preflight,
one new input-only clone and printed Prepared SHA. No worker/probe/claim/query
runs in Prepare mode. Real evaluation directory/Prepared remain ABSENT now.

Ruling: external Prepared seal is obtained in two stages, avoiding a circular
launcher/Prepared dependency. First freeze coordinator/test/launcher hashes and
request only -Mode Prepare. Inspect the saved host-control receipt and captured
Prepared against the original pins independently. Only then provide the distinct
-Mode Run -PreparedSha256 <verifiedSHA> handoff under existing N3 authority.
Do not supply Run yet, infer a pass, or use a self-reported seal without checking.
Cost if wrong: an incorrect handoff is held, not silently authorized.

The original completed FIX_FIRST review remains the review evidence; TDD verifies
this consolidated fix pass. No second independent SHIP claim. Deferred minors:
old fixture digest annotation; old native_execution label ambiguity (no native
Beads, not no Python); old7runnercontrols do not exercise successor gates. Runtime
results/N3-D, real subprocess containment, semantic benefit and whole-skill/native/
release/install/fullCI readiness remain UNVERIFIED. No second engine/plan ledger,
commit/push, original-file deletion or installed-copy change occurred.

Resume here: use current484d2ca-bound private HANDOFF.md and final proof, verify
frozen hashes/HEAD, request ONE normal-host Prepare only. Never run old N3/WIP
commands. Future commits change HEAD and require another explicit successor;
these4Fable updates are intentionally uncommitted until separately authorized.

## Approved child-context repair and local Git checkpoint - 2026-10-20

AUTH: user said "COMMIT WHAT NEED TO SEND TO GIT WHAT YOU FOUND TO SOLVE ISSUE"
and "DO REMAINING NEEDED WORK TO FIND AND SOLVE REMAINING ROOTCAUSE" after the
bounded successor/one-fresh-attempt proposal. This approves that local repair,
tests, evidence, new successor binding and local commits, not push or new trust,
ACL/owner/global configuration, installs, deletion or qualification activation.
The prior484d2ca attempt remains CONSUMED_FAILED; never reset/reuse its markers.

INTENT: installer-only environment scrubbing drops existing user Git context,
and invoke parses empty stdout after a failed child. The required behavior is
the SAME validated existing profile for child Git reads, a real child-context
preflight BEFORE claim, and structured original exit/stream diagnostics before
JSON parsing. No ownership/trust check is skipped and no new exception is added.

Scope: .github/scripts/n3_child_transport.py and its .github/tests regression;
this existing plan/resume/report/state plus child-context repair evidence. Keep
all skill/companion code, packages/manifests, Semantica and installer unchanged.
Use a separate private coordinator/guard/test/launcher successor after the local
commit exists. Raw private environments/logs are not copied to public Git.
Only a sanitized factual failure summary and reviewed reusable repair belong
in Git. Scope inventory and all old hashes must be checked before staging.

Decision (Deep Plan under Fable): hold/no-build preserves safety but cannot
finish N3; validated existing USERPROFILE propagation plus preclaim child read
is the smallest adequate route; a new normal-owned checkout is a larger identity
migration and is rejected for this bounded repair. Evidence families: captured
normal-host stderr/result; source environment/parse logic; paired real read-only
Git environment experiment (agent context); official Git config semantics.
The first two explain one failure and are not independent successful trials.
Weak link: normal-host downstream retrieval still unobserved. Cheapest falsifier:
the exact intended child context fails Git read before claim. Pivot/stop on any
needed trust/permission change, unexpected committed file, preservation mismatch
or3same-issue failed repair cycles. No invented success probabilities.

Implementation order and acceptance gates (existing Fable ledger only):
- [ ] Preserve/recheck failed receipt d4da3f8f, Prepareda50729c1 and old helpers.
- [ ] RED: missing/mismatched/unsafe profile and secret/config inheritance;
  nonzero+empty/malformed stdout, timeout/start failure, stream/hash substitution;
  valid success AND valid structured refusal remain distinguishable.
- [ ] GREEN: portable transport module adds only a validated inherited profile,
  preserves offline restrictions, binds retained streams, reports original
  failure and refuses malformed output; no global installer/env changes.
- [ ] Wire separate successor: same-env child Git/identity/readback before
  Python probe and evaluation claim; failed context is retained/no-auto-repeat.
  Before claim require both same-process successful probes, not caller JSON.
- [ ] Baseline-compared repository suites and native read-only Git comparison;
  fresh native whole-change review; ONE parent RED/GREEN fix pass if needed.
- [ ] Publish accurate diagnosis/results/resume locally with exact staged scope,
  no deletions/secrets; verify commit blobs/tree. No push.
- [ ] Bind NEW guard/output/launcher/Prepared to actual resulting commit; verify
  original529file baseline plus explicitly pinned added files, never broaden
  arbitrary paths. Preparation/external seal precede the ONE approved new host
  evaluation. Normal-account execution remains human-only when sandbox refuses.

Rulings: user-approved description is sufficient; no repeated brainstorming
interview. Reuse current isolated development checkout and this Fable ledger,
not a second Superpowers workspace/plan. All scratch/results retained: user
no-deletion overrides skill cleanup defaults. Local commit changesHEAD; old
commands stay retired, all old files unchanged. The postcommit source scope
must explicitly enumerate added transport/test/evidence paths and hashes,
while525existing product hashes remain unchanged. Cost if wrong: handoff holds.
No native/provider/model calls or environment substitution. One native read-only
reviewer is required by executing-plans; no external AI consultation is included.

Reviewed checkpoint disposition: initial native Sol review FIX_FIRST,0Critical/
2Important. Parent accepts both: inherited dirty-Fable allowance now refuses
every dirty path (new test RED for all4Fable documents, GREEN after repair),
and records now separate historical/current/publication states. One correction
pass only; no second independent SHIP claimed. Guard suite grows from28to29.
Postcommit21successor+29guard verification and exact binding remain required.
Reviewer declined host execution, postcommit proof, general public CLI repair,
full package/CI health and retrieval/release readiness. No scope is broadened.

### N3-D actual-result closure - 2026-10-20

Approved N3-A-D is complete WITH CAVEATS as a bounded local evaluation, not a
release/install/native/semantic qualification. Executed source0532d5b0f9e1d2bd1b65dc07f39de39bae257287;
Prepared4f68aaf85c4b6e2c44ecf371eb9aee980db62e527ed82b5a36b918c11974d987;
Receipt ed368a54870e1a1a5075b47a3cfdcb045bf9561022454f8c056d360c836ee1d1.
Both parent saved-byte audit and one fresh native actual-results reviewer pass
the bounded evidence. Report's current top section maps the full bundle, hashes,
limits, numerical misses and retained artifacts. Old snapshots above stay history.

| Requirement | Observed closure |
| --- | --- |
|N3-R01 authority|Original N3-A-D approval and bounded successor approvals retained; no new outward action|
|N3-R02 isolation|Existing absolute venv/no user site;17,273runtime files match; no installed-copy promotion|
|N3-R03 pinned identity|Python3.12.10 probe,53pins, Semantica0.7.0/pinned revision and retained worker outputs|
|N3-R04 real operation|Historical positive plus16actual lexical/LSA arm workers, finite scores/SHACL and fresh replays|
|N3-R05 discovery|24arms; both graph modes6/7required file hits; approval/workflow miss retained; mandatory excluded|
|N3-R06 comparable limits|Same4sources/52nodes,5results,0hops; literal units vs graph node closure disclosed; no LSA superiority|
|N3-R07 current evidence|25fresh verifier processes,17worker-backed/8literal; exact primary request/response byte replay|
|N3-R08 safety|5named no-pack refusals,5rehashed forgeries, optional-stale exclusion preserves required work|
|N3-R09 nonregression|Exact29approved IDs,0errors/failures/skips; not fullCI/learned embeddings|
|N3-R10 preservation/handoff|Parent full saved-byte audit, fresh independent SHIP for this scope, current4Fable records updated|

Readiness labels: INSTALLATION_OBSERVED; WORKER_RETRIEVAL_OBSERVED;
CASE_QUALITY_MEASURED_WITH_DISCOVERY_MISS; SEMANTIC_TRUTH_UNVERIFIED.
No algorithm/ranking/public CLI/skill code changed during N3-D. Poor discovery
blocks sole-search reliance on the affected task, not truthful experiment closure.
The actual Git child-context defect is absent in this normal-host run; it is not
proof of every future environment. All N3one-shot commands are now consumed and
must not be reissued. Independent review's reporting caveats are incorporated;
no second review or extra runtime execution is requested. No files were deleted.

These four documentation updates were reviewed before publication. The user
subsequently authorized their local commit with "COMMIT"; no push/install/new
runtime or qualification activation is included. Existing release/package/native
gates remain unresolved. Propose separately a bounded real-project coding trial
with explicit mandatory sources/tests and measured task outcome before advising
large-project reliance; do not silently start that trial or a new fence mechanism.

### Offline-first successor release - proposed design, 2026-10-20

The user now requested finishing the narrow offline-first release in three work
packages: existing-core blockers/use, matching verified delivery, and separately
approved installed use. N3-A-D remains COMPLETE_WITH_CAVEATS; do not repeat it.
Source/publication basis is c398be73e9e5eaa14de9e870c7787f53605afd6f on the
existing development branch. Before these planning edits the tree was clean.

Canonical continuation documents in this same Fable store:
- [Full proposed design](offline-first-release-design-20261020.md)
- [Proposed inline implementation plan](offline-first-release-plan-20261020.md)

These documents are draft design/planning, not a completed release or product
change. The explicitly requested Brainstorming/Writing Plans skills require
human review of the full description before inline implementation. The user
already selected executing-plans; do not ask for the execution method again.
One fresh read-only builder check is requested; record its actual result, not
an assumed pass. Separate installation/commit/push/outward gates still apply.

The proposal preserves the existing engines, native WIP, historical capability
facts and R3/R4/knowledge-v2 archives. It recommends a tested restrictive active
profile, a demonstrated worker-lifetime repair (not error suppression), a portable
coding/source fixture and new successor manifests/ZIPs. The existing builder
rewrites R4-CONTENT and prior ZIP paths, so do not run it unchanged for this work.
Current CI evidence: run39396331789 fails all8jobs at content preservation;
run39396331869 has source/package mismatch and Windows3.12 distributed-local
WinError32 with1failure/5errors. Those are observations, not a confirmed root
cause or permission to skip tests. No native/worker/model/test command, dependency
change, commit, push or installed-copy replacement ran during this planning step.

Builder check returned FIX_FIRST with3important questions. The design/plan now
state the parent's proposed answers: no local deletion even of ephemeral outputs;
retained extraction and nondeleting handle probes, with hosted cleanup separately
gated; ALL Beads/Dolt subprocesses disabled and native UNKNOWN remains frozen;
distributed-local retained as an included mode with a mandatory runtime regression
gate, no silent descope. This is one parent clarification, not a second reviewer
SHIP or product completion. Human full-design/plan review remains the next gate.
