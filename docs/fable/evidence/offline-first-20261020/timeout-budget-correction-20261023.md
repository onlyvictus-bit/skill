# Knowledge worker default budget correction - source issue closed

AUTH: user explicitly asked to change30seconds to a suitable larger timeout and
close the issue. Existing measured community worker41.906seconds and successful
120second initial/fresh replay are the primary runtime evidence, retained at
extended-worker-timing-20261023/Attempt. No new runtime was required or repeated.

INTENT: default120seconds for knowledge workers across direct WorkerClient,
DistributedClient, knowledge CLI, offline-run/verify knowledge replay, and the
programmatic preflight omitted-timeout fallback. Exactly FIVE default literals
changed in FOUR production files. No deadline loop, maximum120validation,
explicit smaller override, shared distributed deadline, cleanup/termination,
source/access/evidence acceptance or native qualification behavior changed.
Returning early remains immediate:120 is a ceiling, not a required wait.

User instructions now document both timeout CLI flags. No other30second limit
was globally replaced: benefit_benchmark.py's30second limit runs a separate
small regression-test subprocess, not the knowledge worker. Targeted twin
search found no remaining30second knowledge-worker DEFAULT.

## Verification

Private receipts below are relative to .github/run-artifacts/.

| Check | Actual observed result | Receipt directory |
| --- | --- | --- |
| Failure-first default checks | 7tests;6expected failing assertions,0errors; explicit shorter timeout/bounds already passed | timeout-budget-20261023-red-confirmed |
| New timeout regressions | 7/7PASS,0errors/skips | timeout-budget-20261023-green |
| MI full tests_v2 | 700run:641pass,1failure,3errors,54skips,1expected failure | timeout-budget-20261023-mi-regression |
| Companion full tests_v2 | 213run:212pass,1error,0skips | timeout-budget-20261023-cm-regression |
| MI legacy tests | 21run:17pass,4errors,0skips | timeout-budget-20261023-mi-legacy |

Focused log SHA256 0ed8f5aa5da987f18f8c28f5edcebd85295dd242752499f9d6d9c99376c32b25.
Final focused rerun after documentation:7/7PASS,0errors/skips,0.084seconds;
timeout-budget-20261023-final/Receipt.json, log SHA256
31bf6e92075a7cf22a53a69ccfa82334f8a7372ab4755edd4b1b88104883be40.
MI full log SHA256 1c6fccc30cfd5d44fd63b5e93c2e88d5f55436ac93d2a50cd8f32ea09aa2085a.
CM full log SHA256 d9c9ccb42654ee2b81498560ffc312832a25b221eeccd852e88dfbc5ef5994a2.
Legacy log SHA256 dcc2e285fe2d58e295ec3c4385614a8cd39e6a0ec0af681cdc78a237977a935f.

The new test runs the REAL _process deadline/protocol/cleanup loop with only OS
process creation and clock replaced:50seconds logical loading succeeds under
the new default; an explicit30second budget still times out without retry.
Real parser/preflight controls cover retrieval, offline-run, verify and missing
programmatic timeout. Invalid0/negative/121/NaN/infinite/bool budgets still refuse.
These are controller tests, NOT a new installed numerical-runtime observation.

## Broader blockers retained, not hidden or repaired here

- MI failure: test_native_containment.ContainmentTests.test_grandchild_pipe_holder_killed;
  capture_complete=false, capture_errors=['tree-sweep: taskkill exit1'].
  The containment code was not changed; no claim that its observed failure is
  repaired or proven pre-existing. It remains relevant to release qualification.
- MI errors: test_native_paths.PathIdentityTests.test_info_accepts_short_database_path
  and test_short_and_long_forms_unify: OSError('no short form') from this host.
- MI and CM error: test_preservation.Preservation.test_release_exact_content_and_declared_changes;
  missing tests_v2/OFFLINE1-CONTENT.json. Packaging/manifests are not regenerated
  by a timeout default correction. Entire companion tree remains unchanged.
- MI legacy errors, all test_memory_watchdog.WatchdogTests: test_bridge_seed_and_verify_proves_persisted_canary_and_cleans_it,
  test_recall_audit_reads_compact_result_titles, test_roundtrip_uses_current_api_and_cleans_canary,
  test_status_uses_current_agentmemory_api_and_does_not_claim_healthy. Their local
  HTTP setup socket.bind is blocked by retained runner OFFLINE_RELEASE_NO_NETWORK.
-54existing conditional runtime/model/POSIX checks skipped without their selected
  environments; no runtime/model install or skip removal performed. Expected
  failure: test_practical_v2_schema.CorrespondenceTests.test_dolt_ignore_configuration_proven_on_live_db.
- Fresh same-seat independent final code review could not complete: workspace
  credits exhausted. This is UNAVAILABLE, not passed. Parent inspected the real
  five-literal diff, deadline/bounds tests and callers. Full CI is NOT green.

## Scope and next position

The inadequate default30second cold-start BUDGET defect is resolved in the
development source and focused-tested. User-approved budget contract is now120,
not a claim of passing the old strict30second contract. No permanent WinError32
fix, all-task performance guarantee, Gate1 completion or release/installation
readiness is asserted. Current selected3.12 byte-for-byte rerun is unobserved;
prior120second real observation plus the new default wiring are distinct proof.

Old diagnostic helper/source/Prepared/raw timing files remain unchanged. Their
live-source seals intentionally describe the pre-correction bytes: never rerun
or rebind the consumed handoff after this source edit. Existing historical
manifests/ZIPs/installed copies remain untouched. No pre-existing data deletion,
ACL/trust/global configuration, install/download, native/model call, commit or
push. This is a local source correction; installed skill update is still separate.
