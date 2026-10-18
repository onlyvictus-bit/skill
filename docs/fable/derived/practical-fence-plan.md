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
