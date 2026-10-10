# M7 / R5 step 1 — recovered basis and bounded requirements freeze

Status: planning records constructed; historical specification recovery PARTIAL.
R5 implementation, native qualification, package release and installed promotion are NOT COMPLETE.
Canonical authority remains requirements.json, plan.json, tests.json, approvals.json and state.json in docs/fable. This report and the acceptance matrix are derived views.

## 1. What existed before this step

Baseline main: b5165424f0f019ae300e7a8f773712c4dbeb42ec; tree c3e9c597922ac6b8a2ef64eefe2f949d5d47a540.
All 12 branch heads returned by GitHub were pinned and searched, relevant M7/R4 commits were inspected and the required sources/test oracles reopened. The exact per-source byte identities, required read spans, branch hits and previous Fable state are in r5-source-basis.json. Search hits are discovery, not complete-read proof.

Existing committed sources include docs/FOUR-FEATURE-PLAN.md, docs/NATIVE-QUAL-01.md, docs/STATUS.md, references/m7-native-observation.md and R3/M7/R4 tests. Historical milestones M3 contracts, M4 prerequisites, M5 protected history and M6 fixture merge are present. Real observation, injected-after-effect recovery and production shared-claim protocol are recorded as qualified within their exact scopes. There was no complete R5 scope freeze or R5 release identity in these sources; GitHub commit search for R5 returned no results.

The full original four-feature specification says it lives in the project workspace, but is not in the searched branch snapshots. Its exact four-trap grouping remains NOT_RECOVERED. GAP-ORIGINAL-FOUR-TRAP blocks any claim that the original M7 comparison is complete. Recover the original with provenance or explicitly adopt a replacement; never silently relabel the following candidates as original requirements.

The native pilot executes adapter.execute and then raises InterruptedError (native_pilot.py lines 305-340). That is an injected interruption after a returned native effect. The broader historical wording about kill/during-claim proof cannot establish an OS kill inside the native command. R5 separates those experiments.

## 2. Requirement matrix and operation boundaries

R5-STEP1-* criteria govern this documentation step. R5-IDENTITY/OWNERSHIP/DEPENDENCIES/MERGE/RECOVERY/HISTORY/COMPARISON/PACKAGES/PUBLISH/INSTALL/OPERATIONS describe future outcomes and are explicitly future, not executed or implicitly authorized by a planning record. Promote the relevant criteria to required, include actual code targets in approved artifacts and bind current authorization before implementing a subsequent milestone. Earlier Semantica requirements/tests are preserved without edits or priority changes; their old evidence remains historical on its original basis.

| Operation | Existing scope | Intended R5 boundary |
|---|---|---|
| Exact read-only native observation and operation readback | Qualified for pinned selection, with declared observation limits | Reuse observer and prove current identity; no atomic-fence inference |
| One shared native claim | Qualified protocol with exact per-operation authorization | Preserve current binding; qualify competing actors/current ownership before dependent effects |
| Expiry/reclaim and effective execution fence | Unverified | Conditional future capability; exact command/API determined by real CLI probe, never guessed |
| Compatible native task-state merge | Disposable historical observation; fixture policy is not production merge proof | Future production route with frozen origin/head/CAS evidence |
| Conflicting native task-state merge | Unqualified | Detect actual conflict; require explicit resolution basis; never silently choose ours/theirs |
| Native reconciliation | Existing after-effect pilot scope | Read-only recovery, stable IDs, no resend; separately prove actual process-kill boundaries |
| Init/create/dependency setup/close/delete | Disposable setup observations only; generic writes unqualified | Harness setup only in an explicitly selected disposable environment; no general shared-data route promised |
| Arbitrary updates/deletes, user-source Git merges, real database migration, provider calls | Outside this step and not qualified by it | Separate scope/authorization and qualification if later requested |
| R5 package publication and installed replacement | Not performed | Matching pair, extracted tests, exact final-SHA CI and separately verified installation |

No capability flag or native production code is changed by step 1. Future approval is specific to the operation/environment; protocol proof grants no standing authority over another project.

## 3. Reconstructed candidate traps and required proof

These are four provisional R5 candidates derived from opened tests. They do not claim to recover the original comparison.

| Candidate | Existing oracle | Expected result and future native proof |
|---|---|---|
| T1 forced closure without accepted predecessor evidence | PublicCoordination.test_native_close_without_evidence_and_foreign_task_do_not_unlock | Zero downstream calls/approval spend; port to real native state with CM prerequisite proof |
| T2 late prerequisite revocation | CoordinationTests.test_revocation_between_guard_and_dispatch_is_checked_before_approval_spend and test_revocation_after_dispatch_blocks_acceptance_and_changed_fence_blocks_dispatch | Before effect: zero calls/spend. After effect: no acceptance; history retained |
| T3 history mutation/truncation and projection laundering | HistoryTests.test_ordinary_event_update_delete_and_unsealed_insert_are_refused and test_checkpoint_is_external_and_detects_erased_history | SQL mutation rejected; external checkpoint detects erased tail; no checkpoint means anchored completeness UNVERIFIED |
| T4 old acceptance reused after task-state merge | PublicCoordination.test_checkpoint_and_merge_public_routing_do_not_import_completion | Old basis cannot execute/accept; fresh evidence required; repeat with real native branch heads |

Fixture tests establish policy expectations, not native qualification. Exact criteria, planned targets, consumers, test types and future statuses are in r5-acceptance-matrix.md and the canonical JSON records. The comparison must bind an adopted exact four-case source, equal baseline/candidate inputs and case-by-case denominators; unsupported outcomes never become zeros or passes.

## 4. Architecture and decision

Preserve Fable as authority, Memory Integrity as front door, explicit matching Claude Mon as the protected history/CAS engine and Beads as the selected native operational store. Semantica stays optional and off by default. Extend existing native/coordination/branch contracts; do not add another scheduler, permission ledger, SQLite merger or competing project plan.

Minimal option: keep R4 and rerun the current pilot. This retains rollback but does not satisfy ownership/expiry/conflicting-merge requirements. Selected simplest complete option: extend the existing adapter and real qualification harness, reuse CM guard/journal and port recovered oracles. Stronger alternative: a separate coordination service; revisit only if the pinned runtime cannot provide the required fence/branch behavior, because it adds deployment, new authority and recovery surfaces.

Weakest assumption: pinned Beads can provide a reproducible divergent-branch conflict and effective stale-owner refusal at the actual effect boundary. Cheapest disproof: disposable two-actor expiry/reclaim race plus a real conflicting-merge construction before implementing the wider route. Pivot: if either guarantee cannot be demonstrated, retain the capability as blocked and reopen the mechanism; a precheck or fixture pass is not an acceptable substitute.

Evidence families: repository specs/tests explain intended policy; recorded hosted native runs demonstrate only their actual selected protocol/pilot scope. Fixture and specification agreement is correlated, not a second runtime witness. New native outcomes remain unverified.

## 5. CLI contracts and surface states

Production consumer path: explicit selection/operation authorization -> current observation and CM guard -> intent -> allowed native effect -> independent readback -> outcome or UNKNOWN -> replay/current applicability. Missing source/identity/authorization, revoked prerequisite, expired ownership, stale head, malformed diagnostics, timeout and unsupported relation must produce visible BLOCKED/FAILED/UNKNOWN state; none may imply accepted proof. Current command names are preserved. Future native-merge/reclaim CLI/API shapes remain unspecified until inspected on pinned runtime.

There is no graphical interface change. Accessibility here means concise machine-readable status plus understandable CLI explanations, portable explicit paths and no reliance on colors alone. Uploaded/no-runner use remains manual/unverified and cannot claim computed hashes, native execution or enforced ownership without actual observations.

## 6. Verification, measurements and limits

Step 1: structural Fable/specialist plan and resume checks, a request-to-record review, source hashes, old-record preservation, exact criterion mapping and existing policy oracle rechecks. These do not qualify new runtime behavior. Self-review is labelled as such; no independent reviewer is claimed in this step.

Later runtime proof: two actual actors, real expiry times, real branch heads, per-operation call/effect counts, immutable intent/readback fingerprints, separate before/during/after-effect failures and fresh-process recovery. Capture latency and resource use per case and comparison arm; no p95, cost, capacity, RTO or lease-duration target is invented. Bound time/output/concurrency explicitly in the implemented harness and disclose platform/process-tree limitations.

No atomic SQLite-Dolt transaction is claimed. A SQLite prerequisite transaction does not automatically fence an external native write. Raw native commands outside the wrapper remain outside enforcement. Filesystem-owner replacement of both history and its trusted external checkpoint is outside the integrity guarantee. Baseline/source time, measured native event time and receipt capture time must remain distinct.

## 7. Release and recovery

Later R5 packaging must regenerate the matching pair, verify extracted package behavior, preserve R3/R4/knowledge archives, publish with current-head protection, run Windows/Linux CI on the exact final release commit without skip-ci and verify installed bytes separately. Hosted Windows does not certify the user's own Windows machine. Capability claims are granular and derived from proof, not from release labels or hard-coded true fields.

Rollback retains previous packages and protected histories; uncertain native operations reconcile by readback and are never blindly replayed. Rehearse rollback in disposable data before real promotion. Detailed host/database receipts must be sanitized or retained privately; public summaries identify source/runtime/commit hashes and actual checks without exposing user data.

## 8. Ranked gaps and next milestones

P0 before original M7 completion: GAP-ORIGINAL-FOUR-TRAP. Recover/adopt exact cases. P0 before effective ownership: GAP-NATIVE-OWNERSHIP-FENCE. P0 before native merge: GAP-NATIVE-CONFLICT. P0 before during-command crash claims: GAP-OS-KILL-DURING-CLAIM. Retain UNKNOWN when evidence is ambiguous.

1. Step 1: records constructed and structurally verified; original-source recovery remains partial with explicit blocker.
2. Feasibility: real expiry/reclaim/fence and divergent-conflict probes on pinned disposable runtime. No hard-coded success.
3. Implementation: smallest guarded native route, failure-first tests and actual consumers.
4. M7 qualification: recovered/adopted traps plus all ownership/dependency/merge/recovery boundaries, retained receipts and adverse-case review.
5. R5 pair: manifests/ZIPs/extracted tests and rollback rehearsal.
6. Publication/install: exact final commit CI, remote identity and actual installed pair verification.

Future live provider execution, multi-host services and generic destructive native operations are outside this bounded contract. A later scope change must reopen requirements rather than silently expanding R5.

## 9. Observed step-1 verification

Self-review: canonical criterion/test/task mappings, source identities, existing definition preservation and documentation-only write scope passed. Six selected existing policy tests passed (two public CLI cases, two revocation-boundary cases and two history/checkpoint cases). They remain TEST_ONLY policy proof. The original Fable and specialist plan gate passed. No new native pilot, R5 package build or installed replacement ran. The current completion IDs describe the four new documentation requirements; the baseline state in r5-source-basis.json preserves the earlier 28-requirement Semantica completion on its original evidence basis.
