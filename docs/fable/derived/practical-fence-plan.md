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
