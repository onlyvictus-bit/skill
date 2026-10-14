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
