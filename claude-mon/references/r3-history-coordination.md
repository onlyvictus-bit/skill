# R3 companion contract

CM/m11 is the exact proof/history engine for MI/m11. Semantic digest:
`bf3c6314a1b0e8503230f483ef0be19cbf2ace1d4cab96eb4d7a2599b0270c9f`.
One explicit central ledger and CAS are selected by the MI public workflow.
Keep old independent run ledgers as origin evidence; never merge SQLite files.

`complete_read_v2.coordination` owns frozen task policy, graph validation,
current observed-context envelopes, recursive prerequisite proof and request
basis binding. Runner preparation, strict adapter dispatch, acceptance and
protected low-level transitions share the guard. Dispatch-start eligibility,
single-use approval spend and DISPATCHING commit
atomically in the CM ledger, with filesystem/native/API state outside that
transaction. Legacy dispatch and CM CLI
run/resume refuse coordinated tasks. OFF standalone behavior is separate.
Generic coordinated DISPATCHING transitions refuse; use only
`start_approved_dispatch`. A retained DELIVERY_UNKNOWN blocks coordinated
replacement attempts and eligibility even after a reason-only retry event.
Legacy recovery also preserves DELIVERY_UNKNOWN for a spent-approval
AWAITING_APPROVAL attempt. Reconciliation/new approved basis is explicit;
unknown delivery is never converted into success or an automatic resend.
Coordinated cancellation/retryable-error transitions cannot remove uncertainty
after approval was spent without a saved response; use reconciliation instead.
Coordinated offline tasks require complete manifest coverage and deterministic
TEST_ONLY test-char measurement. A single serialized same-task attempt/claim
prevents duplicate preparations; out-of-band raw database/native changes are
not an atomic cross-store execution guarantee.

`ledger.py` schema 4 protects ordinary event writes/deletes and records full
canonical projection snapshots in one transaction with each mutation. Replay
validates each typed projection delta and all task, attempt, accepted, approval
and coordination metadata columns, not just done flags or the latest snapshot.
Generic events refuse caller-open transactions. Missing policy cannot become
OFF mode by removing its current projection. Legacy migrations remain
LEGACY_UNVERIFIED. Do not run
candidate migration against an installed/shared store without its separate
authorization, backup and M7 qualification.

`verify_history(db, checkpoint=None)` separately reports normal guards,
internal chain, projection replay and anchored completeness. A separately
retained current-head checkpoint is required for the last claim. An older valid
prefix is exposed as anchored_through_seq; the newer tail stays UNVERIFIED.
`make_checkpoint` names
the owner; no mutable run map or local head is an independent trusted anchor.
Filesystem-owner replacement of both database and checkpoint is outside the
guarantee. See the matching MI `references/r3-coordination.md` for public
commands, fixture branch behavior, recovery and manual-mode boundaries.

Native Beads remains UNQUALIFIED_M7 and live provider dispatch remains disabled.
Fixture results do not prove semantic truth, live backend memory or perfect
context retention. Retain failed/uncertain attempts and revocations as history.
